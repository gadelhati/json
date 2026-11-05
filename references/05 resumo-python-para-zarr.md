# Resumo: Python para Zarr (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/05-python-zarr.html](https://noc-oi.github.io/cloud-native-geoscience-course/05-python-zarr.html)
Capítulo 5 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Apresentar os principais pacotes Python usados para trabalhar com dados Zarr, mostrar como inspecionar um repositório Zarr diretamente com a biblioteca `zarr`, como o xarray representa datasets Zarr como dados N-dimensionais rotulados, quando os dados são de fato carregados na memória, e algumas operações básicas de xarray úteis em oceanografia, clima e meteorologia.

## Ecossistema Python para Zarr

O Zarr conta com um ecossistema rico de ferramentas Python:

- **[zarr](https://zarr.readthedocs.io/en/stable/)** — implementação Python central do modelo de arrays N-dimensionais fragmentados e grupos do Zarr.
- **[xarray](https://xarray.dev/en/stable/)** — biblioteca de arrays N-dimensionais rotulados que abre datasets Zarr e os apresenta como objetos `Dataset`, com dimensões e coordenadas nomeadas.
- **[fsspec](https://filesystem-spec.readthedocs.io/en/latest/) / [s3fs](https://s3fs.readthedocs.io/en/latest/) / [gcsfs](https://gcsfs.readthedocs.io/en/latest/) / [obstore](https://developmentseed.org/obstore/latest/)** — adaptadores de sistema de arquivos para acessar repositórios Zarr em disco local, S3, Google Cloud Storage e outros backends.
- **Ferramentas de apoio** — VirtualiZarr, Icechunk e outras, construídas sobre Zarr e xarray para fluxos especializados (rechunking, armazenamento transacional, arquivos prontos para nuvem).

A lição foca no essencial: usar o `zarr` diretamente para inspeção de baixo nível, e usar o xarray para a maior parte da análise do dia a dia com dados ambientais em formato Zarr.

## Abrindo com a biblioteca `zarr`

Como visto no capítulo anterior, repositórios Zarr são organizados em grupos e arrays. A biblioteca `zarr` oferece acesso de baixo nível a esses repositórios, permitindo abrir grupos e arrays, inspecionar seus formatos (`shape`), formatos de chunk, tipos de dado, ler e escrever dados, e visualizar ou editar atributos (metadados).

No exemplo da lição, o repositório `data/era5_sst/ocean_temperature.zarr` contém um único grupo com um array representando dados de temperatura da superfície do mar do reanálise ERA5, fragmentado em tempo e espaço, com atributos como unidades e nomes longos.

Fluxo básico com a biblioteca `zarr`:

```python
import zarr

root = zarr.open_group("data/era5_sst/ocean_temperature.zarr", mode="r")
print(root)
print(list(root.arrays()))
print(list(root.groups()))
print("Group attributes:", root.attrs)

temp = root["sst"]
print("Shape:", temp.shape)
print("Chunks:", temp.chunks)
print("Data type:", temp.dtype)
print("Array attributes:", temp.attrs)
```

Um array Zarr informa como os dados estão organizados em disco ou no object storage: `shape` mostra o tamanho total do array, `chunks` mostra como ele é dividido, e `attrs` guarda metadados úteis como unidades ou nomes de variáveis.

### Carregamento preguiçoso (lazy loading) e memória

Abrir um repositório Zarr normalmente lê primeiro os metadados, não os valores completos dos dados — o chamado **lazy loading**: a estrutura do dataset fica disponível imediatamente, mas os dados dos chunks só são lidos quando solicitados.

Com a biblioteca `zarr`, propriedades como `shape`, `chunks`, `dtype` e `.attrs` vêm dos metadados. Os dados reais só são lidos quando o array é indexado ou fatiado (ex.: `temp[0, :, :]`) — nesse momento, apenas os chunks necessários para essa seleção são lidos, sem carregar o array inteiro. A mesma lógica se aplica ao xarray: abrir o dataset é uma operação barata, e os dados só são carregados quando você seleciona, calcula, plota ou pede valores.

## Abrindo com xarray

Enquanto o `zarr` é ideal para inspeção e manipulação de baixo nível, o xarray costuma ser a principal ferramenta para analisar dados ambientais multidimensionais. Ele oferece:

- **Datasets** — coleções de variáveis de dados (arrays) com dimensões e coordenadas compartilhadas.
- **Dimensões rotuladas** — nomes como `time`, `lat`, `lon`, `depth`, em vez de índices numéricos.
- **Coordenadas** — arrays explícitos para latitude, longitude, tempo, etc.
- **Operações de alto nível** — seleção (`.sel`), redução (`.mean`, `.sum`), reamostragem, plotagem, etc.

O xarray consegue abrir dados NetCDF, GRIB (via backends) e Zarr, o que torna os datasets Zarr acessíveis em um formato familiar e pronto para análise, e facilita atualizar fluxos de trabalho para usar repositórios Zarr cloud-native sem mudar o código de análise.

Para Zarr, usa-se `xr.open_zarr`, que entende os metadados e convenções do Zarr:

```python
import xarray as xr

ds = xr.open_zarr("data/era5_sst/ocean_temperature.zarr")
ds  # visão geral de variáveis e coordenadas

print("Dimensions: ", ds.dims)
print("Data variables: ", ds.data_vars)
print("Coordinates: ", ds.coords)
```

Pontos importantes:

- `ds` é um `Dataset` do xarray.
- `ds.data_vars` lista as variáveis de dados (ex.: `sst`, `salinity`).
- `ds.coords` normalmente inclui `time`, `lat`, `lon` e outras variáveis de coordenada.
- Os metadados dos arrays e atributos Zarr são mapeados para a estrutura do xarray, permitindo o uso das convenções CF e outros padrões.

O resultado é um `Dataset` do xarray, em que cada variável é um `DataArray`, carregando os metadados originais do repositório Zarr.

### NetCDF vs. Zarr com xarray

Ao abrir o mesmo dataset em formato NetCDF (`xr.open_dataset`), a estrutura resultante é muito parecida com a versão Zarr. A principal diferença é que o NetCDF é um único arquivo, enquanto o Zarr é um diretório de arrays fragmentados — mas o xarray oferece uma interface consistente para os dois formatos, permitindo reaproveitar o código de análise.

## Operações básicas do xarray

Em oceanografia, clima e meteorologia, é comum querer selecionar dados por coordenadas, calcular médias sobre dimensões e plotar resultados. O xarray oferece uma interface simples para isso:

- Selecionar dados com `.sel()` usando valores de coordenada.
- Usar `.isel()` para selecionar por posições numéricas.
- Calcular uma média sobre uma ou mais dimensões (ex.: `.mean(dim=("latitude", "longitude"))`) — lembrando que, no ERA5, a longitude costuma ir de 0 a 360.
- Plotar rapidamente um recorte com `.plot()`.

```python
time_slice = ds["sst"].sel(valid_time=slice("2025-01-01T00:00:00", "2025-01-02T00:00:00"))
global_mean = ds["sst"].mean(dim=("latitude", "longitude"))
point_ts = ds["sst"].sel(latitude=0.0, longitude=0.0, method="nearest")
isel_slice = ds["sst"].isel(valid_time=0, latitude=200, longitude=200)
```

Nessas operações, os dados não são carregados na memória até que valores sejam solicitados ou os resultados sejam plotados (ex.: `time_slice.sel(...).plot()`, `point_ts.plot()`, ou `print(isel_slice.values)`). Isso mantém o código legível e permite trabalhar com coordenadas nomeadas em vez de posições brutas de array.

### O que entra na memória?

Uma regra prática:

- **Abrir** um repositório Zarr carrega apenas metadados.
- **Inspecionar** `shape`, `chunks`, `dims` e atributos usa majoritariamente metadados.
- **Selecionar**, **calcular**, **plotar** ou chamar `.values` lê os chunks de dados para a memória.

Por exemplo, isto inspeciona principalmente metadados:
```python
print(ds["sst"])
print(ds["sst"].dims)
print(ds["sst"].attrs)
```

Mas isto solicita valores reais dos dados:
```python
ds["sst"].isel(valid_time=0).values
```

Essa distinção é uma das principais razões pelas quais o Zarr funciona bem para grandes datasets ambientais: é possível explorar a estrutura do dataset primeiro, e carregar apenas as partes necessárias para a análise.

## Exercícios propostos na lição (resumo do raciocínio)

- **Explorar o repositório**: listar arrays do grupo raiz, escolher uma variável e imprimir seu `shape`, `chunks` e `dtype`, e identificar atributos úteis (unidades, nomes longos, nomes padrão).
- **Abrir com xarray**: abrir o dataset com `xr.open_zarr`, imprimir dimensões, variáveis de dados e coordenadas, e observar que a abertura é rápida mesmo em datasets grandes, pois o xarray lê metadados primeiro.
- **Primeira análise em um dataset Zarr**: calcular uma média espacial (latitude/longitude) da temperatura da superfície do mar para obter uma série temporal, e depois calcular a média para uma pequena região (ex.: uma bacia oceânica), lembrando que no `slice()` de latitude deve-se usar primeiro o valor máximo (já que a latitude decresce de norte a sul) e que a longitude do ERA5 vai de 0 a 360.
- **Ler apenas uma pequena parte**: selecionar temperatura apenas para a primeira hora de 2025 em uma pequena região (ex.: costa sudeste do Brasil) e calcular a média — demonstrando que é possível processar apenas uma pequena porção de um dataset muito grande, sem carregá-lo por inteiro, o que seria bem mais custoso com um arquivo NetCDF equivalente.

## Pontos-chave (resumo final da lição)

1. O pacote Python `zarr` oferece acesso de baixo nível a repositórios Zarr, incluindo grupos, arrays e atributos.
2. O xarray é a principal ferramenta de alto nível para trabalhar com datasets Zarr ambientais como dados N-dimensionais rotulados.
3. Abrir um Zarr com xarray (`xr.open_zarr`) fornece variáveis, dimensões e coordenadas em uma estrutura `Dataset` familiar.
4. Os valores dos dados só são carregados quando são selecionados ou usados em algum cálculo.
5. Operações básicas do xarray — seleção, redução e plotagem — funcionam da mesma forma em dados Zarr e em dados NetCDF.

---
*Este é o Capítulo 5 de um curso de 16 capítulos. O próximo capítulo aborda a Escolha de Chunks em Escala.*
