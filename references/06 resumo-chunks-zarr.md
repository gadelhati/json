# Resumo: Choosing Chunks at Scale (Cloud-Native Geoscience Course)

Fonte: [06-chunks.html](https://noc-oi.github.io/cloud-native-geoscience-course/06-chunks.html) — Capítulo 6 do curso *Cloud-Native Geoscience Data Workflows*.

## Objetivo do capítulo

Explicar o que são "chunks" (blocos) em dados armazenados no formato Zarr, como escolher o tamanho/formato ideal de acordo com o tipo de análise, como fazer "rechunking" (reorganização dos blocos) e o que é "sharding" (agrupamento de chunks em arquivos maiores).

## 1. O que são chunks?

Um **chunk** é um bloco N-dimensional de um array que é armazenado e acessado como uma unidade. Em vez de guardar um array gigante em um único arquivo, o Zarr:

- Divide o array em blocos (ex.: `(time, lat, lon) = (10, 100, 100)` por chunk);
- Armazena cada chunk separadamente (como um objeto em um bucket/diretório);
- Lê e escreve os dados chunk por chunk, sob demanda.

Os chunks afetam diretamente:
- **Padrões de I/O** (quais partes do dado são lidas);
- **Paralelismo** (como o trabalho é distribuído entre processos);
- **Eficiência de compressão**;
- **Overhead de metadados** (número de chunks a gerenciar).

## 2. Pensando em dimensões e workloads

Dimensões comuns em dados oceânicos/climáticos: `time`, `lat`/`lon`, `level`/`depth`, `member` (membro de ensemble).

Tipos de workload e o chunking recomendado para cada um:

| Workload | Chunking recomendado |
|---|---|
| Série temporal em um ponto | Muitos passos de tempo, região espacial pequena |
| Média espacial por passo de tempo | Fatias espaciais completas, poucos passos de tempo |
| Estatísticas de ensemble | Múltiplos membros juntos |
| Visualização web/mapas | Chunks pequenos e alinhados espacialmente (~256×256 ou 512×512 px, 100–1000 KB) |
| Análise HPC em larga escala | Chunks maiores (10–100 MB), reduzindo overhead do scheduler |

**Não existe um chunking "ideal" universal** — depende do workload prioritário dos usuários.

## 3. Inspecionando chunks em um Zarr store

O capítulo usa o exemplo do dataset **GLORYS12V1** (reanálise oceânica) e mostra como inspecionar dimensões, formato (shape) e chunks com `xarray`:

```python
import xarray as xr
ds = xr.open_zarr("data/glorys/glorys_202605.zarr")
zos = ds["zos"]
print(zos.dims, zos.shape, zos.data.chunks)
```

No exercício apresentado, o chunking original (um passo de tempo + um nível de profundidade + grade espacial completa) é:
- ✅ Bom para operações espaciais globais (médias globais);
- ❌ Ruim para séries temporais em um ponto, perfis verticais e recortes regionais, pois exige ler muitos chunks grandes para obter pouca informação.

### Boas práticas gerais (trade-offs)

- **Tamanho em bytes**: geralmente entre 1–100 MB por chunk.
  - Muito pequeno → excesso de leituras e overhead de metadados;
  - Muito grande → leituras lentas e baixo paralelismo.
- **Formato dimensional**: alinhar os chunks com o padrão de acesso mais comum (ex.: contíguo no tempo para séries temporais) e evitar "fatiar" dimensões pouco usadas (como `member` ou `level`).

## 4. Rechunking (reorganização de chunks)

**Rechunking** é o processo de mudar a forma como o dataset é dividido em chunks, pois o melhor layout depende do uso pretendido.

Passos com `xarray`:
1. Abrir o dataset original;
2. Definir o novo esquema de chunks, ex.: `ds.chunk({"valid_time": 20, "latitude": 180, "longitude": 180})`;
3. Verificar o novo chunking;
4. Salvar em um novo Zarr store, atualizando também o `encoding`.

⚠️ Rechunking pode ser **caro** em tempo e memória/armazenamento temporário, especialmente se o layout original e o de destino forem muito diferentes.

### Ferramentas alternativas
- **Rechunker**: biblioteca dedicada a rechunking eficiente sem carregar tudo na memória (não funciona com Zarr v3).
- **Cubed**: biblioteca mais recente com API de array, funciona sem um scheduler Dask ativo e é compatível com backends serverless.

### Custo do rechunking (exemplo real)

Um estudo citado no capítulo mediu o tempo de rechunking de um dataset de 9–10 GB em object storage na nuvem:

| Estratégia | Tempo de rechunking |
|---|---|
| Chunks grandes | ~6,66 min |
| Compromisso recomendado | ~22,44 min |
| Chunks muito pequenos | ~46 horas |

Isso mostra o quanto a escolha errada de chunking pode impactar drasticamente o desempenho.

## 5. Sharding: agrupando chunks

**Sharding** é uma técnica que mantém os benefícios lógicos de chunks pequenos, mas reduz o custo físico de armazenar milhões de objetos pequenos.

- **Chunks** controlam a unidade de computação/acesso;
- **Shards** controlam quantos chunks são agrupados em cada objeto de armazenamento físico.

Analogia usada no texto: chunks são como páginas individuais, e um shard é como um fichário que agrupa várias páginas — você ainda lê a página que precisa, mas não precisa armazená-la como um arquivo separado.

### Benefícios
- Reduz o número de objetos no armazenamento em nuvem;
- Mantém chunks pequenos para leituras seletivas rápidas;
- Reduz overhead de sistema de arquivos.

### Trade-offs
- Se o workload lê apenas uma pequena parte de um shard, pode transferir dados desnecessários;
- Escritas parciais ficam mais complicadas (atualizar um chunk pode exigir reescrever parte do shard).

### Exemplo prático (Zarr v3)

```python
ds.to_zarr(
    "data/example_sharded.zarr",
    mode="w",
    zarr_format=3,
    encoding={"temperature": {"chunks": (10, 10), "shards": (100, 100)}},
)
```

Aqui, os dados são divididos em chunks pequenos de `10×10` para acesso granular, mas armazenados fisicamente em shards de `100×100`.

No metadado Zarr (`zarr.json`), dois campos são importantes:
- `chunk_grid.configuration.chunk_shape`: na verdade representa o **shard**;
- `codecs` → entrada `"sharding_indexed"`: contém o **chunk real** dentro do shard.

O `xarray` consegue abrir stores com sharding normalmente — a técnica é transparente para quem está analisando os dados.

## 6. Diferença entre Chunking e Sharding

| | Pergunta que responde |
|---|---|
| **Chunking** | Qual é a unidade de computação e acesso? |
| **Sharding** | Como esses chunks são fisicamente empacotados no armazenamento? |

Um dataset pode usar chunks pequenos para análise flexível, mas agrupá-los em shards maiores para tornar o armazenamento em nuvem mais eficiente.

## Pontos-chave (Key Points)

- Chunks são blocos N-dimensionais que controlam como os dados são armazenados e acessados no Zarr.
- O formato dos chunks deve ser escolhido com base nos workloads dominantes (séries temporais, médias espaciais, ensembles) e em restrições práticas de tamanho em bytes.
- Rechunking pode reorganizar um dataset para melhor atender necessidades de performance, ao custo de uma reescrita inicial.
- Ferramentas como `zarr` e `xarray` permitem inspecionar layouts de chunks, projetar novos esquemas e salvar stores rechunked para análise em escala.
- Sharding agrupa múltiplos chunks em objetos de armazenamento maiores, reduzindo overhead e mantendo os benefícios do acesso baseado em chunks.

---
*Este resumo cobre o Capítulo 6 do curso [Cloud-Native Geoscience Data Workflows](https://noc-oi.github.io/cloud-native-geoscience-course/), que também inclui exercícios práticos com os datasets GLORYS12V1 e ERA5 (não reproduzidos integralmente aqui).*
