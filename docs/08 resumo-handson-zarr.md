# Resumo: Reading Real-World Zarr Datasets in Python (Cloud-Native Geoscience Course)

Fonte: [08-handson-zarr.html](https://noc-oi.github.io/cloud-native-geoscience-course/08-handson-zarr.html) — Capítulo 8 do curso *Cloud-Native Geoscience Data Workflows*.

## Objetivo do capítulo

Apresentar, de forma prática, vários datasets Zarr públicos reais de oceanografia, clima e meteorologia, e ensinar a abri-los e explorá-los com Python (`xarray`, `zarr`, `fsspec`) diretamente do armazenamento em nuvem (Google Cloud, AWS S3), sem precisar baixá-los.

⚠️ **Aviso importante do capítulo**: esses datasets podem ter vários terabytes — **NÃO devem ser baixados localmente**. A ideia é acessá-los de forma "lazy" (preguiçosa) e ler apenas as partes necessárias.

## 1. Visão geral dos datasets explorados

O capítulo trabalha com quatro datasets principais, cada um ilustrando um aspecto diferente da estrutura de dados:

| Dataset | O que ilustra |
|---|---|
| **IFS/AIFS ENS (ECMWF, dynamical.org)** | Previsões de ensemble em Icechunk/Zarr, na AWS |
| **ERA5 ARCO** | Reanálise global em Zarr, pronta para análise (Climate Data Store) |
| **Sofar Spotter drifters** | Boias de deriva — dados armazenados como *ragged array* (arrays "esfarrapados", com trajetórias de tamanhos variados) |
| **NEMO Near-Present-Day (NOC)** | Simulações oceânicas multi-decadais em formato Icechunk |

Esses exemplos cobrem: grades regulares lat/lon, arrays "esfarrapados" (ragged), grades irregulares e dimensões de **ensemble** (`member`).

## 2. Previsões de ensemble — ECMWF AIFS ENS (Icechunk/Zarr)

O `dynamical.org` hospeda previsões do ECMWF AIFS (single e ensemble) em Icechunk/Zarr na AWS S3.

```python
import xarray as xr
ds = xr.open_zarr("https://data.dynamical.org/ecmwf/aifs-single/forecast/latest.zarr")
```

O dataset tem ~14 TB, com dimensões `init_time`, `lead_time`, `latitude`, `longitude` e variáveis como temperatura, vento e cobertura de nuvens.

### Fatiando os dados

Para trabalhar com um subconjunto menor (ex.: apenas o último horário de inicialização):

```python
temperature_2m = ds['temperature_2m'].isel(init_time=slice(-1, None))
```

Nada é carregado ainda — os dados continuam como um **array Dask**. Só ao chamar `.compute()` os dados são de fato lidos na memória (exemplo clássico de **lazy loading**):

```python
temperature_2m_local = temperature_2m.compute()
temperature_2m_local.isel(init_time=0, lead_time=0).plot()
```

É possível também selecionar por coordenadas (latitude/longitude) usando `.sel()` em vez de `.isel()`.

### Visualização com Cartopy

O capítulo mostra um exemplo usando `cartopy` para plotar o vento zonal a 10m sobre um mapa com litoral, usando `ccrs.PlateCarree()` como projeção.

## 3. ERA5 ARCO — reanálise global em Zarr

Um subconjunto do ERA5 (dados de superfície e onda) está disponível em formato **ARCO** (Analysis-Ready, Cloud-Optimized) no Copernicus Climate Data Store (CDS).

### Passos para acesso
1. Criar conta no [CDS](https://cds.climate.copernicus.eu/);
2. Obter uma **API key** na página de perfil;
3. Usar a chave para autenticar as requisições.

O dataset de ondas está disponível em **dois layouts de chunking**:
- **geo-chunked**: otimizado para série temporal em um único ponto;
- **time-chunked**: otimizado para mapa global em um único passo de tempo.

```python
ds = xr.open_zarr(
    timechunked_wav_url,
    consolidated=True,
    storage_options={"headers": {"Authorization": f"Bearer {cdsapi_key}"}}
)
```

O dataset completo (variáveis `mwd`, `mwp`, `swh`) representa cerca de **2 TB**, com chunks de tamanho `(1, 361, 720)`.

### Exemplos de análise
- Plotar altura significativa de onda (`swh`) em um único instante com `matplotlib`;
- Usar o dataset **geo-chunked** para extrair uma série temporal em um ponto específico (ex.: litoral do Rio de Janeiro) de forma eficiente.

## 4. Sofar Spotter drifters — arrays "esfarrapados" (ragged arrays)

O [Sofar Spotter Archive](https://registry.opendata.aws/sofar-spotter-archive/) fornece dados históricos de ondas e vento inferido de uma rede global de boias **Spotter** (pequenas boias movidas a energia solar).

```python
s3_uri = "https://sofar-spotter-archive.s3.amazonaws.com/spotter_data_bulk_zarr"
ds = xr.open_zarr(s3_uri)
```

O dataset tem dimensões `index` (amostras) e `trajectory` (boias/drifters individuais).

### Por que "ragged array"?

Cada boia registra um número diferente de observações (por causa do tempo de implantação, frequência de relatório, vida útil do instrumento etc.). Existem duas formas de representar isso:

- **Array incompleto (incomplete array)**: cada coluna é uma boia, preenchendo com valores ausentes as séries mais curtas — intuitivo, mas desperdiça espaço de armazenamento em datasets grandes.
- **Array contíguo "esfarrapado" (contiguous ragged array)**: as observações de todas as boias são armazenadas sequencialmente em um único array, com variáveis de índice adicionais (como `rowsize`) identificando quais observações pertencem a cada trajetória — evita armazenar valores ausentes.

O Sofar Spotter Archive e o NOAA Global Drifter Program usam essa segunda abordagem.

### Extraindo e plotando uma trajetória individual

```python
import numpy as np
spotter_id = 'SPOT-0164'

# índices de início de cada trajetória
traj_idx = np.insert(np.cumsum(ds.rowsize.values), 0, 0)
j = np.where(ds.trajectory == spotter_id)[0][0]
sli = slice(traj_idx[j], traj_idx[j+1])
```

Com o índice `sli`, é possível extrair latitude/longitude/altura de onda daquela boia específica e plotar a trajetória no mapa (usando `cartopy`), colorida pela altura significativa de onda.

## 5. NEMO Near-Present-Day (NPD) — simulações oceânicas do NOC

As simulações **Near-Present-Day** do National Oceanography Centre (NOC, Reino Unido) são rodadas multi-decadais do modelo oceânico NEMO, em resoluções nominais de 1°, 1/4° e 1/12°. Os dados ficam armazenados em formato **Icechunk** e são organizados via catálogo **STAC**.

O pacote Python `OceanDataStore` facilita a busca e abertura desses datasets:

```python
from OceanDataStore import OceanDataCatalog

catalog = OceanDataCatalog(catalog_name="noc-stac")
catalog.search(
    collection="noc-npd-era5",
    standard_name="sea_surface_temperature",
)

ds_npd = catalog.open_dataset(
    id=catalog.available_items[0],
    start_datetime="1980-01",
    end_datetime="1990-12",
)

ds_npd["tos_con"].mean(dim="time_counter").plot(cmap="RdBu_r")
```

A busca é feita por **metadados** (nome padrão CF, coleção, período), sem precisar saber a URL exata do Zarr store.

## 6. Outros datasets Zarr abertos para explorar

- **CMIP6 Zarr na AWS** — saídas de modelos climáticos globais;
- **CarbonPlan Zarr datasets** — dados climáticos downscaled, acessíveis via URLs HTTPS;
- **Earthmover Marketplace** — coleção de datasets geocientíficos abertos, alguns em Zarr.

## Exercícios propostos (resumo)

1. **ECMWF AIFS SINGLE**: identificar dimensões/coordenadas, calcular série temporal de média global (uma semana) e mapa espacial em um instante.
2. **ERA5 (CDS)**: inspecionar dimensões/variáveis, selecionar uma variável (ex. `mwp`), calcular média global anual e mapa espacial.
3. **Ragged arrays (Sofar Spotter)**: identificar a estrutura ragged, extrair a série temporal de uma trajetória específica e plotá-la.
4. **NEMO NPD**: buscar no catálogo, abrir um item para um período (2000–2010) e plotar a temperatura média da superfície do mar, mantendo os dados "lazy" o máximo possível.
5. **(Opcional) Mini-projeto**: escolher um dos datasets, definir uma pergunta de pesquisa, explorar dimensões/chunking/metadados e realizar uma pequena análise/visualização, refletindo sobre as dificuldades de acesso e o impacto do chunking/armazenamento no desempenho.

## Pontos-chave (Key Points)

- Existem muitos datasets Zarr abertos para oceanografia, clima e meteorologia (ERA5 ARCO, Sofar Spotter, previsões de ensemble ECMWF/IFS, CMIP6, produtos marinhos, entre outros).
- Ferramentas Python como `xarray`, `zarr` e `fsspec` facilitam abrir e explorar dados Zarr hospedados em object storage na nuvem.
- Datasets reais ilustram grades regulares, arrays esfarrapados (ragged), dimensões de ensemble e mais — boa prática para entender estruturas de dados chunked.
- Trabalhar de forma prática com esses datasets ajuda a construir intuição sobre estrutura de dados, desempenho e boas práticas para workflows científicos "cloud-native".

---
*Este resumo cobre o Capítulo 8 do curso [Cloud-Native Geoscience Data Workflows](https://noc-oi.github.io/cloud-native-geoscience-course/), incluindo exercícios práticos com os datasets AIFS, ERA5, Sofar Spotter e NEMO NPD (não reproduzidos integralmente aqui).*
