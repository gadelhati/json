# Resumo: Formatos de Dados, Metadados e Vocabulário (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/01-intro.html](https://noc-oi.github.io/cloud-native-geoscience-course/01-intro.html)
Capítulo 1 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Introduzir os principais formatos de dados usados em oceanografia e meteorologia, explicar o conceito de metadados e vocabulários controlados, e apresentar os padrões internacionais que conectam esses formatos tradicionais aos formatos cloud-native modernos (como o Zarr).

## Por que formatos e metadados importam

Ao trabalhar com dados ambientais, não basta armazenar os valores medidos — é preciso codificar também o significado: o quê, onde, quando, como e sob quais condições algo foi medido.

- **Formatos** definem a organização física dos dados (arrays vs. tabelas, grade vs. vetor, binário vs. texto, cloud-native vs. legado).
- **Metadados e vocabulários** definem a semântica: nomes de variáveis, unidades, sistemas de referência de coordenadas, informações de qualidade e termos controlados.

Usar formatos e metadados padronizados torna os dados autodescritivos e semanticamente consistentes, o que é essencial para interoperabilidade entre modelos, arquivos, ferramentas de visualização e serviços em nuvem.

## Principais formatos de dados

### Formatos de arrays autodescritivos
Armazenam os dados e a metadata estrutural (dimensões, variáveis, unidades, coordenadas) juntos:

- **NetCDF** — formato binário, independente de máquina, muito usado em dados climáticos, oceanográficos e meteorológicos em grade.
- **HDF5** — formato hierárquico (como "pastas"), usado em produtos de satélite e saídas de modelos complexos.
- **Zarr** — formato mais recente, voltado a arrays N-dimensionais fragmentados (chunked), pensado para ambientes de nuvem/object storage. O padrão **GeoZarr** define como representar dados geoespaciais em Zarr.

### Formatos de intercâmbio da OMM (WMO)
Otimizados para transmissão em redes de telecomunicação:

- **GRIB** — formato binário compacto para campos meteorológicos em grade (ex.: previsão numérica do tempo).
- **BUFR** — formato binário flexível, orientado a tabelas, para representar observações meteorológicas e oceanográficas diversas.

### Outros formatos comuns
- **CSV/ASCII** — tabelas de texto simples.
- **GeoTIFF** / **Cloud-Optimized GeoTIFF (COG)** — imagens georreferenciadas 2D.
- **GeoJSON** — geometrias vetoriais em JSON.
- **Shapefile** — formato vetorial GIS mais antigo.
- **Parquet / GeoParquet** — formatos colunares comprimidos, cada vez mais usados em analytics cloud-native (substituindo CSV/Shapefile em vários fluxos de trabalho).
- **XML/JSON** — usados principalmente para documentos de metadados e catálogos.

> **Conceito-chave:** um arquivo é "autodescritivo" quando contém metadados estruturais suficientes (dimensões, variáveis, unidades, sistema de coordenadas) para que uma ferramenta o interprete sem precisar de manuais externos.

## O que é metadado?

Metadado é "dado sobre dado": informação que descreve um conjunto de dados para que pessoas e softwares possam entendê-lo, encontrá-lo e reutilizá-lo. Inclui tipicamente:

- Quem coletou os dados e por quê.
- O que foi medido (variáveis, unidades, métodos).
- Onde e quando (extensão espacial/temporal, sistema de referência).
- Como foi processado (algoritmos, flags de qualidade, versões).
- Como acessar, citar e interpretar os dados.

O padrão **ISO 19115** define os elementos de metadados geográficos usados em catálogos e portais de descoberta.

### Vocabulários controlados

Metadados em texto livre podem ser ambíguos (ex.: "temp", "T", "temperatura"). Vocabulários controlados resolvem isso com listas curadas de termos padronizados.

- **NERC Vocabulary Server (NVS)**, mantido pelo BODC, publica listas de termos para plataformas, instrumentos, parâmetros, projetos e regiões geográficas, usando o modelo SKOS.
- Servem para preencher listas em editores de metadados, marcar dados com URIs estáveis (em vez de texto livre) e permitir buscas semânticas entre diferentes esquemas de metadados.
- **MEDIN Discovery Metadata Standard** — perfil marinho britânico alinhado ao GEMINI, ao INSPIRE e à ISO 19115, focado em "metadados de descoberta" (elementos essenciais para catálogos).

