# Resumo: Convertendo Formatos Tradicionais para Zarr (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/10-conversion-workflow.html](https://noc-oi.github.io/cloud-native-geoscience-course/10-conversion-workflow.html)
Capítulo 10 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Explicar por que e como converter dados NetCDF para Zarr, como escolher tamanhos de chunk ao partir de arquivos NetCDF, como usar Dask e xarray para converter e escrever dados em Zarr de forma eficiente, e como verificar se os dados convertidos são utilizáveis e corretos (ex.: comparando médias).

## Por que converter NetCDF para Zarr?

O NetCDF é amplamente usado em dados oceânicos, climáticos e meteorológicos, e funciona bem em sistemas de arquivos locais e armazenamento HPC. Porém, à medida que os datasets crescem e migramos para computação em nuvem e paralela, o Zarr oferece várias vantagens:

- Armazenamento em chunks alinhado com object stores e acesso via HTTP/S3.
- Leitura/escrita paralela fácil de chunks por Dask ou outros frameworks.
- Layout flexível para grandes coleções (muitos arquivos NetCDF → um único dataset Zarr).

Converter NetCDF para Zarr não muda o conteúdo científico, mas muda como os dados são organizados e acessados, viabilizando fluxos de trabalho cloud-native e análises mais eficientes em escala.

### Conversão básica com xarray

Fluxo simples usando o `to_zarr` do xarray:

```python
import xarray as xr

ds_nc = xr.open_dataset(f"{base_path}data/era5_sst/ocean_temperature.nc")

# Decidir o chunking
ds_nc = ds_nc.chunk({"valid_time": 10, "latitude": 100, "longitude": 100})

# Escrever o repositório Zarr
ds_nc.to_zarr("data/example.zarr", mode="w")

# Reabrir para verificar
ds_zarr = xr.open_zarr("data/example.zarr")
```

Depois disso, você tem um repositório Zarr local que pode ser enviado ao object storage e acessado em paralelo por múltiplos clientes.

## Fluxo geral: NetCDF → Zarr → object store

Na prática, a conversão de NetCDF para Zarr costuma seguir estas etapas:

1. **Entender a entrada NetCDF**: verificar variáveis, dimensões, coordenadas e chunking existentes.
2. **Decidir a estratégia de chunking para o Zarr**: com base nos padrões de acesso esperados e nos tamanhos aproximados de chunk em MB.
3. **Abrir o NetCDF com xarray**: usando `open_dataset` ou `open_mfdataset` para múltiplos arquivos.
4. **Aplicar chunking e encoding**: usar `.chunk()` e definir opções de compressão/codificação.
5. **(Opcional) Escrever o Zarr em armazenamento local**: usando `Dataset.to_zarr()`, possivelmente com Dask para escritas paralelas.
6. **Enviar o repositório Zarr para object storage**: usando ferramentas de CLI de nuvem, bibliotecas de sistema de arquivos, ou escrevendo diretamente no object storage com `fsspec`.
7. **Verificar reabrindo a partir do object storage e executando análises** (ex.: calculando médias).

O exemplo prático da lição usa um subconjunto do dataset de reanálise **GLORYS**, fornecido como múltiplos arquivos NetCDF (um por dia), com o objetivo de convertê-los em um único repositório Zarr acessível eficientemente em paralelo.

## Etapa 1 — Inspecionar as entradas NetCDF

Antes de converter, é preciso inspecionar o(s) arquivo(s) NetCDF:

```python
import xarray as xr

ds_nc = xr.open_dataset(f"{base_path}data/glorys/glorys_20260501.nc")
print(ds_nc.dims)
print(ds_nc.data_vars)
print(ds_nc.coords)
print(ds_nc.encoding)  # pode mostrar informações de chunking e compressão
```

Perguntas a responder:

- Há múltiplos arquivos (ex.: um por fatia de tempo) ou apenas um único arquivo?
- Quais dimensões estão presentes (`time`, `lat`, `lon`, `depth`, `member`)?
- As variáveis já estão fragmentadas (chunked), e como?
- Os arquivos são consistentes em termos de variáveis e coordenadas, caso se use `open_mfdataset`?

Para múltiplos arquivos NetCDF, `open_mfdataset` os abre todos de uma vez:

```python
ds_nc_multi = xr.open_mfdataset(
    f"{base_path}data/glorys/*.nc",
    combine="by_coords",
)
```

Importante: o `open_mfdataset` combina múltiplos arquivos em um único dataset xarray, mas exige que as variáveis e coordenadas sejam consistentes entre os arquivos. Os dados não são carregados na memória nesse momento — o xarray os carrega de forma preguiçosa (lazy) conforme necessário.

## Etapa 2 — Decidir a estratégia de chunking para o Zarr

Os chunks no Zarr têm grande impacto no desempenho. Uma regra prática comum é mirar tamanhos de chunk comprimidos na faixa de 10–100 MB, mas a escolha exata depende das cargas de trabalho e do hardware.

