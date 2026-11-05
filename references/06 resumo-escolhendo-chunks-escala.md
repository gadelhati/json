# Resumo: Escolhendo Chunks em Escala (Cloud-Native Geoscience Course)

**Fonte:** [noc-oi.github.io/cloud-native-geoscience-course/06-chunks.html](https://noc-oi.github.io/cloud-native-geoscience-course/06-chunks.html)
Capítulo 6 do curso "Cloud-Native Geoscience Data Workflows".

## Objetivo do capítulo

Entender o que é um chunk e por que seu formato afeta o desempenho, como escolher tamanhos de chunk para diferentes tipos de análise, os trade-offs entre chunks grandes e pequenos, como fazer *rechunking* de um dataset Zarr, e o que é *sharding* e como ele reduz a sobrecarga de armazenar/acessar muitos chunks pequenos.

## O que são chunks?

No Zarr (e em muitos sistemas baseados em arrays), um **chunk** é um pequeno bloco N-dimensional de um array, armazenado e acessado como uma unidade. Em vez de guardar um array gigante em um único arquivo/objeto:

- O array é dividido em chunks (ex.: `(time, lat, lon) = (10, 100, 100)` por chunk).
- Cada chunk é armazenado separadamente (ex.: como um objeto separado em um diretório ou bucket).
- Os dados são lidos e escritos chunk a chunk, conforme necessário.

Os chunks influenciam:

- **Padrões de I/O**: quais partes do dataset são lidas do armazenamento.
- **Paralelismo**: como o trabalho pode ser distribuído entre processos ou threads.
- **Eficácia da compressão**: quão bem os dados comprimem dentro de cada chunk.
- **Sobrecarga de metadados**: número de chunks e o gerenciamento associado.

Escolher bons formatos de chunk é crítico ao passar de datasets "de brinquedo" para dados de reanálise em larga escala, ensembles ou modelos de alta resolução.

### Pensando em dimensões e cargas de trabalho

Para escolher o formato dos chunks, é preciso partir das dimensões e das cargas de trabalho (workloads) típicas.

Dimensões comuns em oceano, clima e meteorologia: `time`; `lat`/`lon` (ou `x`/`y`); `level`/`depth` (níveis de pressão/modelo, profundidade no oceano); `member` (membro de ensemble).

Cargas de trabalho comuns e o layout de chunk que as favorece:

- **Série temporal em um ponto** (ex.: temperatura em um local ao longo de anos) → chunks que incluam muitos passos de tempo para uma pequena região espacial.
- **Médias espaciais por passo de tempo** (ex.: temperatura média global ao longo do tempo) → chunks que incluam fatias espaciais completas (ou grandes blocos espaciais) para poucos passos de tempo.
- **Subconjuntos regionais** (ex.: dados de uma bacia específica) → depende do alinhamento espacial dos chunks.
- **Perfis verticais** (ex.: temperatura vs. profundidade em um ponto e horário) → chunks alinhados na dimensão vertical.
- **Estatísticas de ensemble** (ex.: média e dispersão entre membros) → chunks que incluam vários membros juntos, se eles costumam ser usados em conjunto.
- **Visualização web/em nuvem**: chunks menores e alinhados espacialmente, geralmente em torno de 256×256 ou 512×512 pixels (~100–1000 KB), para que os "tiles" de mapa sejam lidos eficientemente e só a região necessária seja transferida.
- **Análise HPC em larga escala**: chunks maiores, que reduzem a sobrecarga do agendador e funcionam bem com processamento paralelo, mas ainda cabem confortavelmente na memória — uma regra prática é manter os chunks na faixa de 10–100 MB.

Não existe um único "melhor" esquema de chunking: depende de quais cargas de trabalho são mais importantes para os usuários do dataset.

## Inspecionando o formato dos chunks em um repositório Zarr

A lição usa um subconjunto do dataset de reanálise oceânica **GLORYS12V1** (produto CMEMS de reanálise global do oceano com resolução de 1/12° e 50 níveis verticais, cobrindo o período de altimetria desde 1993).

Exemplo de inspeção da variável `zos` (altura da superfície do mar):

```python
import xarray as xr
ds = xr.open_zarr("data/glorys/glorys_202605.zarr")

zos = ds["zos"]
print("Dimensions:", zos.dims)
print("Shape:", zos.shape)
print("Chunks:", zos.data.chunks)
```

No exercício da lição, ao inspecionar a variável `so` (salinidade), com dimensões `(time, depth, latitude, longitude)`, o chunking atual armazena um passo de tempo e um nível de profundidade com toda a grade horizontal global em cada chunk. Isso é:

- **Favorável** para operações que precisam do campo espacial completo em um dado instante (ex.: calcular uma média global).
- **Desfavorável** para série temporal em um ponto, perfil vertical em um ponto ou subconjunto regional — em todos esses casos seria preciso ler muitos chunks grandes para obter uma pequena quantidade de dados, já que latitude e longitude não são fragmentadas.

Isso ilustra que o chunking é sempre um trade-off: um layout bom para operações espaciais globais pode ser ineficiente para análises pontuais, regionais ou de perfil vertical.

### Trade-offs: chunks pequenos vs. grandes

- **Tamanho do chunk em bytes**: geralmente um alvo de poucos MB por chunk (ex.: 1–100 MB), dependendo do ambiente de armazenamento e computação.
  - Pequeno demais: muitas leituras minúsculas e grande sobrecarga de metadados.
  - Grande demais: leituras lentas e paralelismo ruim, especialmente em redes.
- **Formato do chunk nas dimensões**:
  - Alinhar os chunks com os padrões de acesso comuns (ex.: contíguo no tempo para séries temporais, ou contíguo no espaço para estatísticas espaciais).
  - Evitar fragmentar dimensões raramente usadas (ex.: `member` ou `level`), a menos que sejam processadas com frequência.

## Rechunking

*Rechunking* significa mudar a forma como um dataset é dividido em chunks — necessário porque o melhor layout de chunk depende do uso: um layout pode ser melhor para ler séries temporais, outro melhor para ler mapas ou para escrever em armazenamento cloud-optimized.

Com o xarray, o rechunking é simples, mas pode ser caro para datasets grandes. Passos básicos:

1. **Abrir o dataset original** (ex.: `xr.open_zarr(...)`) e inspecionar seu `shape` e `chunks` atuais.
2. **Escolher um novo layout de chunk**, ex.: `ds.chunk({"valid_time": 20, "latitude": 180, "longitude": 180})`.
3. **Verificar o novo chunking** inspecionando o dataset rechunkado.
4. **Escrever os dados rechunkados em um novo repositório Zarr**, atualizando também a codificação (`encoding`) da variável para refletir o novo chunking:

```python
ds_chunked.to_zarr(
    "data/era5_sst/ocean_temperature_rechunked.zarr",
    mode="w",
    encoding={"sst": {"chunks": (20, 180, 180)}},
)
```

Essa abordagem é conveniente, mas nem sempre eficiente para datasets muito grandes: se os layouts original e de destino forem muito diferentes, o rechunking pode exigir armazenamento e memória temporários substanciais, além de criar um novo repositório Zarr (custo adicional de armazenamento).

### Rechunker e Cubed
- **[Rechunker](https://rechunker.readthedocs.io/)** — biblioteca dedicada a rechunking eficiente de grandes datasets de array sem carregar tudo na memória de uma vez; porém não funciona com repositórios Zarr v3.
- **[Cubed](https://cubed-dev.github.io/cubed/)** — biblioteca mais recente que fornece uma API de array para rechunking e outras operações, projetada para funcionar com backends serverless ou localmente, sem precisar de um agendador Dask ativo; pode ser integrada ao xarray (`chunked_array_type="cubed"`).

## O rechunking pode ser caro

O rechunking pode levar muito tempo, especialmente se os layouts original e de destino forem muito diferentes. Um estudo citado na lição mediu o tempo para rechunkar um dataset de 9–10 GB com diferentes estratégias de chunking:

| Estratégia de chunking | Tempo de rechunking |
|---|---|
| Chunks grandes | ~6,66 min |
| Compromisso recomendado (melhor padrão geral de acesso) | ~22,44 min |
| Chunks muito pequenos | ~46 h |

Isso demonstra que o chunking não é apenas um detalhe de armazenamento — pode ter impacto real no custo computacional, especialmente ao operar em escala com grandes datasets climáticos ou oceânicos na nuvem.

## Sharding: agrupando chunks

*Sharding* é uma forma de manter os benefícios lógicos de chunks pequenos, reduzindo o custo físico de armazenar um número excessivo de objetos minúsculos.

- **Chunks** controlam a unidade de computação e acesso aos dados.
- **Shards** controlam quantos chunks são agrupados em cada objeto de armazenamento.

Uma analogia útil: pense nos chunks como páginas individuais e no shard como uma pasta que reúne várias páginas — ainda lemos a página que precisamos, mas não é necessário armazenar cada página como um arquivo separado. Isso é especialmente útil em object storage na nuvem, onde milhões de objetos muito pequenos podem ser difíceis de gerenciar.

### Benefícios
- Chunks pequenos para leituras rápidas e seletivas.
- Redução do número de objetos no armazenamento em nuvem.
- Redução da sobrecarga do sistema de arquivos causada por um número muito grande de arquivos.
- Mantém os benefícios da análise baseada em chunks sem pagar o custo total de armazenar cada chunk separadamente.

### Trade-offs
Se a carga de trabalho normalmente lê apenas uma pequena parte de um shard, mais dados do que o necessário podem ser transferidos. O sharding também torna escritas parciais mais complicadas, pois atualizar um chunk pode exigir reescrever parte de um shard. Por isso, o layout do shard deve refletir o uso real dos dados (ex.: agrupar chunks espaciais vizinhos se os usuários costumam ler regiões de mapa juntas, ou agrupar ao longo do tempo se leem séries temporais).

### Exemplo de sharding no Zarr v3

O Zarr Python v3 oferece suporte direto a arrays fragmentados (*sharded*) na criação do array. Exemplo: criar um array Zarr com chunks de 10×10, mas armazená-los em shards de 100×100:

```python
ds.to_zarr(
    "data/example_sharded.zarr",
    mode="w",
    zarr_format=3,
    encoding={"temperature": {"chunks": (10, 10), "shards": (100, 100)}},
)
```

Ao reabrir o array, os chunks continuam aparecendo como `(10, 10)`, mas o armazenamento subjacente é agrupado em shards maiores. No metadado `zarr.json`, o campo `chunk_grid.configuration.chunk_shape` na verdade reflete o formato do shard, enquanto o codec `"sharding_indexed"` traz, em sua configuração, o tamanho real do sub-chunk dentro de cada shard.

### xarray com Zarr fragmentado (sharded)

O xarray abre um repositório Zarr com sharding da mesma forma que abre qualquer outro dataset Zarr — do ponto de vista de quem analisa os dados, o sharding é majoritariamente um detalhe de armazenamento, sem afetar o uso de dimensões rotuladas e operações de alto nível.

## Exercícios propostos na lição (resumo do raciocínio)

- **Relacionar o chunking atual às cargas de trabalho**: inspecionar `shape`/`chunks` de uma variável (ex.: salinidade do GLORYS12V1) e avaliar se o layout atual é "amigável" ou "desfavorável" para série temporal em um ponto, média espacial por passo de tempo, subconjunto regional e perfil vertical.
- **Desenhar um novo esquema de chunking**: identificar a carga de trabalho prioritária para um dataset, propor um esquema de chunk adequado e estimar seu tamanho aproximado em bytes (usando `numpy` para multiplicar o formato do chunk pelo tamanho do tipo de dado).
- **Rechunkar e comparar**: implementar um esquema de rechunking, salvar em um novo repositório Zarr, e medir/comparar o tempo de cálculo de uma média global e de uma média regional entre o repositório original e o rechunkado (usando `time.time()` ou `%%time`).
- **Fragmentar (sharding) o dataset**: aplicar um esquema de shard sobre um dataset já rechunkado (usando `align_chunks=True` ao salvar), verificar os metadados e comparar o número de arquivos/objetos entre os repositórios original, rechunkado e fragmentado — o dataset fragmentado deve ter menos arquivos, mantendo os benefícios do acesso em chunks.

> **Atenção**: chunking e sharding não são a mesma coisa. Chunking responde "qual é a unidade de computação e acesso?"; sharding responde "como esses chunks são fisicamente empacotados em objetos de armazenamento?". Um dataset pode usar chunks pequenos para análise flexível, mas armazená-los dentro de shards maiores para tornar o armazenamento em nuvem mais eficiente.

## Pontos-chave (resumo final da lição)

1. Chunks são blocos N-dimensionais que controlam como os dados são armazenados e acessados no Zarr.
2. O formato dos chunks deve ser escolhido com base nas cargas de trabalho dominantes (série temporal, médias espaciais, ensembles) e em restrições práticas como o tamanho do chunk em bytes.
3. O rechunking pode reorganizar um dataset para atender melhor às necessidades de desempenho, ao custo de uma etapa inicial de reescrita.
4. Ferramentas como zarr e xarray permitem inspecionar layouts de chunk, desenhar novos esquemas e salvar repositórios Zarr rechunkados para análise em escala.
5. O sharding é uma técnica que agrupa múltiplos chunks em objetos de armazenamento maiores, reduzindo a sobrecarga e mantendo os benefícios do acesso fragmentado.

---
*Este é o Capítulo 6 de um curso de 16 capítulos. O próximo capítulo aborda Processamento Paralelo com Zarr.*
