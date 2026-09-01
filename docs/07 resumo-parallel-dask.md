# Resumo: Parallel Processing with Zarr (Cloud-Native Geoscience Course)

Fonte: [07-parallel.html](https://noc-oi.github.io/cloud-native-geoscience-course/07-parallel.html) — Capítulo 7 do curso *Cloud-Native Geoscience Data Workflows*.

## Objetivo do capítulo

Explicar por que o processamento paralelo é importante para grandes datasets Zarr, como usar a biblioteca **Dask** junto com `xarray` para paralelizar computações, e como o chunking e o carregamento "lazy" (preguiçoso) se conectam ao paralelismo. Também apresenta brevemente outras ferramentas de paralelismo em Python.

## 1. Por que processamento paralelo?

Datasets ambientais grandes podem ser lentos ou grandes demais para processar em um único núcleo/processo. Isso é especialmente relevante no Zarr, pois o formato é projetado para ser lido/escrito **chunk por chunk**, o que se encaixa naturalmente em trabalho paralelo.

Processar em um único núcleo pode ser:
- **Lento**: tempos de execução longos mesmo para operações simples;
- **Limitado por memória**: dados ou resultados intermediários podem não caber na RAM;
- **Limitado por I/O**: leitura/escrita domina o tempo de computação, principalmente via rede ou disco.

O paralelismo ajuda quando o workflow precisa:
- Ler muitos chunks de um Zarr store;
- Calcular estatísticas sobre grandes regiões espaciais/temporais;
- Rodar a mesma operação em muitos arquivos, variáveis ou membros de ensemble independentes.

**Chave**: paralelismo funciona melhor quando a camada de computação e o layout dos dados estão alinhados — o armazenamento em chunks (Zarr) permite que múltiplos workers leiam chunks diferentes de forma independente, enquanto o Dask agenda o trabalho entre eles.

## 2. Dask: processamento distribuído para Python

O **Dask** é uma biblioteca de processamento distribuído que paraleliza código Python em múltiplos núcleos (mesma máquina) ou múltiplos computadores (cluster). Pode ser usado "por trás" do `xarray` com poucas modificações no código.

Conceitos-chave do Dask:
- **Task graph (grafo de tarefas)**: o Dask constrói um grafo de tarefas e dependências ao escrever o código, mas não executa imediatamente;
- **Lazy evaluation (avaliação preguiçosa)**: as computações só são executadas quando se chama `.compute()`;
- **Cluster**: conjunto de workers gerenciados por um scheduler — pode ser local (uma máquina) ou remoto (HPC, Kubernetes etc.).

### Criando um cluster local

```python
from dask.distributed import Client, progress

client = Client(processes=False, threads_per_worker=4,
                n_workers=1, memory_limit="2GB")
client  # Mostra informações do cluster
```

### Dashboard do Dask

O objeto `client` fornece um link para um **Dashboard** onde é possível monitorar o cluster: quão ocupado ele está, grafo de dependências de tarefas, uso de memória e status dos workers. Acesso local geralmente via `http://localhost:8787/status`.

No JASMIN (cluster HPC citado no curso), é necessário instalar a extensão `jupyter-server-proxy` e gerar uma URL de proxy para acessar o dashboard remotamente.

### Uso do Dask Gateway no JASMIN

O JASMIN oferece um serviço de **Dask Gateway** para submeter jobs Dask a uma fila especial no cluster HPC:

```python
import dask_gateway
gw = dask_gateway.Gateway("https://dask-gateway.jasmin.ac.uk", auth="jupyterhub")

options = gw.cluster_options()
options.worker_cores = 1
options.scheduler_cores = 1
options.account = "workshop"
options.worker_setup = '...'  # ambiente Conda/Mamba

clusters = gw.list_clusters()
if not clusters:
    cluster = gw.new_cluster(options, shutdown_on_close=False)
else:
    cluster = gw.connect(clusters[0].name)

client = cluster.get_client()
cluster.adapt(minimum=1, maximum=15)  # escala workers automaticamente
```

Ao final, é importante encerrar o cluster com `cluster.shutdown()` para liberar recursos.

## 3. Arrays Dask e computação preguiçosa (lazy)

Arrays Dask (`dask.array`) imitam a API do NumPy, mas executam de forma preguiçosa e paralela, dividindo os dados em chunks. Os dados também podem ser carregados "lazy" — só são lidos do disco quando acessados, dando a ilusão de trabalhar com um dataset maior que a memória disponível.

```python
import dask.array as da

x = da.random.random((10000, 10000), chunks=(1000, 1000))
y = da.ones((10000, 10000), chunks=(1000, 1000))
z = x + y          # ainda não computado, apenas grafo de tarefas
result = z.mean().compute()  # dispara a computação de fato
```

**Pontos importantes:**
- Criar `x` e `y` define arrays com chunking especificado, mas nada é computado até ser necessário;
- Operações constroem um grafo de tarefas; `.compute()` executa as tarefas;
- O chunking permite que o Dask processe blocos diferentes em paralelo e carregue apenas os chunks necessários na memória.

### Cuidado com o lazy loading + paralelismo

Combinar carregamento preguiçoso com processamento paralelo pode ser complicado: é difícil saber exatamente quando os dados são lidos do disco ou baixados de uma fonte remota, o que pode causar uso inesperado de memória. Ao abrir um Zarr com `xarray`, os dados **não** são lidos para a memória — apenas quando são efetivamente acessados (fatiados ou usados em um cálculo).

## 4. Dask + Zarr via xarray

O padrão mais comum do curso é abrir um Zarr store com `xarray` e deixar que ele use chunks apoiados em Dask, mantendo os dados "lazy" até que algo seja computado.

```python
import xarray as xr
from dask.distributed import Client

client = Client(n_workers=2, threads_per_worker=2, memory_limit="1GB")

ds = xr.open_zarr(f"{base_path}data/era5_sst/ocean_temperature.zarr", chunks={})
sst = ds["sst"]
```

Como o dataset já está chunked no Zarr, basta usar `chunks={}` (ou nem especificar) para que o xarray reaproveite o chunking já existente no store. Para datasets **netCDF**, é necessário especificar manualmente os tamanhos de chunk ao abrir:

```python
ds_nc = xr.open_dataset(
    f"{base_path}data/era5_sst/ocean_temperature.nc",
    chunks={"valid_time": 10, "latitude": 100, "longitude": 100}
)
```

### Exemplo de computação paralela simples

```python
corrected = sst * 1.1 - 1.0
global_mean = corrected.mean(dim=("latitude", "longitude"))
result = global_mean.compute()
```

Os dados permanecem "lazy" (preguiçosos) até `.compute()` ser chamado — nesse momento o Dask distribui o trabalho entre os chunks.

## 5. Outras formas de paralelizar workflows com Zarr

O Dask é a ferramenta principal do curso, mas existem alternativas — a melhor escolha depende se a tarefa é limitada por CPU, por I/O, ou já está "chunked":

| Ferramenta | Quando usar |
|---|---|
| **Threads** | Útil quando o trabalho passa tempo esperando I/O (ex.: leitura de chunks de um Zarr store). Menos flexível que o Dask para organizar um workflow de análise completo. |
| **Multiprocessing** (nativo do Python) | Bom para tarefas independentes que não compartilham muito estado ("embaraçosamente paralelas"). Não entende chunks, grafos de tarefas ou arrays rotulados automaticamente. |
| **Cubed** | Biblioteca para processamento de arrays fora da memória (*out-of-core*), voltada a grandes computações em ambientes orientados à nuvem. |

## 6. Visualizando o grafo de tarefas (Task Graph)

É possível visualizar como o Dask está organizando/agendando o trabalho, o que ajuda a entender quantas tarefas são criadas e como elas dependem umas das outras.

```python
import dask
import xarray as xr

ds = xr.open_zarr(f"{base_path}data/era5_sst/ocean_temperature.zarr")
sst = ds["sst"]
corrected = sst * 1.1 - 1.0
global_mean = corrected.mean(dim=("latitude", "longitude"))
dask.visualize(global_mean, filename='task_graph.png')
```

Isso gera um arquivo PNG com o grafo de tarefas (requer a biblioteca `graphviz`; às vezes é necessário ajustar a variável de ambiente `PATH` para que o Dask encontre o executável do graphviz). Também é possível usar `global_mean.visualize()` diretamente em um notebook Jupyter.

## Exercícios abordados no capítulo (resumo)

1. **Comparar Dask vs NumPy**: medir o tempo de cálculo da média de um array grande com e sem Dask, observando uso de CPU.
2. **Dask + xarray juntos**: comparar a performance ao computar médias espaciais em datasets Zarr (chunked) vs. netCDF, mostrando o ganho de desempenho do Zarr+Dask.
3. **Workflow paralelo pequeno**: comparar o dataset original e o "rechunked" (do capítulo anterior) ao rodar estatísticas espaciais e temporais, observando qual chunking resulta em execução mais eficiente.
4. **(Opcional) Workflow em cluster HPC (JASMIN)**: usar o Dask Gateway para processar o dataset GLORYS (maior), aplicando uma correção na variável de velocidade `uo`, e experimentar variando número de cores/workers.

## Pontos-chave (Key Points)

- Dask é a principal ferramenta de paralelismo usada no curso.
- Zarr e Dask combinam bem porque o Zarr armazena dados em chunks independentes.
- O xarray pode abrir dados Zarr de forma "lazy" e repassar o trabalho chunked para o Dask.
- Existem outras ferramentas de paralelismo em Python, mas o Dask é a opção mais natural para dados ambientais organizados em chunks.

---
*Este resumo cobre o Capítulo 7 do curso [Cloud-Native Geoscience Data Workflows](https://noc-oi.github.io/cloud-native-geoscience-course/), que inclui exercícios práticos de comparação de performance com os datasets ERA5 e GLORYS (não reproduzidos integralmente aqui).*
