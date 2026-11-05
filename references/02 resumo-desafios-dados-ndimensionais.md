# Resumo: Desafios dos Dados N-Dimensionais (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/02-ndata-challenges.html](https://noc-oi.github.io/cloud-native-geoscience-course/02-ndata-challenges.html)
Capítulo 2 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Entender como formatos como NetCDF, GRIB e HDF5 organizam dados n-dimensionais, por que os conjuntos de dados de meteorologia e oceanografia cresceram tanto nas últimas décadas, e por que compartilhar/acessar esses dados por meio de downloads de arquivos inteiros deixou de ser viável — abrindo caminho para soluções cloud-native (chunking, object storage).

## Por que dados n-dimensionais são difíceis

Na oceanografia e meteorologia, a maioria dos produtos de dados é naturalmente n-dimensional: tempo, latitude, longitude, altura/profundidade, e frequentemente dimensões adicionais como membro de ensemble, tempo de previsão (lead time) e variável.

Bancos de dados genéricos tentaram lidar com esses dados no passado, mas não tratavam arrays multidimensionais como objetos de primeira classe e tinham desempenho ruim em grandes datasets científicos — o que motivou a criação de formatos especializados como NetCDF e GRIB.

### NetCDF — arrays autodescritivos
Criado no final dos anos 1980 como formato portátil e autodescritivo para dados científicos organizados em arrays (ex.: saídas de modelos climáticos e oceânicos). Armazena variáveis, dimensões (`time`, `lat`, `lon`, `level`) e atributos (metadados) em um único container.

- **NetCDF-3**: layout simples e contíguo.
- **NetCDF-4**: construído sobre o HDF5 como camada de armazenamento, adicionando grupos e suporte a arrays muito grandes e hierarquias complexas.

À medida que os datasets crescem, as escolhas organizacionais (quais dimensões incluir, como estruturar variáveis e arquivos) afetam fortemente a facilidade de uso.

### GRIB — intercâmbio operacional compacto
Formato da Organização Meteorológica Mundial (OMM/WMO) voltado à transmissão e armazenamento eficiente de campos meteorológicos em grade, especialmente saídas de previsão numérica do tempo. Organiza os dados em "mensagens", cada uma com um campo e metadados codificados, regidas por tabelas da OMM.

- O **GRIB2** (padronizado no início dos anos 2000) trouxe metadados mais flexíveis, mais métodos de compressão e melhor suporte a valores ausentes.
- É muito compacto e adequado a fluxos operacionais, mas mais difícil de tratar como um array n-dimensional simples — mensagens heterogêneas podem precisar ser filtradas/reagrupadas antes da análise.

### HDF5 — container genérico de alto desempenho
Formato hierárquico geral que sustenta a camada de armazenamento do NetCDF-4. Oferece grupos, datasets e metadados ricos, sendo amplamente adotado além da ciência atmosférica (ex.: sensoriamento remoto). O NetCDF-4 esconde a complexidade do HDF5 atrás da sua própria API, então a maioria dos usuários trabalha com variáveis, dimensões e atributos sem lidar diretamente com os detalhes de armazenamento.

## Trinta anos de crescimento dos volumes de dados

Nas últimas três décadas, várias tendências impulsionaram o crescimento dos dados em meteorologia e oceanografia:

- Maior resolução espacial (de grades globais grosseiras a domínios em escala de quilômetro).
- Maior resolução temporal (saídas horárias/sub-horárias em vez de apenas mensais/diárias).
- Mais níveis verticais nos modelos de atmosfera e oceano.
- Arquivos mais longos de observações e reanálises, cobrindo várias décadas.
- Ensembles de previsões e simulações climáticas, multiplicando o volume pelo número de membros.

Isso levou arquivos de dados a passarem de simples coleções de arquivos para coleções na escala de terabytes e até petabytes. Exemplos citados na lição:

| Dataset | Aplicação | Nº de arquivos | Tamanho |
|---|---|---|---|
| CHESS-SCAPE | Projeções climáticas do Reino Unido em 1 km, 1980–2080 | 387.840 | ~11 TB |
| NOC NEMO NPD | Simulações oceânicas globais NEMO em várias resoluções | não consolidado | ~71 TB |
| CMIP6 / ESGF | Modelos climáticos globais e experimentos diversos | milhões de variações | ~21 PB |
| ERA5 surface | Reanálise atmosférica e de superfície do ECMWF | ~5,31 milhões | ~6 TB |
| ERA5 full | Reanálise global horária | sem contagem única | ordem de PB |

## Padrões de acesso típicos hoje

Na prática, profissionais de meteorologia e oceanografia costumam:

- Usar NetCDF (NetCDF-3 ou NetCDF-4/HDF5) para arquivamento e análise de campos em grade e séries temporais.
- Usar GRIB para produtos operacionais de previsão e intercâmbio entre centros.
- Recorrer a bibliotecas de alto nível como o **xarray** para abrir arquivos NetCDF e GRIB como datasets n-dimensionais rotulados.

A lição inclui exercícios práticos com xarray: inspecionar a estrutura de um arquivo NetCDF (dimensões, coordenadas, atributos), comparar a abertura de um mesmo dado em NetCDF vs. GRIB (usando o engine `cfgrib`), e refletir sobre como o crescimento de resolução, frequência e duração de um dataset afeta seu tamanho, organização e forma de compartilhamento.

