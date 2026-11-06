# AGENTS.md

Editor web de arquivos JSON/GeoJSON (CRUD, mapa e exportação) com suporte a metadados de GeoTIFF. Construído com FastAPI + Jinja2.

## Comandos

```
python -m venv .venv
.venv/Scripts/activate
pip install --upgrade -r requirements.txt
uvicorn app.app:app --reload
```

## Estrutura

- `app/` — backend (FastAPI)
- `app/templates/` — páginas Jinja2 (todas estendem `base.html`)
- `app/static/` — JS/CSS (`dashboard.js`, `geometry.js`, `geotiff.js`, `map.js`, `style.css`) e prévias de GeoTIFF
- `app/data/uploads`, `app/data/exports` — arquivos enviados/exportados
- `docs/` — documentação operacional organizada por arquitetura, desenvolvimento, guias e histórico; consulte `docs/README.md`.
- `references/` — resumos de estudo; `references/exercices/` — exercícios NumPy/pandas/xarray (fora da aplicação)

## Módulos em `app/`

- `app.py` — inicializa o FastAPI, configura recursos estáticos e registra as rotas.
- `config.py` — configurações da aplicação (`Settings`, pydantic-settings); sobrescrevíveis por variáveis de ambiente ou `.env`; prepara os diretórios de trabalho.
- `routers/crud.py` — **rotas integradas** para importar, editar, exibir e exportar JSON/GeoJSON/GeoTIFF:
  - tabela de registros unificada (JSON, GeoJSON e metadados de GeoTIFF), mapa com camadas, formulário de importação integrado;
  - **upload unificado** (`/import`): detecta tipo de arquivo (JSON/GeoJSON/GeoTIFF) e processa com as opções apropriadas:
    - `concatenar=true`: para JSON/GeoJSON, adiciona aos dados existentes (mesmo formato);
    - `substituir_geotiff=true`: para GeoTIFF, remove rasters anteriores;
    - suporta **cross-type**: pode-se misturar JSON com GeoTIFF na mesma sessão.
  - criar, editar, atualizar (com validação) e excluir registros;
  - exportar JSON/GeoJSON (excluindo GeoTIFF)/CSV (incluindo metadados de GeoTIFF);
  - Na tabela, a geometria é exibida resumida como texto curto; registros GeoTIFF aparecem com indicador 🗺️ e link "Mapa".
- `services/crud.py` — `JsonStore` agora gerencia **registros integrados** (JSON, GeoJSON e metadados de GeoTIFF):
  - `load(file_path, mode)` detecta o formato (JSON, GeoJSON) pelo conteúdo; `mode` = `replace` ou `append`.
  - **Novo**: `add_geotiff_metadata(file_id, filename, metadata, bounds_geometry, preview_path)` cria um registro GeoTIFF com metadados extraídos (CRS, resolução, bandas, limites em EPSG:4326).
  - Em GeoJSON, cada registro é uma Feature: as chaves de `properties` viram colunas normais e a geometria fica isolada em `GEOMETRY_FIELD`.
  - Registros GeoTIFF marcam-se com `_source_type="geotiff"` e incluem `_geotiff_id` e `_geotiff_preview`.
  - `columns()` lista as colunas normais; `feature_collections_by_layer()` **agora agrupa e inclui camadas GeoTIFF como limites (Polygon)**; `has_multiple_sources()` indica concatenação.
  - `get_all`, `get`, `prepare_incoming` (converte dados brutos do formulário), `create` (gera id e marca tipo), `update` (retorna `None` se não existir), `delete` (retorna bool).
  - `export()` aplica as edições; em GeoJSON reconstrói uma FeatureCollection válida (geometrias de JSON + limites de GeoTIFF), senão exporta lista de objetos. Usa nome genérico (`export.geojson`/`export.json`) quando há várias fontes.
- `geotiff.py` (em `services/`) — processa e armazena GeoTIFFs com UUID: extrai metadados (CRS, transformação, limites, resolução, pontos de controle, bandas com estatísticas/tags GDAL/TIFF); reprojeta para EPSG:4326 e gera uma prévia PNG no caminho público `/static/previews/`, preservando a paleta de rasters indexados, com limites para Leaflet e polígono GeoJSON. Remove `PROJ_DATA` do ambiente na importação. Exporta para `app.services.crud.JsonStore` via `add_geotiff_metadata()`.
- `geotiff.py` — **rota de upload legada** `/geotiff/upload` (mantida para compatibilidade) e consulta de metadados `/geotiff/{file_id}/metadata`; agora integrada à rota unificada `/import`.

## Templates

- `base.html` — layout comum; define os blocos `content` e `scripts`.
- `datatable.html` — **tabela integrada** de registros (JSON, GeoJSON e metadados de GeoTIFF) com CRUD e exportação; indicador visual de tipo (📄 JSON, 🔷 GeoJSON com geometria, 🗺️ GeoTIFF); ações contextuais (Editar/Mapa, Excluir).
- `form.html` — criação/edição de registro.
- `map.html` — mapa Leaflet com as camadas GeoJSON.
- `upload.html` — **formulário integrado** para importar JSON, GeoJSON ou GeoTIFF com opções de concatenação (JSON/GeoJSON) e substituição (GeoTIFF).

## Convenções

- Docstrings e comentários em português; uma docstring curta por módulo, classe e função.
- Novas páginas estendem `base.html` e usam os blocos `content`/`scripts`.
- Os dados vivem apenas em memória (`store`); reiniciar o servidor os descarta.
- Ao alterar comportamento, atualize a docstring correspondente e este arquivo.
