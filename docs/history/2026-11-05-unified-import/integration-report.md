# Relatório de Integração: Upload Unificado JSON/GeoJSON/GeoTIFF

## ✅ Implementação Concluída

A aplicação agora possui um **sistema integrado de importação** que suporta:
- **JSON/GeoJSON** (.json, .geojson)
- **GeoTIFF** (.tif, .tiff)

Tudo em um único campo de upload com interface simplificada.

---

## 📋 Mudanças Implementadas

### 1. **app/services/crud.py** (JsonStore)

#### Novos campos de controle:
```python
SOURCE_TYPE_FIELD = "_source_type"     # "json", "geojson" ou "geotiff"
GEOTIFF_ID_FIELD = "_geotiff_id"       # Referência ao arquivo GeoTIFF
GEOTIFF_PREVIEW_FIELD = "_geotiff_preview"  # URL da prévia PNG
geotiff_layers: dict[str, dict]        # Armazenamento de metadados GeoTIFF
```

#### Novos métodos:
- **`add_geotiff_metadata(...)`**: Adiciona um registro GeoTIFF com metadados extraídos
  - Cria um registro que aparece na tabela principal
  - Extrai: CRS, resolução, limites (EPSG:4326), estatísticas de bandas
  - Armazena referência para preview e geometria de limites

#### Métodos modificados:
- **`create(...)`**: Agora marca o tipo de fonte (`_source_type`)
- **`feature_collections_by_layer(...)`**: Agora inclui camadas GeoTIFF como limites (Polygon)

---

### 2. **app/routers/crud.py**

#### Rota unificada `/import` (POST):
```python
@router.post("/import")
async def import_file(
    file: UploadFile,
    concatenar: bool = Form(False),      # Para JSON/GeoJSON
    substituir_geotiff: bool = Form(False)  # Para GeoTIFF
)
```

**Comportamento:**
- **Detecta tipo** pelo nome do arquivo
- **JSON/GeoJSON**: 
  - `concatenar=true`: adiciona aos dados existentes (mesmo formato)
  - `concatenar=false`: substitui dados anteriores
- **GeoTIFF**:
  - `substituir_geotiff=true`: remove GeoTIFFs anteriores
  - `substituir_geotiff=false`: adiciona à coleção existente
- **Cross-type**: Permite misturar JSON com GeoTIFF

---

### 3. **app/templates/upload.html**

**Antes:**
- Aceitava: JSON/GeoJSON apenas
- Um formulário simples

**Depois:**
- Aceita: JSON, GeoJSON, GeoTIFF
- Formulário com fieldsets organizados:
  - "Selecione um arquivo" com descrição dos formatos aceitos
  - "Opções de carregamento" com checkboxes:
    - ☐ Concatenar com dados já carregados
    - ☐ Substituir GeoTIFFs anteriores

---

### 4. **app/templates/datatable.html**

**Novos elementos:**
- **Coluna "T"** (Tipo): Indicador visual
  - 📄 = JSON
  - 🔷 = GeoJSON (com geometria)
  - 🗺️ = GeoTIFF

- **Coluna "Ações" modificada**:
  - Para registros normais: "Editar" + "Excluir"
  - Para GeoTIFF: "Mapa" (link para visualizar no mapa) + "Excluir"

- **Link "Ver mapa"** adicionado à barra de ferramentas

---

### 5. **app/services/crud.py** (feature_collections_by_layer)

**Mudanças:**
- Inclui camadas de GeoJSON (como antes)
- **Novo**: Inclui camadas GeoTIFF como Polygon de limites
- Cada GeoTIFF é uma Feature com:
  - `geometry`: bounding box em EPSG:4326
  - `properties.tipo`: "GeoTIFF"
  - `properties.crs`: CRS do raster
  - `properties.preview`: URL da prévia

---

## 🎯 Fluxo de Uso

### Importar GeoJSON:
1. Acesse `/import`
2. Selecione um arquivo `.geojson`
3. (Opcional) Marque "Concatenar" para adicionar aos dados existentes
4. Clique "Importar" → Redirecionado para tabela
5. Veja os dados na tabela (com indicador 🔷)
6. Visualize no mapa `/map`

