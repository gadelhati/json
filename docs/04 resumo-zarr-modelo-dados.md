# Resumo: Modelo de Dados Zarr e Armazenamento em Chunks (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/04-zarr.html](https://noc-oi.github.io/cloud-native-geoscience-course/04-zarr.html)
Capítulo 4 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Explicar o que é o Zarr, como seu modelo de dados difere de formatos como NetCDF ou HDF5, como funcionam seus metadados de arrays e grupos, o que é armazenamento em chunks e por que isso importa para dados oceânicos, climáticos e meteorológicos. Também apresenta a prática de abrir e inspecionar um repositório Zarr com Python.

## Zarr em contexto

O Zarr é um formato e modelo de dados de código aberto para armazenar arrays N-dimensionais fragmentados (chunked) de forma compatível tanto com object storage em nuvem quanto com sistemas de arquivos tradicionais. Nasceu na comunidade científica Python e hoje tem implementações em várias linguagens (Python, Rust, Julia, MATLAB, R, JavaScript, entre outras).

Para dados terrestres e climáticos, o Zarr vem sendo adotado por grandes provedores (ex.: produtos Sentinel da ESA, National Weather Service dos EUA) e por projetos como Earth Data Hub, Pangeo e DestinE, justamente por escalar até volumes de petabytes e permanecer acessível a partir de ferramentas como o xarray.

## Zarr como modelo de dados

Em alto nível, o Zarr representa grandes arrays N-dimensionais como peças menores que podem ser armazenadas e acessadas com eficiência. Um dataset Zarr é organizado em torno de três conceitos principais:

- **Arrays**: arrays N-dimensionais de um único tipo de dado, divididos em chunks.
- **Grupos**: contêineres hierárquicos que podem conter arrays e subgrupos, como pastas (semelhante aos grupos do HDF5).
- **Stores** (repositórios): o sistema de armazenamento subjacente que guarda dados e metadados — pode ser um diretório local, um bucket S3 ou outro backend de chave-valor.

Um dataset climático ou oceânico típico pode usar um grupo contendo arrays como `temperature`, `salinity`, `u_wind` e `v_wind`, organizados por dimensões como `time`, `lat`, `lon` e `level`. Em vez de um único arquivo monolítico, cada array é dividido em chunks, cada um armazenado e lido separadamente.

### Zarr v2

Especificação de armazenamento mais antiga e amplamente usada. No Zarr v2, o dataset é organizado como uma estrutura de diretórios com pequenos arquivos de metadados:

- `.zgroup` — metadados do grupo.
- `.zattrs` — atributos definidos pelo usuário.
- `.zmetadata` — metadados consolidados (quando habilitado).

Dentro do grupo, cada array aparece como seu próprio diretório, contendo:

- `.zarray` — metadados do array (formato, tipo de dado, layout dos chunks, etc.).
- `.zattrs` — atributos específicos do array.
- Arquivos de chunk, nomeados por suas coordenadas (ex.: `0.0.0`, `0.0.1`, `1.0.0`).

Um ponto-chave do Zarr v2 é que os metadados são pequenos, legíveis por humanos e fáceis de inspecionar sem abrir o dataset inteiro — o que facilita explorar a estrutura antes de qualquer análise.

### Zarr v3

Especificação mais recente. Mantém a mesma ideia básica (arrays e grupos em chunks), mas atualiza a estrutura de metadados e parte da terminologia para melhor suportar usos científicos e cloud-native modernos. Em vez de vários arquivos JSON pequenos e ocultos espalhados pela árvore de diretórios, o Zarr v3 usa arquivos `zarr.json` para descrever grupos e arrays.

Principais mudanças de terminologia do v2 para o v3:

| Zarr v2 | Zarr v3 |
|---|---|
| `dtype` | `data_type` |
| `chunks` | `chunk_grid` |
| `dimension_separator` | `chunk_key_encoding` |
| `order` | codec de transposição |
| `filters` / `compressor` | campo genérico `codecs` |

Os dados de chunk ficam armazenados separadamente em caminhos como `c/0/0/0`. O Zarr v3 também adiciona suporte mais explícito a **sharding**, em que vários chunks podem ser agrupados dentro de um objeto de armazenamento maior — reduzindo a sobrecarga de gerenciar um número enorme de arquivos/objetos muito pequenos, especialmente em object storage na nuvem (tema aprofundado em capítulos posteriores).

## Armazenamento em chunks: como o Zarr guarda grandes arrays

O *chunking* é central no design do Zarr. Em vez de armazenar um array muito grande como um único bloco, o Zarr o divide em pedaços menores chamados **chunks** — pequenos blocos N-dimensionais do array (ex.: um subconjunto de `time × lat × lon`), cada um armazenado e lido separadamente.

É como recortar um mapa muito grande em "ladrilhos" (tiles): se você só quer olhar uma região, não precisa desenrolar o mapa inteiro — busca apenas os ladrilhos necessários. O Zarr faz o mesmo com dados multidimensionais.

Para dados ambientais, o chunking é útil porque permite:

- **Leituras seletivas**: uma série temporal em um ponto, uma região ou uma variável podem ser lidas sem varrer o dataset inteiro.
- **Paralelismo**: chunks diferentes podem ser processados ao mesmo tempo por workers diferentes.
- **Compressão**: cada chunk pode ser comprimido separadamente, reduzindo custo de armazenamento e transferência.

É por isso que o Zarr se encaixa bem em fluxos de trabalho na nuvem: o acesso via object storage e HTTP funciona naturalmente quando os dados são organizados em muitas peças endereçáveis, em vez de um único arquivo monolítico.

### Pensando em chunks na prática

Imagine um dataset de temperatura oceânica com dimensões `time = 120`, `lat = 721`, `lon = 1440`. Armazenado como um único array gigante, até operações pequenas exigiriam ler uma quantidade enorme de dados. Com chunking, o dataset pode ser dividido em blocos menores — um chunk por grupo de instantes de tempo, um chunk por bloco espacial, ou uma combinação dos dois. Quando alguém pede "a série temporal neste ponto" ou "esta região neste mês", o software pode requisitar apenas os chunks que se sobrepõem a essa consulta.

> **Atenção — o chunking também tem trade-offs**: chunks grandes demais fazem cada leitura trazer mais dados do que o necessário; chunks pequenos demais geram um número enorme de objetos minúsculos, tornando o gerenciamento das requisições ineficiente (especialmente em object storage). O equilíbrio ideal depende dos tipos de análise mais comuns — motivo pelo qual o recurso de *sharding* foi introduzido no Zarr.

## Por que o Zarr importa para oceanografia, clima e meteorologia

- **De arquivos para cubos de dados**: arquivos podem ser publicados como repositórios Zarr coerentes representando grandes cubos de dados (ex.: campos climáticos globais do ERA5 ou produtos de observação da Terra do Sentinel), em vez de milhares de arquivos NetCDF/GRIB individuais.
- **Acesso direto na nuvem**: cientistas podem abrir datasets diretamente via S3/HTTPS em notebooks ou aplicações, lendo apenas os chunks necessários em vez de baixar arquivos inteiros.
- **Interoperabilidade e ferramental**: o Zarr integra-se bem com xarray, dask, Icechunk e ferramentas de visualização como browzarr e zarr-cesium.
- **Padrões orientados pela comunidade**: o Zarr vem sendo adotado por grandes provedores e projetos, com convenções emergindo para garantir interoperabilidade e boas práticas.

Em resumo, o Zarr não substitui semânticas científicas como o CF ou o Common Data Model — ele oferece uma nova camada de armazenamento e acesso que funciona nativamente com infraestrutura em nuvem e ferramentas modernas de análise.

## Inspecionando um repositório Zarr com Python

A lição demonstra, com a biblioteca `zarr` em Python, como abrir um repositório Zarr (`zarr.open_group(...)`), listar seus grupos e arrays (`store.groups()`, `store.arrays()`), navegar por subgrupos (ex.: grupos `"0"` e `"1"` de uma pirâmide multiescala) e inspecionar um array específico — no exemplo, o array `sst` (sea surface temperature), com shape `(10, 360, 720)` (10 passos de tempo × 360 pontos de latitude × 720 de longitude), tipo `float32`, e atributos herdados do GRIB original (nome longo, unidades em Kelvin, etc.).

Um ponto importante destacado: ao inspecionar a estrutura e os metadados dessa forma, **o dataset inteiro não é carregado na memória** — os dados reais só são lidos do disco ou do object storage quando explicitamente solicitados (ex.: ao fatiar o array). Esse carregamento preguiçoso (*lazy loading*) é um recurso central do Zarr e do xarray, permitindo lidar com grandes datasets de forma eficiente.

Também é possível inspecionar o *shape* dos chunks do array (ex.: `sst.chunks`, retornando algo como `(1, 360, 360)` ou `(10, 100, 100)`), que representa quantos passos de tempo e qual bloco espacial cada chunk cobre. Chunks "altos em tempo" favorecem leituras de série temporal em um local específico, enquanto chunks que cobrem regiões espaciais maiores favorecem agregações espaciais — a escolha do formato do chunk é sempre um compromisso baseado na carga de trabalho dominante.

## Pontos-chave (resumo final da lição)

1. O Zarr organiza dados em grupos e arrays armazenados como chunks endereçáveis, suportando leituras e escritas parciais eficientes.
2. Os metadados do Zarr descrevem a estrutura dos arrays, o chunking e os atributos, podendo ser estendidos por convenções compartilhadas para fluxos de trabalho geocientíficos.
3. O armazenamento em chunks é central para o desempenho do Zarr, pois permite que as ferramentas leiam apenas as peças necessárias para uma dada consulta ou cálculo.
4. Inspecionar um repositório Zarr com Python e xarray ajuda a distinguir a exploração barata de metadados do carregamento real dos dados.
5. Entender o modelo de dados, os metadados e o layout de chunks é a base para as próximas lições sobre rechunking, processamento paralelo e análise cloud-native.

---
*Este é o Capítulo 4 de um curso de 16 capítulos. O próximo capítulo aborda Python para Zarr.*