Considerar:

- **Dimensões**: quais correspondem a tempo, espaço, profundidade, membro de ensemble?
- **Cargas de trabalho**: série temporal em pontos, médias espaciais, subconjuntos regionais, estatísticas de ensemble.
- **Armazenamento**: disco HPC local vs. object store, largura de banda de rede, framework paralelo (Dask).

Exemplo de estratégias de chunk para um dataset com dimensões `(time, latitude, longitude, depth)`:

- Se séries temporais são comuns: `{"time": 360, "latitude": 100, "longitude": 100, "depth": 1}`.
- Se mapas espaciais por instante de tempo são comuns: `{"time": 1, "latitude": 361, "longitude": 720, "depth": 1}`.
- Se fatias de profundidade são comuns: `{"time": 1, "latitude": 100, "longitude": 100, "depth": 10}`.

É possível experimentar diferentes formatos de chunk e usar o dashboard do Dask e medições de desempenho para refinar as escolhas.

## Etapa 3 — Converter NetCDF para Zarr com xarray e Dask

Depois de decidir o chunking, o `to_zarr` do xarray escreve o dataset — de forma serial ou paralela com Dask. Para datasets grandes, a escrita paralela costuma ser necessária para evitar tempos de execução muito longos.

```python
from dask.distributed import Client
import xarray as xr

client = Client(n_workers=6, threads_per_worker=2)

ds_nc = xr.open_mfdataset(f"{base_path}data/glorys/*.nc", combine="by_coords")
ds_chunked = ds_nc.chunk({"time": 5, "latitude": 400, "longitude": 400, "depth": 10})

ds_chunked.to_zarr("data/glorys.zarr", mode="w", consolidated=True)

ds_zarr = xr.open_zarr("data/glorys.zarr", consolidated=True)
```

### Metadados consolidados

Ao escrever um repositório Zarr, é possível consolidar os metadados: o repositório passa a ter um único arquivo-índice de metadados, reunindo os metadados de todos os arrays e atributos em um só lugar. Isso torna a abertura do dataset mais rápida, especialmente quando o repositório tem muitas variáveis ou muitos chunks — em vez de ler muitos arquivos de metadados pequenos um a um, o xarray pode ler os metadados consolidados em uma única etapa.

> **Boa prática**: usar metadados consolidados quando o dataset será lido muitas vezes após a escrita, especialmente em fluxos de trabalho de nuvem/object storage — geralmente um bom padrão para repositórios Zarr prontos para análise.

### Encoding e compressão

Ao escrever repositórios Zarr, é possível escolher como cada variável é codificada e comprimida. O objetivo geralmente não é maximizar a compressão a todo custo, mas equilibrar tamanho de arquivo, velocidade e facilidade de leitura:

```python
import zarr
from zarr.codecs import BloscCodec, BloscShuffle
import xarray as xr

ds = xr.open_dataset(f"{base_path}data/era5_sst/ocean_temperature.nc")
compressor = BloscCodec(cname="zstd", clevel=3, shuffle=BloscShuffle.shuffle)
encoding = {
    "sst": {
        "compressors": compressor,
        "chunks": (10, 100, 100),
    }
}

ds.to_zarr(
    "data/example_compressed.zarr",
    mode="w",
    encoding=encoding,
    consolidated=True,
)
```

Nesse exemplo: `zstd` oferece boa compressão com velocidade razoável; `clevel=3` é um nível de compressão moderado, geralmente um bom compromisso entre velocidade e tamanho; `shuffle=2` costuma melhorar a compressão para muitos datasets numéricos; o mesmo compressor é aplicado a cada variável de dados via o dicionário `encoding`.

Para dados científicos, compressão moderada costuma ser um bom padrão: reduz o tamanho de armazenamento, diminui custos de transferência de rede e mantém velocidades de leitura/escrita razoáveis. Compressão muito agressiva pode economizar mais espaço, mas pode deixar a escrita e a leitura mais lentas — trade-off que, em fluxos de trabalho grandes, muitas vezes não vale a pena.

## Etapa 4 — Enviar o Zarr para o object storage