## Padrões-chave

- **Convenções CF (Climate and Forecast)** — definem atributos como `standard_name`, `units`, `cell_methods`, `coordinates`, `bounds` e `grid_mapping` para descrever dados de ciências da Terra em formatos autodescritivos (originalmente NetCDF), permitindo que ferramentas como o xarray interpretem as variáveis corretamente.
- **ISO 19115 / INSPIRE** — padrão internacional (e sua implementação europeia) para descrever conjuntos de dados geográficos como um todo (identificação, extensão, qualidade, sistema de referência, distribuição), diferente do CF, que descreve variáveis *dentro* do dado.
- **GRIB/BUFR (OMM)** — formas de código usadas operacionalmente para troca de dados meteorológicos e oceanográficos.
- **STAC (SpatioTemporal Asset Catalogs)** — linguagem baseada em JSON/GeoJSON para organizar ativos geoespaciais no espaço e no tempo, com três objetos principais: *Catalog*, *Collection* e *Item*. Geralmente usado em conjunto com metadados de descoberta ISO 19115.

### Duas camadas de metadados
- **Metadados internos** (dentro do arquivo, ex.: atributos CF em NetCDF) — permitem que ferramentas de análise interpretem os arrays corretamente.
- **Metadados de descoberta** (MEDIN, GEMINI, INSPIRE, ISO 19115, STAC) — descrevem o dado em nível mais alto (título, resumo, palavras-chave, extensão, contato) em catálogos, permitindo que usuários encontrem e avaliem o dado.

## Por que seguir padrões é importante

- **Interoperabilidade**: dados NetCDF compatíveis com CF podem ser lidos por bibliotecas como xarray, Iris e CF-Python sem código customizado.
- **Descobribilidade**: registros de metadados compatíveis com ISO 19115/INSPIRE/MEDIN podem ser colhidos por catálogos nacionais e internacionais.
- **Clareza semântica**: vocabulários controlados via NVS garantem que diferentes conjuntos de dados usem os mesmos conceitos bem definidos.
- **Governança e eficiência**: incorporar gestão de dados (padrões, metadados, vocabulários) à política organizacional reduz riscos e custos ao longo do ciclo de vida dos dados.

Para dados cloud-native, esses padrões são o que permite migrar de arquivos tradicionais para armazenamento em objeto e APIs sem perder significado — por exemplo, o alinhamento do GeoZarr com CF/NetCDF, e de catálogos com STAC.

## Pontos-chave (resumo final da lição)

1. Oceanografia e meteorologia usam formatos de arrays autodescritivos (NetCDF, HDF5, Zarr) e formatos de intercâmbio da OMM (GRIB, BUFR).
2. Metadado é "dado sobre dado" e existe tanto dentro dos arquivos (atributos CF) quanto em registros de descoberta separados (ISO 19115, INSPIRE, MEDIN).
3. Vocabulários controlados, disponibilizados por serviços como o NERC Vocabulary Server, tornam os metadados consistentes e processáveis por máquina.
4. As convenções CF definem como descrever variáveis, grades e coordenadas em formatos autodescritivos.
5. Perfis de descoberta como o MEDIN alinham a prática nacional a padrões internacionais.
6. O STAC (Catalogs, Collections, Items) oferece uma forma moderna baseada em JSON de organizar e expor ativos geoespaciais em fluxos cloud-native.
7. Formatos cloud-native como o Zarr só se tornam interoperáveis quando combinados com padrões de metadados e vocabulário estabelecidos (CF, Unidata CDM, perfis ISO, NVS), complementados pelo STAC para descoberta.

---
*Este é o Capítulo 1 de um curso de 16 capítulos sobre workflows de dados geocientíficos cloud-native. Os próximos capítulos abordam desafios de dados N-dimensionais, formatos cloud-native, o modelo de dados Zarr, processamento paralelo, STAC, versionamento com Icechunk, entre outros.*