### Importar GeoTIFF:
1. Acesse `/import`
2. Selecione um arquivo `.tif` ou `.tiff`
3. (Opcional) Marque "Substituir GeoTIFFs anteriores"
4. Clique "Importar" → Redirecionado para tabela
5. Veja os metadados como registro (com indicador 🗺️)
6. Clique "Mapa" para visualizar o raster no mapa

### Misturar tipos:
1. Importe um GeoJSON
2. Retorne a `/import`
3. Importe um GeoTIFF **sem marcar "Substituir GeoTIFFs"**
4. Ambos aparecem na tabela (com indicadores diferentes)
5. Mapa mostra camadas de geometrias + limites de raster

---

## 🧪 Testes

Todos os 44 testes existentes continuam passando:
```
tests/test_export.py          ✅ 6/6 passed
tests/test_geojson.py         ✅ 8/8 passed
tests/test_json_crud.py       ✅ 15/15 passed
tests/test_pages.py           ✅ 15/15 passed
```

**Novo**: Teste de integração manual validou:
- ✅ Upload de GeoJSON via formulário
- ✅ Dados aparecem na tabela
- ✅ Dados aparecem no mapa
- ✅ Redirecionamentos funcionam

---

## 📊 Metadados de GeoTIFF na Tabela

Quando um GeoTIFF é carregado, o registro criado contém:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `_source` | str | Nome do arquivo |
| `_source_type` | "geotiff" | Tipo do registro |
| `_geometry` | Polygon | Limites em EPSG:4326 |
| `_geotiff_id` | UUID | ID do arquivo na preview |
| `_geotiff_preview` | str | URL da prévia PNG |
| `crs` | str | CRS do raster |
| `resolucao_x` | float | Resolução em X |
| `resolucao_y` | float | Resolução em Y |
| `bandas` | int | Número de bandas |
| `banda_1_media` | float | Média da banda 1 |
| `banda_1_min` | float | Mínimo da banda 1 |
| `banda_1_max` | float | Máximo da banda 1 |
| ... | ... | Estatísticas para outras bandas |

---

## 🗺️ Visualização no Mapa

### Camadas GeoJSON:
- Aparecem como Features com geometrias originais
- Um toggle por arquivo importado
- Controle de opacidade
- Cores diferentes por camada

### Camadas GeoTIFF:
- Aparecem como Polygon com os limites (bounding box)
- Label com nome do arquivo
- Quando selecionado, pode-se ver:
  - Preview PNG do raster
  - Metadados (CRS, resolução, etc.)

---

## 💾 Exportação

- **JSON**: Exporta registros JSON (exclui GeoTIFF)
- **GeoJSON**: Exporta geometrias de JSON + limites de GeoTIFF
- **CSV**: Exporta todas as colunas (metadados de GeoTIFF inclusos)

---

## 🔄 Backward Compatibility

✅ **100% compatível** com imports anteriores:
- Aplicativos existentes continuam funcionando
- Rotas anteriores `/geotiff/upload` deixadas como fallback
- Todos os testes antigos passam

---

## 🎉 Benefícios

| Antes | Depois |
|-------|--------|
| Dois formulários separados | Um formulário unificado |
| Importar JSON OU GeoTIFF | Importar JSON E GeoTIFF na mesma sessão |
| GeoTIFF invisível na tabela | Metadados de GeoTIFF como registros |
| Experiência fragmentada | Experiência integrada |

---

## 📝 Próximos Passos (Sugestões)

1. **Teste E2E**: Cenários completos de workflow (upload múltiplo, exportação)
2. **UI Aprimoramentos**: Drag-and-drop para upload, progress bars
3. **Performance**: Cache de previews de GeoTIFF para uploads grandes
4. **Metadados**: Persistência dos metadados extraídos (banco de dados)
5. **Busca avançada**: Filtrar registros por tipo, CRS, etc.

---

## 📄 Arquivos Modificados

```
app/services/crud.py          ✏️ Novos campos, métodos para GeoTIFF
app/routers/crud.py            ✏️ Rota unificada /import
app/templates/upload.html      ✏️ Formulário integrado
app/templates/datatable.html   ✏️ Indicadores de tipo, link ao mapa
```

---

**Integração concluída com sucesso!** 🚀
