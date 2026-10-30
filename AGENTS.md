# AGENTS.md

Editor web de arquivos JSON/GeoJSON (CRUD, mapa e exportação) com suporte a metadados de GeoTIFF. Construído com FastAPI + Jinja2.

## Comandos

```
python -m venv .venv
.venv/Scripts/activate
pip install --upgrade -r requirements.txt
uvicorn src.app:app --reload
```

## Estrutura

- `src/` — backend (FastAPI)
- `templates/` — páginas Jinja2 (todas estendem `base.html`)
- `static/` — JS/CSS (`dashboard.js`, `geometry.js`, `geotiff.js`, `map.js`, `style.css`) e prévias de GeoTIFF
- `data/uploads`, `data/exports`, `uploads/geotiff` — arquivos enviados/exportados
- `docs/` — resumos de estudo; `src/exercices/` — exercícios NumPy/pandas/xarray (fora da aplicação)

## Módulos em `src/`

- `app.py` — inicializa o FastAPI, configura recursos estáticos e registra as rotas.
- `config.py` — configurações da aplicação (`Settings`, pydantic-settings); sobrescrevíveis por variáveis de ambiente ou `.env`; prepara os diretórios de trabalho.
- `routes.py` — rotas web para importar, editar, exibir e exportar JSON/GeoJSON:
  - tabela de registros (redireciona para a importação se vazia), mapa com camadas GeoJSON, formulário de importação;
  - upload: salva e carrega o arquivo, substituindo ou concatenando registros;
  - criar, editar, atualizar (com validação) e excluir registros;
  - exportar JSON/GeoJSON para download e CSV.
  - Na tabela, a geometria é exibida resumida como texto curto, não o objeto completo.
- `services.py` — `JsonStore`, armazenamento **em memória** dos registros:
  - `load(file_path, mode)` detecta o formato (JSON ou GeoJSON) pelo conteúdo; `mode` = `replace` ou concatenar.
  - Em GeoJSON, cada registro é uma Feature: as chaves de `properties` viram colunas normais e a geometria fica isolada em `GEOMETRY_FIELD`.
  - `columns()` lista as colunas normais; `feature_collections_by_layer()` agrupa registros com geometria por arquivo de origem; `has_multiple_sources()` indica concatenação.
  - `get_all`, `get`, `prepare_incoming` (converte dados brutos do formulário), `create` (gera id quando necessário), `update` (retorna `None` se não existir), `delete` (retorna bool).
  - `export()` aplica as edições; em GeoJSON reconstrói uma FeatureCollection válida (todos os arquivos concatenados), senão exporta lista de objetos. Usa nome genérico (`export.geojson`/`export.json`) quando há várias fontes.
- `geotiff_service.py` — salva GeoTIFFs com UUID e extrai metadados: CRS, transformação, limites, resolução, pontos de controle, bandas (estatísticas/tags), tags GDAL/TIFF; reprojeta para EPSG:4326 e gera PNG + limites para o Leaflet. Remove `PROJ_DATA` do ambiente na importação.
- `routes_geotiff.py` — upload de GeoTIFF (aceita apenas `.tif`/`.tiff`, senão HTTP 400) retornando id, prévia e metadados; consulta de metadados (HTTP 404 se a camada não existir).

## Templates

- `base.html` — layout comum; define os blocos `content` e `scripts`.
- `datatable.html` — tabela de registros (CRUD, exportação).
- `form.html` — criação/edição de registro.
- `map.html` — mapa Leaflet com as camadas GeoJSON.
- `upload.html` — importação de arquivo e estado atual dos dados.

## Convenções

- Docstrings e comentários em português; uma docstring curta por módulo, classe e função.
- Novas páginas estendem `base.html` e usam os blocos `content`/`scripts`.
- Os dados vivem apenas em memória (`store`); reiniciar o servidor os descarta.
- Ao alterar comportamento, atualize a docstring correspondente e este arquivo.
