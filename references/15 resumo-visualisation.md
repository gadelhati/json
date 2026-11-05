# Resumo: Visualizando Zarr Multiscale e GeoZarr

**Fonte:** [Cloud-Native Geoscience Data Workflows – Capítulo 15: Visualizing Multiscale Zarr and GeoZarr](https://noc-oi.github.io/cloud-native-geoscience-course/15-visualisation.html)

Este capítulo explica como preparar e visualizar dados Zarr geoespaciais de forma interativa em navegadores, usando pirâmides multiscale e as convenções **GeoZarr**.

## Objetivos da aula

- Explicar como datasets Zarr geoespaciais podem ser visualizados eficientemente no navegador e em ferramentas desktop.
- Descrever por que chunking e pirâmides multiscale são importantes para visualização interativa.
- Apresentar as convenções GeoZarr para datasets Zarr geoespaciais e multiscale.
- Usar o **Topozarr** para construir um dataset Zarr multiscale a partir de um Zarr store existente.
- Entender como clientes de navegador (ex.: OpenLayers, zarrita, zarr-cesium) podem renderizar GeoZarr multiscale sem um servidor de tiles dedicado.

## Introdução

O Zarr pode ser usado tanto para análise científica quanto para visualização web. Como os dados são armazenados em chunks, navegadores ou servidores podem buscar apenas as partes necessárias para a visualização atual do mapa, em vez de carregar o dataset inteiro.

Existem dois padrões principais:
- **Baseado em servidor:** um backend lê o Zarr store e serve tiles ou imagens.
- **Baseado em cliente:** o navegador lê os chunks diretamente do object storage e renderiza com **WebGL + GPU**.

## Chunking importa para a visualização

Para grandes datasets geoespaciais (grades globais, imagens de satélite), a visualização interativa geralmente envolve olhar pequenas janelas (viewports) de cada vez, com zoom e pan mudando o subconjunto de dados necessário.

Por isso, um bom chunking deve:
- Alinhar-se com viewports e níveis de zoom típicos (ex.: tiles de 256×256 ou 512×512 pixels).
- Ser pequeno o suficiente para transferência rápida (dezenas/centenas de KB), mas grande o suficiente para evitar excesso de requisições HTTP separadas.

Chunking ineficiente (chunks enormes ou mal alinhados) pode forçar o carregamento de muito mais dados do que o necessário, causando interações lentas, alto consumo de banda e má experiência do usuário. Em geral, prefere-se "chunkar" ao longo das dimensões espaciais (x, y) e possivelmente banda/tempo.

## Pirâmides multiscale

A ideia vem dos **Cloud-Optimized GeoTIFFs (COGs)**, amplamente usados para imagens: eles armazenam múltiplas resoluções dos mesmos dados em um único arquivo, permitindo que clientes solicitem apenas a resolução necessária para o nível de zoom atual.

O mesmo conceito é aplicado ao Zarr através de **pirâmides multiscale**: cada nível é uma versão "downsampled" (reduzida) dos dados originais.

Estrutura típica:
- **Nível 0:** grade em resolução total.
- **Nível 1:** versão reduzida (ex.: 2× mais grosseira).
- **Nível 2:** ainda mais reduzida, e assim por diante.

Benefícios: visualização eficiente em diferentes níveis de zoom sem sobrecarregar o cliente — uma visão global de mapa pode usar baixa resolução, enquanto um zoom local busca tiles de alta resolução apenas para a área de interesse.

A convenção **multiscales** do GeoZarr formaliza como armazenar e descrever essas pirâmides no Zarr.

## GeoZarr: convenções geoespaciais para Zarr

**GeoZarr** é um conjunto de convenções modulares para codificar datasets geoespaciais em Zarr. As convenções centrais são:

- **`proj`** — descreve o sistema de referência de coordenadas (CRS).
- **`spatial`** — descreve transformações espaciais.
- **`multiscales`** — descreve a estrutura da pirâmide multiscale.

Essas convenções são registradas via um atributo de metadados `zarr_conventions` e usam atributos com namespace, como `proj:code`, `spatial:transform` e `multiscales`.

O GeoZarr está sendo desenvolvido como um **padrão OGC**, construído sobre o Unidata Common Data Model e as convenções CF, com o objetivo de unir as comunidades científica e geoespacial.

Referências úteis:
- Visão geral: https://geozarr.org
- Convenções (proj, spatial, multiscales): https://geozarr.org/conventions.html
- Rascunho da especificação: https://zarr.dev/geozarr-spec/documents/standard/template/geozarr-spec.html

## Topozarr: criando Zarr multiscale para visualização

**Topozarr** é uma biblioteca Python da **CarbonPlan** que ajuda a criar Zarr stores multiscale seguindo as convenções GeoZarr, a partir de um dataset Zarr já existente.

### Fluxo de trabalho

1. **Abrir o dataset Zarr com xarray:**
```python
import xarray as xr
ds = xr.open_zarr(f"{base_path}data/era5_sst/ocean_temperature.zarr", consolidated=True)
```

2. **Definir o CRS** (ex.: WGS84 / EPSG:4326):
```python
ds = ds.proj.assign_crs({"EPSG": 4326})
```

3. **Criar a pirâmide** com `create_pyramid`, especificando número de níveis, dimensões x/y, tamanho de chunk alvo, método de downsampling (ex.: `"mean"`, `"nearest"`) e chunks por shard:
```python
from topozarr import create_pyramid

pyramid = create_pyramid(
    ds,
    levels=2,
    x_dim="longitude",
    y_dim="latitude",
    target_chunk_bytes=512 * 512 * 4,
    method="mean",
    chunks_per_shard=4
)
```

4. **Inspecionar os níveis** convertendo em datatree:
```python
pyramid_tree = pyramid.as_datatree()
print(pyramid_tree["0"])  # resolução total
print(pyramid_tree["1"])  # reduzida
```

5. **Salvar toda a pirâmide em um único Zarr store multiscale**, seguindo as convenções GeoZarr — por exemplo, diretamente em object storage (S3), usando `zarr.storage.FsspecStore`. Como a operação pode ser custosa, recomenda-se usar um cluster Dask local (`dask.distributed.Client`).

```python
pyramid_tree.to_zarr(
    store,
    mode="w",
    consolidated=True,
    encoding=pyramid.encoding,
    align_chunks=True
)
```

6. **Reabrir e inspecionar** o Zarr multiscale usando `xr.open_datatree` (necessário por se tratar de uma datatree).

**Aviso de API instável:** o suporte a pirâmides multiscale é relativamente recente no ecossistema Zarr, e o Topozarr está em desenvolvimento ativo — a API pode mudar entre versões. Recomenda-se fixar versões dos pacotes.

## Visualização no navegador: opções de servidor e cliente

Com um Zarr store multiscale compatível com GeoZarr, há duas formas principais de visualizá-lo no navegador: via **servidor** de tiles ou via **cliente** que lê o Zarr diretamente do object storage. Em ambos os casos, os metadados multiscale são essenciais para indicar ao visualizador qual nível de resolução usar em cada zoom, e um bom chunking continua importante.

### Visualização baseada em servidor

Um serviço Python lê os dados Zarr no backend e os transforma em tiles de mapa sob demanda (modelo clássico de web-mapping). Opções principais:

- **TiTiler** — serviços dinâmicos de tiles que podem renderizar Zarr e outros datasets legíveis por xarray.
- **xpublish-tiles** — um roteador de tiles para xpublish, capaz de servir tiles a partir de dados baseados em xarray/Zarr.

Útil quando se precisa de controle no lado do servidor sobre estilização, reprojeção, controle de acesso ou processamento pesado, mantendo o navegador simples.

### Visualização baseada em cliente

O navegador lê os chunks Zarr diretamente do object storage e os renderiza sozinho, eliminando a necessidade de um servidor de tiles dedicado. Exemplos:

- **zarr-maps** — camada client-side para mapas web no estilo Leaflet/OpenLayers.
- **zarr-cesium** — visualização client-side em 2D e 3D no CesiumJS.
- **zarr-layer** / **deck.gl-raster** — renderização no navegador baseada em carregamento de chunks Zarr e exibição via GPU, para Mapbox e Maplibre.

Essas ferramentas geralmente dependem de um leitor Zarr em JavaScript como o **Zarrita** para buscar dados de chunk do object storage. O navegador então combina esses dados com **WebGL** e a **GPU** para renderizar imagens, superfícies ou tiles de mapa eficientemente.

### Exemplo simples em HTML

O capítulo apresenta um exemplo mínimo (`zarr-maps-openlayers.html`) que usa **zarr-maps** com **OpenLayers** para visualizar um dataset Zarr multiscale no navegador. O usuário pode editar a `zarrUrl` e a `variable` para apontar para seu próprio dataset, rodar um servidor web local (`python -m http.server 8000`) e abrir a página no navegador para observar como os dados carregam e renderizam em diferentes escalas de zoom.

Também há um exercício para abrir o dataset multiscale no **zarr-cesium** (https://noc-oi.github.io/zarr-cesium/), explorando visualização 3D em torno do globo, incluindo exemplos de Zarr-Cube e Zarr-Cube-Velocity.

## Pipeline completo: da conversão à visualização

O capítulo conecta esta lição com a lição 10 (conversão de NetCDF para Zarr): depois de converter os dados, constrói-se a pirâmide multiscale com Topozarr e visualiza-se no navegador usando as convenções GeoZarr — um passo adicional de processamento multiscale antes da visualização.

**Atenção com grades irregulares:** para datasets em grades regulares o workflow é direto, mas muitos datasets geocientíficos usam grades irregulares ou curvilíneas (ex.: o dataset NEMO Near-Present-Day), onde a relação entre chunks Zarr e tiles de mapa não é direta. Nesses casos, é necessário reprojetar/reamostrar os dados para uma grade regular antes de gerar a pirâmide multiscale, usando bibliotecas como **rioxarray**, **xESMF** e **rasterio**. O capítulo referencia um relatório da Development Seed sobre reprojeção e reamostragem de dados geoespaciais com Python.

## Pontos-chave (Key Points)

- Chunking e pirâmides multiscale são centrais para a visualização interativa de datasets Zarr geoespaciais, permitindo acesso eficiente baseado em tiles em diferentes níveis de zoom.
- O GeoZarr define convenções modulares (proj, spatial, multiscales) para codificar metadados geoespaciais e layouts multiscale sobre o Zarr.
- O Topozarr pode ser usado para construir Zarr stores multiscale a partir de datasets existentes, preparando-os para visualização eficiente.
- Clientes de navegador como OpenLayers (via GeoZarr), zarrita e zarr-cesium podem renderizar dados Zarr diretamente do object storage usando WebGL e aceleração por GPU, sem um servidor de tiles dedicado.
- Combinando convenções GeoZarr, Zarr multiscale e clientes HTML/JS simples, é possível construir workflows de visualização totalmente cloud-native para datasets geoespaciais.