Depois de escrever o Zarr localmente com sucesso, é possível enviar o diretório do repositório para um object store (AWS S3, GCS, MinIO, etc.). A lição demonstra o uso do [s3cmd](https://s3tools.org/s3cmd) (apenas para fins de demonstração — não instalado no ambiente do curso), mas outras ferramentas como `awscli`, `rclone`, `boto3` ou `fsspec` também servem:

```bash
# Criar um bucket (se não existir)
s3cmd mb s3://my-bucket

# Enviar o repositório Zarr recursivamente
s3cmd put -r data/glorys.zarr s3://my-bucket/glorys.zarr
```

### Escrita direta no object storage com fsspec

Em vez de gerar o dataset Zarr localmente e enviá-lo depois, a lição recomenda escrever o dataset Zarr diretamente no object store usando `fsspec` — uma abordagem mais eficiente que evita uso desnecessário de armazenamento local.

Como o dataset é grande, a lição usa o cluster Dask do JASMIN (que tem melhor acesso de rede ao object store) para executar a conversão e o envio:

```python
import dask_gateway

gw = dask_gateway.Gateway("https://dask-gateway.jasmin.ac.uk", auth="jupyterhub")

options = gw.cluster_options()
options.worker_cores = 4
options.scheduler_cores = 2
options.account = "workshop"
options.worker_setup = "..."  # ativação do ambiente conda específico

clusters = gw.list_clusters()
cluster = gw.new_cluster(options, shutdown_on_close=False) if not clusters else gw.connect(clusters[0].name)
client = cluster.get_client()
cluster.adapt(minimum=1, maximum=4)
```

Criar um "mapper" para o object store e escrever diretamente nele:

```python
import xarray as xr
import fsspec
import os

store_url = "s3://my-bucket/glorys.zarr"

os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"

storage_options = {
    "key": os.environ["AWS_ACCESS_KEY_ID"],
    "secret": os.environ["AWS_SECRET_ACCESS_KEY"],
    "client_kwargs": {"endpoint_url": "https://atlantis-vis-o.s3-ext.jc.rl.ac.uk"},
    "config_kwargs": {
        "request_checksum_calculation": "when_required",
        "response_checksum_validation": "when_required",
    },
}

mapper = fsspec.get_mapper(store_url, **storage_options)

ds_chunked.to_zarr(mapper, mode="w", consolidated=True)
```

## Etapa 5 — Verificar com uma análise simples

Para confirmar que o dataset Zarr convertido é utilizável, executa-se uma análise simples, como calcular uma média:

```python
ds_zarr = xr.open_zarr(mapper, consolidated=True)
# ou diretamente via URL pública:
ds_zarr = xr.open_zarr("https://atlantis-vis-o.s3-ext.jc.rl.ac.uk/my-bucket/glorys.zarr", consolidated=True)

var = ds_zarr["zos"]

# Média para cada instante de tempo (média espacial global)
mean_per_time = var.mean(dim=("latitude", "longitude")).compute()

# Média para cada ponto lat/lon (média no tempo)
mean_per_latlon = var.mean(dim="time").compute()
```

## Exercícios propostos na lição (resumo do raciocínio)

Os exercícios 2 a 5 usam um subconjunto do dataset de reanálise **ERA5**, variável `swh` (altura significativa de onda), fornecido como múltiplos arquivos NetCDF diários (`data/daily_swh/`):

- **Entender o dataset NetCDF**: abrir um único arquivo e depois vários com `open_mfdataset`, verificando dimensões, variáveis, coordenadas, encoding e consistência entre arquivos, e o comprimento combinado da dimensão de tempo.
- **Propor tamanhos de chunk para o Zarr**: propor um dicionário de chunking (ex.: `{"time": 720, "lat": 100, "lon": 100}`), estimar o tamanho aproximado de cada chunk em bytes/MB (a partir do tipo de dado e dos comprimentos das dimensões) e justificar como as escolhas apoiam as análises pretendidas.
- **Converter o dataset NetCDF para Zarr no object storage**: criar um cluster Dask (local ou via JASMIN), converter o dataset diretamente para o object store com `fsspec`, e reabrir para verificar se a estrutura, variáveis e atributos foram preservados. Perguntas de reflexão incluem quanto tempo a conversão/envio levou, se o tamanho do repositório Zarr parece razoável em comparação aos arquivos NetCDF originais, e se alguma variável ou atributo precisou ser descartado/ajustado.
- **Verificar consistência e calcular uma média**: comparar o mesmo cálculo estatístico (ex.: média global em um instante) entre o dataset NetCDF original e o dataset Zarr convertido, tanto em termos de resultado (devem coincidir dentro da tolerância de ponto flutuante) quanto de tempo de abertura e cálculo.

## Pontos-chave (resumo final da lição)

1. Converter NetCDF para Zarr viabiliza acesso cloud-native, fragmentado (chunked) e amigável ao paralelismo para grandes datasets científicos.
2. Uma conversão eficaz exige entender os dados de entrada, escolher tamanhos de chunk com base nas cargas de trabalho, e usar o `to_zarr` do xarray com encoding e compressão adequados.
3. O Dask pode paralelizar o processo de conversão, tornando viável lidar com grandes coleções de arquivos NetCDF.
4. Enviar repositórios Zarr para object storage permite que equipes distribuídas e ferramentas diversas acessem os mesmos datasets eficientemente.
5. Verificar estatísticas básicas (ex.: valores médios) nas versões NetCDF e Zarr ajuda a confirmar que a conversão preserva o conteúdo científico.

---
*Este é o Capítulo 10 de um curso de 16 capítulos. O próximo capítulo apresenta Estudos de Caso.*
