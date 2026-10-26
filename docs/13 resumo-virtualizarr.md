# Resumo: Virtual Zarr com Virtualizarr

**Fonte:** [Cloud-Native Geoscience Data Workflows – Capítulo 13: Virtual Zarr with Virtualizarr](https://noc-oi.github.io/cloud-native-geoscience-course/13-virtualizarr.html)

Este capítulo faz parte de um curso sobre workflows de dados geocientíficos "cloud-native" e explica como usar a biblioteca **Virtualizarr** para acessar arquivos NetCDF como se fossem um repositório Zarr, sem precisar copiar ou reescrever os dados originais.

## Objetivos da aula

- Explicar o que é um "virtual Zarr store".
- Criar um dataset virtual a partir de arquivos NetCDF locais.
- Abrir o dataset virtual com xarray e inspecionar sua estrutura.
- Comparar o acesso virtual com o acesso direto a NetCDF.

## Por que usar um virtual Zarr store?

Converter todo um arquivo de dados NetCDF para o formato Zarr físico nem sempre é prático: pode exigir muito tempo e espaço de armazenamento, e algumas instituições precisam manter os arquivos NetCDF originais por razões legais ou operacionais.

O **Virtualizarr** resolve isso criando um dataset virtual que **aponta de volta** para os arquivos NetCDF originais, em vez de escrever novos chunks Zarr. Do ponto de vista do usuário, o resultado se comporta como um dataset xarray normal, mas os dados continuam armazenados nos arquivos NetCDF de origem.

### Quando usar Virtualizarr em vez de conversão física

Cenários comuns:
- Grandes arquivos de NetCDF/GRIB onde se quer acesso rápido e "chunked" via xarray/Dask, sem reescrever tudo.
- Necessidade de manter os arquivos originais intactos (motivos regulatórios, legado, operacionais).
- Sistemas de armazenamento que sofrem com um número muito grande de arquivos pequenos (problema comum em Zarr físico).
- Prototipagem de acesso otimizado para nuvem antes de migrar de fato.

Por outro lado, a conversão física para Zarr ainda é preferível quando se espera uso intenso e se quer máxima performance, ou quando é necessário reestruturar o layout dos dados.

## Fluxo de trabalho do Virtualizarr

O exemplo prático usa um subconjunto do dataset **ERA5 Reanalysis** (altura significativa de onda), com um arquivo NetCDF por dia.

### Passo 1 — Inspecionar os arquivos NetCDF
Usa `xarray.open_mfdataset` para abrir múltiplos arquivos `.nc` e checar dimensões, variáveis e coordenadas.

### Passo 2 — Criar o dataset virtual
1. Importa `obstore` (interface para armazenamento de objetos, incluindo sistema de arquivos local), `virtualizarr` e o `HDFParser` (necessário porque NetCDF é baseado em HDF5).
2. Coleta os caminhos dos arquivos e cria URLs no formato `file://...`.
3. Cria um `LocalStore` e um `ObjectStoreRegistry` para indicar onde os arquivos estão.
4. Usa `open_virtual_mfdataset(urls, parser, registry, combine="nested", concat_dim="time")` para gerar o dataset virtual (`vds`), que **não copia os dados**, apenas cria referências virtuais.

### Passo 3 — Criar um repositório Icechunk local
Um dos benefícios de datasets virtuais é poder salvá-los em um repositório **Icechunk**, criando um "snapshot" versionado. Isso requer configurar um `VirtualChunkContainer` apontando para o diretório local dos NetCDFs originais.

### Passo 4 — Escrever o dataset virtual no Icechunk
Usa `vds.vz.to_icechunk(session.store)` seguido de `session.commit(...)` para gravar e versionar o snapshot.

### Passo 5 — Reabrir o snapshot
Ao reabrir, é preciso **autorizar o acesso** aos arquivos NetCDF originais (`authorize_virtual_chunk_access`), e então o dataset pode ser lido normalmente com `xr.open_zarr`.

### Comparação de desempenho
O capítulo sugere comparar o tempo de cálculo de uma média espacial usando o NetCDF original vs. o dataset virtual via Icechunk, esperando que o acesso virtual seja mais rápido.

## Por que isso é útil

- Mantém os arquivos originais intocados, mas oferece uma visão "chunked" e amigável à nuvem.
- Combinado com Icechunk, permite versionamento, reprodutibilidade e atualizações incrementais seguras, sem duplicar dados.
- Funciona tanto para arquivos locais quanto para arquivos já armazenados em object storage (S3, GCS, Azure).
- **Ressalva:** o desempenho ainda depende do layout dos arquivos originais; chunks mal alinhados com os dados-fonte podem reduzir a eficiência.

## Tabela comparativa (para um arquivo com 500.000 arquivos NetCDF)

| Formato                | NetCDF4 | Zarr "Nativo" | Kerchunk | Icechunk |
|-------------------------|---------|----------------|----------|----------|
| Nº de URLs              | 500.000 | 1              | 1        | 1        |
| Tempo de abertura       | ~1 ano  | < 1 seg        | < 1 seg  | < 1 seg  |
| Aumento de armazenamento| 0%      | 100%           | 0,0004%  | 0,0004%  |
| Conversível via Xarray? | N/A     | Sim            | Não      | Sim      |
| Versionado?             | Não     | Não            | Não      | Sim      |
| Seguro para atualização?| Não     | Não            | Não      | Sim      |

## Pontos-chave (Key Points)

- O Virtualizarr cria datasets Zarr virtuais sem copiar os dados.
- É útil quando a conversão completa é impraticável ou desnecessária.
- É possível criar um dataset virtual diretamente a partir de arquivos NetCDF já existentes no servidor.
- O xarray pode abrir o dataset virtual e analisá-lo como um dataset comum.
- A virtualização é uma ponte útil entre arquivos NetCDF e workflows no estilo Zarr.

## Aviso importante

O texto alerta que **Virtualizarr e Icechunk ainda estão em rápido desenvolvimento**: a API de abertura/autorização muda a cada versão. Recomenda-se fixar (pin) as versões usadas e documentá-las em qualquer código compartilhado.
