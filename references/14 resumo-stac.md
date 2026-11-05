# Resumo: Organizando Dados Zarr na Nuvem com STAC

**Fonte:** [Cloud-Native Geoscience Data Workflows – Capítulo 14: Organizing Cloud Zarr Data with STAC](https://noc-oi.github.io/cloud-native-geoscience-course/14-stac.html)

Este capítulo explica o que é o **STAC (SpatioTemporal Asset Catalog)** e como usá-lo para organizar, descrever e tornar descobrível conjuntos de dados Zarr armazenados na nuvem.

## Objetivos da aula

- Explicar o que é STAC e por que é importante em workflows geoespaciais "cloud-native".
- Descrever os papéis de Catalog, Collection e Item no STAC.
- Criar objetos STAC simples (catalog, collection, item) usando a API PySTAC.
- Vincular um dataset Zarr como asset de um Item STAC e entender as opções entre STAC estático (JSON) e baseado em banco de dados (ex.: pgSTAC/PgPystac).

## O que é STAC e por que é importante?

**STAC** é uma família de especificações baseadas em JSON para descrever ativos geoespaciais (arquivos de dados) junto com seus metadados espaço-temporais, facilitando a navegação e busca.

- Site da especificação: https://stacspec.org/en/about/stac-spec/
- Repositório GitHub: https://github.com/radiantearth/stac-spec

### Os três objetos centrais do STAC

- **Catalog:** estrutura hierárquica simples de links que agrupa Items (e outros Catalogs/Collections) para navegação.
- **Collection:** estende o Catalog com metadados adicionais (extensão espacial/temporal, licença, palavras-chave, provedores) para um grupo coerente de Items.
- **Item:** descreve um único ativo espaço-temporal (ex.: uma cena de satélite, um produto ou um cubo de dados Zarr em uma extensão/tempo específicos).

Os arquivos de dados reais (Zarr, NetCDF, Cloud Optimized GeoTIFF etc.) são referenciados como **assets** dentro do Item, cada um com uma URL, tipo de mídia e papéis opcionais (ex.: "data", "thumbnail", "metadata").

### Por que o STAC importa para workflows cloud-native

- Padroniza a forma de descrever e organizar datasets (incluindo Zarr), permitindo que ferramentas e portais os descubram sem código customizado por provedor.
- Funciona tanto como arquivos JSON estáticos em object storage quanto como APIs dinâmicas apoiadas em bancos de dados.
- Um ecossistema de ferramentas já entende STAC: STAC Browser, PySTAC, servidores de STAC API, pgSTAC — tornando dados Zarr "plug-and-play".

### Estrutura de exemplo (JSON)

O capítulo mostra exemplos de JSON para os três níveis:

- **Catalog:** objeto raiz com `links` do tipo `child` apontando para Collections.
- **Collection:** inclui `extent` (bbox espacial + intervalo temporal), `license`, `keywords`, e `links` para parent/items.
- **Item:** é uma GeoJSON Feature com `geometry`, `bbox`, `properties` (datas de início/fim) e um dicionário `assets` apontando para o dado real (ex.: um Zarr store em `s3://bucket/path.zarr`).

## STAC e workflows Zarr cloud-native

- Cada Zarr store é tipicamente referenciado como um **asset** em um Item STAC, apontando para a raiz do store.
- Collections agrupam múltiplos Zarr stores que compartilham um produto (ex.: "ERA5 surface daily Zarr cubes").
- Catalogs fornecem organização de alto nível (por provedor, por projeto).

Benefícios:
- Torna datasets Zarr "descobríveis" por critérios espaciais/temporais e palavras-chave, em vez de ficarem "escondidos" como caminhos brutos em buckets.
- Ferramentas como o **STAC Browser** exibem e permitem buscar o catálogo/API STAC em uma UI genérica.
- Servidores de STAC API com banco de dados (ex.: pgSTAC/PgPystac) suportam buscas rápidas e escaláveis sobre muitos datasets Zarr.

### Exemplos reais de STAC + Zarr

- **NOC STAC Catalog** — o NOC Ocean Data Store publica datasets oceanográficos Zarr como Collections e Items STAC.
- **EOPF Sentinel Explorer** — expõe amostras Zarr do Sentinel como Collections/Items STAC, navegáveis no browser.
- **Microsoft Planetary Computer** — metadados espaço-temporais pesquisáveis para datasets de ciências da Terra hospedados pela Microsoft.

Em todos os casos, o STAC descreve o dataset enquanto o Zarr store permanece como o ativo de dados real, facilitando busca e compartilhamento sem inventar um formato de metadados customizado para cada projeto.

## PySTAC: criando Catalogs, Collections e Items na prática

O **PySTAC** é uma biblioteca Python que espelha a estrutura JSON do STAC, permitindo criar esses objetos programaticamente.

O exemplo usa o dataset Zarr de altura significativa de onda (`swh`) do ERA5, já convertido e hospedado em object storage (da lição 10).

### 1. Criar o Catalog raiz
```python
import pystac

catalog = pystac.Catalog(
    id="Era5-Catalog",
    description="Root catalog for ERA5 datasets"
)
```

### 2. Criar a Collection
Primeiro abre o Zarr com xarray para extrair a extensão espacial (bbox de lon/lat) e temporal (min/max de tempo):
```python
import xarray as xr

url = "https://.../daily_swh"
ds = xr.open_zarr(url, consolidated=True)
lon_min, lon_max = float(ds.longitude.min()), float(ds.longitude.max())
lat_min, lat_max = float(ds.latitude.min()), float(ds.latitude.max())
time_min, time_max = ds.time.min().values, ds.time.max().values
```
Depois define o `Extent` e cria a `Collection`, adicionando-a ao catalog com `catalog.add_child(collection)`.

### 3. Criar o Item apontando para o Zarr store
- A geometria e o bbox vêm das coordenadas do dataset.
- Datas de início/fim vêm dos timestamps.
- Um **Asset** é criado apontando para a URL do Zarr (`media_type="application/vnd+zarr"`; para Icechunk usa-se `"application/vnd.zarr+icechunk"`).
- O asset é anexado ao Item (`item.add_asset("data", asset)`), e o Item é adicionado à Collection (`collection.add_item(item)`).

Isso completa uma hierarquia STAC mínima: **Catalog → Collection → Item → Asset (Zarr)**.

### 4. Salvar como catálogo estático (arquivos JSON)
```python
catalog.normalize_and_save(
    "stac",
    catalog_type=pystac.CatalogType.SELF_CONTAINED,
)
```
Isso gera `catalog.json`, `.../collection.json` e `.../item.json` dentro do diretório `stac/`, com links relativos — prontos para upload em object storage ou servidor web.

## STAC em bancos de dados: pgSTAC / PgPystac

- Catálogos STAC estáticos (arquivos JSON) são simples de publicar e funcionam bem para datasets pequenos/médios.
- À medida que o número de Items cresce (milhões de cenas ou muitos cubos Zarr), buscar via arquivos JSON se torna ineficiente.
- Muitos deployments armazenam metadados STAC em banco de dados (ex.: **pgSTAC**) e expõem via **STAC API**, permitindo consultas rápidas, filtragem e paginação.

Vantagens do STAC baseado em banco de dados:
- Consultas espaciais/temporais e por atributo rápidas em catálogos grandes.
- Índices e otimizadores de consulta lidam com filtros complexos.
- Fonte única de verdade para metadados STAC, atualizável de forma transacional.

**Recomendação geral:** começar com catálogo estático para poucos datasets Zarr e migrar para uma API STAC com banco de dados conforme a coleção cresce.

## Visualizando o catálogo com STAC Browser

O **STAC Browser** é uma aplicação web para navegar catálogos STAC estáticos ou APIs STAC com uma interface amigável.

Passos sugeridos:
1. Fazer upload do diretório `stac/` para um bucket de object storage (exemplo usando `boto3` no capítulo).
2. Usar uma demo hospedada do STAC Browser (ex.: https://browser.moregeo.it/) e inserir a URL do `catalog.json`.

## Pontos-chave (Key Points)

- STAC padroniza a forma de descrever e organizar ativos geoespaciais, incluindo cubos de dados Zarr, facilitando sua descoberta e integração em workflows cloud-native.
- Catalogs, Collections e Items formam uma hierarquia de três camadas: Catalog como ponto de entrada, Collection como agrupamento de datasets, Item como ativo espaço-temporal individual com arquivos de dados vinculados.
- O PySTAC fornece uma API Python para criar e gerenciar Catalogs, Collections e Items STAC, salvando-os como catálogos JSON estáticos ou alimentando APIs STAC.
- Zarr stores em object storage podem ser referenciados como assets de Items STAC, conectando dados de array cloud-native ao ecossistema STAC mais amplo.
- Metadados STAC podem ser armazenados como JSON estático (publicação simples) ou em bancos de dados como pgSTAC/PgPystac (APIs STAC escaláveis e pesquisáveis), e ferramentas como o STAC Browser podem visualizar ambos.