## Compartilhamento de dados e acesso a subconjuntos

### Padrão tradicional: baixar tudo para depois analisar
Muitos fluxos de trabalho ainda: publicam arquivos NetCDF/GRIB em servidores FTP/HTTP ou portais, baixam os arquivos completos para disco local ou servidor compartilhado, e só então os abrem com ferramentas como xarray.

Isso funciona bem para datasets pequenos, mas para arquivos de multi-gigabytes ou multi-terabytes se torna ineficiente:

- Downloads de arquivos inteiros são lentos e caros (rede, armazenamento, tempo).
- Usuários geralmente precisam de apenas um subconjunto (uma variável, uma região, uma janela de tempo), não do arquivo completo.
- Vários usuários baixando os mesmos arquivos grandes geram duplicação e sobrecarga de armazenamento desnecessárias.

Mesmo quando há *chunking* interno no NetCDF-4/HDF5, o arquivo ainda é tratado como um único objeto, e os formatos clássicos são otimizados para sistemas de arquivos POSIX, não para acesso direto a object storage.

> **POSIX vs. object storage**: um sistema de arquivos POSIX é o modelo tradicional de diretórios e caminhos acessados localmente ou por montagem. Um sistema de object storage expõe armazenamento em nuvem por meio de operações do tipo "arquivo", mas os dados são acessados via APIs de objeto, não por uma árvore de diretórios comum.

### Subsetting no lado do servidor e acesso remoto
Protocolos como o **OPeNDAP** e APIs modernas permitem que clientes solicitem apenas subconjuntos de um arquivo NetCDF (ex.: uma caixa delimitadora espacial e um intervalo de tempo), sem transferir o arquivo inteiro. Isso reduz duplicação e centraliza o acesso, mas exige infraestrutura mantida, e o desempenho ainda depende da carga do servidor e da largura de banda da rede.

### Considerações de armazenamento
Manter grandes arquivos em sistemas de arquivos tradicionais em rede pode ficar caro e difícil de escalar, especialmente quando os dados precisam ficar disponíveis online por muitos anos. Por isso, infraestruturas em nuvem e institucionais têm adotado cada vez mais o **object storage** para grandes datasets majoritariamente somente-leitura, pois escala horizontalmente e pode ser mais barato por terabyte.

O xarray pode ser "preguiçoso" (*lazy*) ao abrir arquivos NetCDF — inspecionando metadados sem carregar todos os valores de imediato —, mas muitas análises acabam puxando grande parte do arquivo para a memória de qualquer forma. Isso reforça por que arquivos científicos grandes tendem a ser mais bem geridos em servidores centrais ou object storage do que em cópias locais duplicadas, e é uma das razões pelas quais formatos cloud-native como o Zarr (tema dos próximos capítulos) estão ganhando importância.

## Resumo: formato, escala e acesso como desafios centrais

Nas últimas três décadas, a meteorologia e a oceanografia passaram de datasets modestos e processados localmente para arquivos globais multi-decadais e previsões de alta resolução armazenadas em formatos especializados. O NetCDF (especialmente NetCDF-4/HDF5) oferece um modelo flexível e autodescritivo para arrays n-dimensionais, enquanto o GRIB oferece armazenamento e transmissão compactos e voltados à operação, regidos por códigos e tabelas da OMM.

Ferramentas como o xarray permitem abrir ambos os formatos como datasets n-dimensionais rotulados, mas a escala crescente dos dados e as escolhas organizacionais desses formatos geram desafios reais de compartilhamento eficiente, desempenho, escalabilidade, memória e custo de armazenamento. O subsetting no lado do servidor e o armazenamento em chunks ajudam, mas os formatos clássicos baseados em arquivo ainda giram em torno de um único arquivo e sistemas de arquivos compartilhados.

## Pontos-chave (resumo final da lição)

1. O NetCDF oferece um modelo de dados autodescritivo e orientado a arrays para datasets científicos n-dimensionais, amplamente usado em meteorologia e oceanografia.
2. O GRIB é um formato compacto e baseado em mensagens da OMM, projetado para transmissão operacional de campos meteorológicos em grade, usando tabelas e códigos para representar metadados.
3. Os volumes de dados cresceram drasticamente com maior resolução, saídas mais frequentes, arquivos mais longos e ensembles ao longo das últimas três décadas.
4. Em muitos fluxos de trabalho atuais, grandes arquivos NetCDF e GRIB ainda são baixados por completo para servidores locais ou compartilhados, mesmo quando só se precisa de subconjuntos.
5. O subsetting no lado do servidor (ex.: OPeNDAP) e arquivos centralizados podem reduzir a duplicação, mas o armazenamento de longo prazo em sistemas de arquivos tradicionais fica caro em escala, comparado ao object storage.
6. Entender como os formatos existentes organizam dados n-dimensionais — e onde eles falham diante do crescimento em tamanho e uso compartilhado — prepara o terreno para o chunking e as soluções cloud-native dos próximos capítulos.

---
*Este é o Capítulo 2 de um curso de 16 capítulos. O próximo capítulo trata de Formatos Cloud-Native.*
