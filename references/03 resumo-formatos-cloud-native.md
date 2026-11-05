# Resumo: Formatos Cloud-Native (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/03-cloudnative-formats.html](https://noc-oi.github.io/cloud-native-geoscience-course/03-cloudnative-formats.html)
Capítulo 3 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Explicar o que torna um formato "cloud-native", por que formatos tradicionais baseados em arquivo nem sempre são adequados ao armazenamento em nuvem, apresentar as principais abordagens cloud-native/cloud-optimized usadas em ciências da Terra (Zarr, Kerchunk, VirtualiZarr, COG, GeoParquet, FlatGeobuf) e mostrar como esses formatos mudam a forma de trabalhar com dados ambientais.

## "Não vamos mais baixar o arquivo inteiro toda vez"

Os dados ambientais crescem rapidamente em tamanho e complexidade, e a abordagem tradicional de baixar arquivos completos está cada vez mais impraticável, especialmente quando o usuário precisa apenas de um subconjunto dos dados.

Formatos cloud-native e cloud-optimized buscam permitir acesso direto apenas às partes do dataset realmente necessárias, sem exigir o download completo do arquivo primeiro — algo essencial em oceanografia, clima e meteorologia, onde os datasets costumam ser grandes, multidimensionais e compartilhados por muitos usuários.

### De arquivos para objetos em nuvem

Formatos científicos tradicionais como NetCDF, GRIB e HDF5 foram projetados principalmente para sistemas de armazenamento baseados em arquivo (discos locais, servidores compartilhados, sistemas de arquivo de HPC), seguindo o fluxo "baixar o arquivo → abrir o arquivo → analisar o arquivo".

O armazenamento em nuvem funciona diferente: em vez de um arquivo grande em um sistema de arquivos, os dados costumam ser guardados como muitos objetos independentes, acessados via HTTP ou APIs no estilo S3. Nesse contexto, o desempenho depende não só de como os dados são codificados, mas também de quantas requisições são necessárias, onde os metadados residem e se pequenos subconjuntos podem ser obtidos de forma eficiente.

### O que torna um formato cloud-native?

Segundo o *Cloud-Native Geospatial Formats Guide*, formatos cloud-optimized seguem um padrão comum:

- Os metadados fornecem endereços dos blocos de dados.
- Os metadados são armazenados em formato e local consistentes.
- Todos os metadados podem ser carregados com poucas leituras (idealmente uma só).
- Bibliotecas podem usar esses metadados para ler apenas o subconjunto de dados necessário.

Para dados ambientais multidimensionais, isso geralmente significa: arrays organizados em chunks, acesso leve a metadados, e layouts que funcionam bem com object storage (em vez de assumir um sistema de arquivos POSIX). O objetivo não é mudar o significado dos dados, mas sim a eficiência com que podem ser descobertos, acessados e processados.

> **Atenção:** cloud-native não é sinônimo de "estar armazenado na nuvem". Colocar arquivos NetCDF ou HDF5 dentro de um bucket na nuvem **não** os torna automaticamente cloud-native. Um formato ou layout só é cloud-native/cloud-optimized quando suporta acesso remoto eficiente a metadados e subconjuntos, em vez de tratar o armazenamento em nuvem como se fosse apenas mais um disco.

## Principais formatos e abordagens em ciências da Terra

Não existe uma solução cloud-native única para todos os dados ambientais — o guia da comunidade destaca explicitamente que não há uma abordagem "tamanho único". Em vez disso, várias abordagens complementares são usadas:

- **[Zarr](https://zarr.dev/)** — formato para arrays N-dimensionais fragmentados (chunked), armazenados como objetos chave-valor; muito usado em dados climáticos e de observação da Terra.
- **[Kerchunk](https://fsspec.github.io/kerchunk/)** — biblioteca Python que cria arquivos de referência descrevendo como ler dados NetCDF/HDF5/GRIB existentes *como se fossem* um repositório Zarr, sem reescrever os dados originais.
- **[VirtualiZarr](https://virtualizarr.readthedocs.io/)** — projeto para criar repositórios Zarr "virtuais" e cloud-optimized a partir de dados científicos existentes, expondo dados não-Zarr através de uma interface tipo Zarr.
- **[Cloud-Optimized GeoTIFF (COG)](https://www.cogeo.org/)** — formato para dados raster geoespaciais que permite acesso eficiente a subconjuntos de imagens grandes via HTTP ou object storage, usando *tiling* interno e metadados.
- **[GeoParquet](https://www.geoparquet.org/)** — formato colunar amigável à nuvem para dados vetoriais geoespaciais, construído sobre o Apache Parquet.
- **[FlatGeobuf](https://flatgeobuf.org/)** — formato binário de dados vetoriais geoespaciais projetado para streaming eficiente e acesso espacialmente indexado, inclusive via requisições HTTP range.

Na prática, essas abordagens atendem a necessidades diferentes: alguns fluxos reescrevem os dados em um novo layout cloud-native (como o Zarr), enquanto outros mantêm os arquivos legados e os expõem por meio de referências para acesso amigável à nuvem.

## Por que não depender apenas de formatos tradicionais?

Formatos tradicionais continuam essenciais nas ciências da Terra e não vão desaparecer. Porém, grandes coleções de arquivos NetCDF, HDF5 ou GRIB podem ser incômodas em ambientes de nuvem porque:

- Os metadados podem estar embutidos dentro de muitos arquivos separados.
- Os padrões de acesso podem gerar muitas leituras remotas.
- Os fluxos de trabalho ainda costumam assumir que os arquivos serão baixados ou montados antes da análise.

As abordagens cloud-native tentam reduzir esses problemas tornando os metadados mais acessíveis, permitindo leituras mais seletivas e suportando acesso compartilhado a partir de object storage central — especialmente útil quando muitos usuários querem pequenos subconjuntos de arquivos muito grandes (ex.: série temporal em um ponto, uma variável sobre uma região, um recorte de uma saída de modelo global).

## Como isso muda os fluxos de trabalho

Com abordagens cloud-native, o fluxo de trabalho pode passar de "baixar primeiro, analisar depois" para "abrir remotamente, inspecionar metadados e ler apenas os chunks necessários". Isso reduz tempo de espera, cópias locais duplicadas e volume de dados transferido pela rede.

Também viabiliza análises compartilhadas mais escaláveis: os dados permanecem em um armazenamento central enquanto vários usuários, notebooks ou jobs de processamento acessam partes diferentes ao mesmo tempo. Para este curso, o próximo passo mais importante é o **Zarr**, por oferecer um exemplo concreto de como organizar dados ambientais multidimensionais fragmentados para esse tipo de acesso.

## Como formatos cloud-native mudam a interação com os dados

- **Acesso direto e seletivo na nuvem**: usuários podem abrir datasets diretamente via HTTPS ou S3 sem download prévio, lendo apenas os chunks necessários para um cálculo ou visualização.
- **Cubos de dados prontos para análise**: arquivos podem ser reestruturados em grandes cubos de dados coerentes (ex.: campos climáticos globais em Zarr com convenções CF), mais fáceis de consultar e recortar por espaço, tempo e variável.
- **Separação entre armazenamento e computação**: o processamento roda em ambientes de nuvem escaláveis (clusters Kubernetes, plataformas serverless) enquanto os dados ficam no object storage, reduzindo a movimentação de dados e permitindo acesso compartilhado.

Isso significa que fluxos de trabalho em oceanografia e meteorologia podem passar de "baixar arquivos, gerenciar discos locais, rodar scripts" para "abrir datasets na nuvem, recortar interativamente e rodar análises sem mover arquivos inteiros". Também viabiliza novos serviços: exploradores web, notebooks interativos e pipelines de processamento escaláveis que operam diretamente sobre repositórios cloud-native — como em tutoriais que usam dados ERA5 em Zarr junto com metadados STAC.

## Exercícios propostos na lição (resumo do raciocínio)

- **Pensando em oportunidades cloud-native**: refletir sobre como você acessa hoje um dataset (download, montagem de armazenamento compartilhado, serviço de consulta), se normalmente precisa do dataset inteiro ou só de um subconjunto, e como a inspeção rápida de metadados + leitura seletiva mudaria essa tarefa.
- **Pensando em chunks**: para diferentes tarefas sobre um dataset global de temperatura da superfície do mar em Zarr (mapa de um dia, série temporal de 10 anos em um ponto, média regional de um mês), discutir quais partes do dataset seriam lidas em cada caso — cada tarefa se beneficia de um layout de chunk diferente, o que torna a escolha da estratégia de chunking uma parte importante do trabalho com Zarr.

## Pontos-chave (resumo final da lição)

1. Formatos cloud-native são projetados para acesso eficiente via object storage e protocolos web, não apenas para sistemas de arquivos locais.
2. Um layout cloud-native geralmente combina metadados leves com chunks endereçáveis, para que as ferramentas leiam apenas os dados necessários.
3. Simplesmente armazenar arquivos NetCDF ou HDF5 na nuvem não os torna cloud-native automaticamente.
4. Nas ciências da Terra, abordagens comuns incluem Zarr, layouts cloud-optimized de NetCDF/HDF5, Kerchunk, VirtualiZarr, GeoParquet e FlatGeobuf.
5. Abordagens cloud-native podem reduzir a movimentação de dados, melhorar o compartilhamento e viabilizar análises escaláveis de grandes datasets ambientais.

---
*Este é o Capítulo 3 de um curso de 16 capítulos. O próximo capítulo aborda o Modelo de Dados Zarr e o Armazenamento em Chunks.*
