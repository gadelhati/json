o processo de entrada de dados é orientado a dados e não a arquivos. Exportaremos um mesmo conjunto de dados científico em diferentes formatos, respeitando suas limitações.
(GeoTIFF + .aux.xml (opcional) + formulário científico(scientific_metadata.json) → raw.json + refined.json)

- raw.json — registro fiel dos dados e metadados encontrados nas fontes de entrada, independentemente do formato.
- refined.json — representação técnica e científica normalizada, com informações interpretadas, calculadas, transformadas, validadas ou inferidas sobre um raw.json específico.
- scientific_metadata.json — declarações e informações científicas fornecidas pelo responsável pelo conjunto de dados, antes do processamento.

```directory
batimetria.zarr/
│
├── zarr.json
│
├── depth/
│   ├── zarr.json
│   └── c/
│       ├── 0/
│       ├── 1/
│       └── ...
│
└── metadata/
   ├── raw.json
   ├── refined.json
   └── scientific_metadata.json
```

| Formato | Natureza | Tipo de dado / Modelo | Observação arquitetural | O que muda em relação ao GeoTIFF | Ferramenta sugerida |
|---|---|---|---|---|---|
| GeoTIFF | Raster geoespacial | Grade 2D, bandas | Base do fluxo `raw.json` + `refined.json` + `scientific_metadata` | — (referência) | GDAL ou rasterio (cobre tudo) |
| COG | Raster geoespacial otimizado | Grade 2D, bandas | É um GeoTIFF com organização otimizada para acesso remoto (tiling, overviews, ordem dos blocos) | Nada no modelo de dados. Só o layout muda, verificado por validação COG (`cog_validation`) | GDAL ou rasterio (cobre tudo) |
| NetCDF | Contêiner científico | Arrays multidimensionais (variáveis, dimensões, grupos) | Muito utilizado em oceanografia, meteorologia e climatologia; costuma seguir as convenções CF e ACDD, que trazem metadados dentro do arquivo | Não há "bandas". O raw vira uma árvore: dimensões, variáveis (tipo, forma, chunks, compressão, atributos) e atributos globais | `xarray` ou `netCDF4` (GDAL como apoio) |
| HDF5 | Contêiner científico | Grupos, datasets e atributos (multidimensional) | Pode armazenar estruturas heterogêneas. Sem convenção geográfica própria: só ganha significado com um perfil (por exemplo BAG ou IHO S-102 em batimetria, que trazem datum vertical e incerteza) | Não há "bandas". O raw vira uma árvore: grupos, datasets (tipo, forma, chunks, compressão) e atributos | `h5py` (GDAL como apoio) |
| Zarr | Armazenamento multidimensional | Arrays N-dimensionais em chunks, com grupos e atributos | Adequado para processamento distribuído e armazenamento em nuvem. É um diretório ou conjunto de objetos, não um arquivo único | Não há "bandas" nem arquivo único. O raw vira uma árvore: arrays (tipo, forma, chunks, compressão), grupos e atributos | `zarr` ou `xarray` (GDAL como apoio) |
| GRIB | Formato meteorológico | Campos e grades meteorológicas (sequência de mensagens, cada uma um campo) | Especializado em previsão numérica do tempo e modelos atmosféricos | A unidade de leitura é a mensagem (parâmetro, nível, instante, grade), não o arquivo | `ecCodes` (GDAL como apoio: lê, mas cada mensagem vira uma banda e perde chaves da mensagem) |
| BUFR | Formato meteorológico | Observações estruturadas (pontos, perfis, séries) | Utilizado para intercâmbio de observações meteorológicas e ambientais | Não é grade. A leitura depende de tabelas WMO (versão master e local) | `ecCodes` (o GDAL não lê BUFR; confirmar com `gdalinfo --formats`) |
| Shapefile | Vetorial geoespacial | Pontos, linhas e polígonos (vetorial, conjunto de arquivos) | Normalmente composto por vários arquivos associados: `.shp`, `.shx`, `.dbf` e, se houver, `.prj`, `.cpg`, `.shp.xml` | Não há pixel, nodata ou estatística de banda. O raw descreve geometria, atributos e codificação | GDAL/OGR (`pyogrio` ou `fiona`) |
| Parquet / GeoParquet | Colunar tabular / vetorial geoespacial | Tabela colunar com tipos Arrow; no GeoParquet, uma ou mais colunas de geometria | Parquet otimiza armazenamento e consulta analítica; GeoParquet acrescenta metadados `geo` para declarar colunas geométricas, codificação, CRS e limites | Não há pixel nem bandas. O raw descreve esquema Arrow, grupos de linhas, compressão, estatísticas e, no GeoParquet, metadados e colunas geométricas | `pyarrow` (Parquet); `geopandas` ou `pyogrio` (GeoParquet) |

OBS.: Cada formato possui seu próprio mecanismo de leitura (e ferramenta adequada para isso) e produz informações brutas com sua proveniência.

1. Validação estrutural — JSON Schema
JSON Schema
- Tipos, propriedades e campos obrigatórios.
- Enums e padrões.
- Estruturas específicas de TIFF, NetCDF e perfis científicos.
- Compatibilidade de versões.

```directory
/docs/domain/schemas_3_3_0/
├── common.schema.json (Tipos e estruturas compartilhadas)
├── raw.schema.json (TIFF/GeoTIFF, GDAL PAM e NetCDF)
├── refined.schema.json (Dataset normalizado, objetos, variáveis, estatísticas e proveniência)
├── scientific_metadata.schema.json (Declarações científicas genéricas)
├── profiles/
│   └── hydrography/
│       └── bathymetry/ (Estrutura específica da extensão de batimetria)
│           └── 1.0.0/
│               └── profile.schema.json
└── README.md
```

2. Validação de consistência — Validador da aplicação
Lógica própria
- Correspondência entre dataset_id e document_id.
- Integridade dos vínculos entre raw, refined e scientific metadata.
- Resolução de referências internas.
- Compatibilidade entre versões e checksums.
- Propagação dos estados incomplete, provisional e completed.

3. Avaliação científica — Regras do perfil
Perfil científico
- Requisitos de qualidade.
- Coerência das declarações científicas.
- Datum vertical, incerteza e convenção de sinal.
- Condições para publicação.

[Validação estrutural — JSON Schema] para agora e [Validação de consistência — Validador da aplicação] e [Avaliação científica — Regras do perfil] para depois, cada um com sua responsabilidade.
para isso vamos fechar nossos schemas