# Guia de Uso: Upload Integrado

## Visão Geral

A partir desta versão, o editor suporta um **sistema unificado de importação** que permite carregar JSON, GeoJSON e GeoTIFF em um único fluxo. Você não precisa mais alternar entre dois formulários diferentes.

---

## 📥 Como Importar

### 1. Acessar a página de importação
```
GET /import
```

Você verá um formulário único com:
- Campo para selecionar arquivo (aceita `.json`, `.geojson`, `.tif`, `.tiff`)
- Opções de carregamento (checkboxes)
- Botões "Importar" e "Cancelar"

### 2. Selecionar o arquivo
Clique no campo de arquivo e escolha:
- **JSON/GeoJSON**: Arquivo com dados vetoriais ou objetos
- **GeoTIFF**: Arquivo com dados raster

### 3. Configurar opções (se já há dados)

#### Para JSON/GeoJSON:
- ☐ **Concatenar com os dados já carregados**
  - Se marcado: adiciona registros do novo arquivo aos existentes
  - Se não marcado: substitui todos os dados
  - ⚠️ Só funciona se ambos os arquivos têm o mesmo formato (JSON com JSON ou GeoJSON com GeoJSON)

#### Para GeoTIFF:
- ☐ **Substituir GeoTIFFs anteriores**
  - Se marcado: remove todos os rasters carregados antes de adicionar o novo
  - Se não marcado: adiciona o novo raster aos existentes

### 4. Importar
Clique "Importar" → A página redireciona para a tabela de registros (`/`)

---

## 🎯 Cenários de Uso

### Cenário 1: Começar do zero com GeoJSON
```
1. Clique em /import
2. Selecione um arquivo .geojson
3. Deixe "Concatenar" desmarcado
4. Clique "Importar"
→ Tabela mostra os registros com geometrias (indicador 🔷)
```

### Cenário 2: Adicionar mais GeoJSON
```
1. Já tem dados GeoJSON carregados
2. Clique em /import
3. Selecione outro .geojson
4. Marque "Concatenar com os dados já carregados"
5. Clique "Importar"
→ Tabela mostra registros de ambos os arquivos
→ Mapa mostra duas camadas (uma por arquivo)
```

### Cenário 3: Carregar um raster GeoTIFF
```
1. (Com ou sem dados anteriores)
2. Clique em /import
3. Selecione um arquivo .tif
4. Deixe "Substituir GeoTIFFs" desmarcado
5. Clique "Importar"
→ Tabela mostra um novo registro com metadados do raster (indicador 🗺️)
→ Mapa mostra os limites do raster (bounding box)
```

### Cenário 4: Misturar JSON com GeoTIFF (novo!)
```
1. Importe um arquivo .geojson
2. Volte a /import
3. Selecione um arquivo .tif
4. Deixe "Substituir GeoTIFFs" desmarcado
5. Clique "Importar"
→ Tabela mostra registros GeoJSON (🔷) E metadados GeoTIFF (🗺️)
→ Mapa mostra camada de geometrias + camada de limites de raster
```

### Cenário 5: Atualizar raster (descartar anterior)
```
1. Tem um .tif carregado
2. Volte a /import
3. Selecione outro .tif
4. Marque "Substituir GeoTIFFs anteriores"
5. Clique "Importar"
→ O raster anterior é removido
→ Novo raster aparece na tabela
```

---

## 📊 Visualizando os dados

### Tabela (`/`)
Mostra todos os registros com indicadores visuais:

| Tipo | Indicador | Ações | Notas |
|------|-----------|-------|-------|
| JSON | 📄 | Editar, Excluir | Dados sem geometria |
| GeoJSON | 🔷 | Editar, Excluir | Dados com geometria (Point, Polygon, etc.) |
| GeoTIFF | 🗺️ | **Mapa**, Excluir | Metadados extraídos; clique "Mapa" para visualizar |

### Mapa (`/map`)
Exibe:
- **Camadas GeoJSON**: Features com suas geometrias originais
  - Um toggle por arquivo importado
  - Controle de opacidade
  - Cores diferentes por camada
- **Camadas GeoTIFF**: Limites (bounding box como Polygon)
  - Label com nome do arquivo
  - Preview PNG do raster (quando clicado)
  - Metadados (CRS, resolução)
- **Controles de camada**: arquivos com geometria possuem visibilidade, opacidade
  e ordem de sobreposição.

### Lista de arquivos importados
Está disponível em todas as abas e contém todos os arquivos importados, incluindo
JSON sem geometria. No mapa, esta é a mesma lista usada para controlar as camadas:
arquivos geográficos exibem visibilidade, opacidade, ordem e **Excluir arquivo**
na mesma linha; arquivos JSON exibem apenas contagem e exclusão. Use **Excluir
arquivo** para remover seus registros da tabela, sua camada do mapa (quando houver)
e os arquivos locais associados.

---

## 💾 Exportando

### JSON
```
GET /export
```
Baixa um arquivo `.json` com todos os registros (exclui GeoTIFF).

### GeoJSON
```
GET /export  (quando dados são GeoJSON)
```
Baixa um arquivo `.geojson` com:
- Todas as Features originais (geometrias de JSON/GeoJSON)
- Limites de GeoTIFF como Polygon (cada raster = 1 Feature)

### CSV
```
GET /export/csv
```
Baixa um arquivo `.csv` com:
- Todas as colunas de registros JSON/GeoJSON
- **Incluindo** metadados de GeoTIFF:
  - `crs`: Coordinate Reference System
  - `resolucao_x`, `resolucao_y`: Resolução espacial
  - `bandas`: Número de bandas
  - `banda_1_media`, `banda_1_min`, `banda_1_max`: Estatísticas de cada banda
  - `_geometry`: Limites em WKT

---

## 🔧 Campos de Metadados de GeoTIFF

Quando um GeoTIFF é carregado, um registro é criado com:

```
id                          UUID do registro
_source                     Nome do arquivo GeoTIFF
_source_type               "geotiff"
_geometry                  Limites (Polygon EPSG:4326)
_geotiff_id                UUID do arquivo processado
_geotiff_preview           URL da prévia PNG
crs                        Ex: "EPSG:4326"
resolucao_x                Resolução em X (metros ou graus)
resolucao_y                Resolução em Y (metros ou graus)
bandas                     Número de bandas (ex: 1, 3, 4)
banda_1_media              Valor médio dos pixels da banda 1
banda_1_min                Valor mínimo dos pixels da banda 1
banda_1_max                Valor máximo dos pixels da banda 1
banda_2_media, banda_2_min, banda_2_max  (se houver banda 2)
...
```

---

## ⚙️ Comportamento de Concatenação

### JSON + JSON
✅ Suportado
- Registros são mesclados
- IDs duplicados são regenerados
- Nomes de arquivo são preservados em `_source`

### GeoJSON + GeoJSON
✅ Suportado
- Features são mescladas
- Camadas aparecem separadas no mapa (uma por arquivo)
- Geometrias preservadas

### JSON + GeoJSON
❌ Não permitido
- Erro: "Só é possível concatenar arquivos do mesmo formato"

### GeoTIFF + GeoTIFF (sem `substituir_geotiff=true`)
✅ Suportado
- Ambos os rasters aparecem como registros separados
- Mapa mostra ambos os limites

### GeoTIFF + GeoTIFF (com `substituir_geotiff=true`)
✅ Suportado
- Rasters anteriores são removidos
- Apenas o novo raster aparece

### JSON/GeoJSON + GeoTIFF
✅ **Novo** - Suportado
- Registros de ambos os tipos aparecem na tabela
- Mapa mostra geometrias + limites de raster
- Exemplos:
  - GeoJSON + GeoTIFF → tabela com 🔷 e 🗺️
  - JSON + GeoTIFF → tabela com 📄 e 🗺️

---

## 🐛 Troubleshooting

### "Só é possível concatenar arquivos do mesmo formato"
**Problema**: Tentou concatenar GeoJSON com JSON ou vice-versa.
**Solução**: Use `concatenar=false` para substituir os dados, ou carregue em sessões separadas.

### GeoTIFF não aparece na tabela
**Problema**: Upload foi bem-sucedido (código 303), mas não vê o registro.
**Solução**: Recarregue a página (`F5` ou `Ctrl+R`). Se persistir, verifique os logs do servidor.

### Mapa vazio com GeoTIFF
**Problema**: Arquivo carregado, mas limites não aparecem no mapa.
**Solução**: Verifique se o CRS do GeoTIFF é suportado; o sistema reprojeta para EPSG:4326 automaticamente.

### Excluir um arquivo importado
**Problema**: Precisa remover de uma vez todos os dados de um arquivo.
**Solução**: Na página do mapa, use **Excluir arquivo** na linha da camada.
Todos os registros, a camada e os arquivos locais associados àquela importação
serão removidos.

---

## 📝 Notas

- **Armazenamento**: Todos os dados vivem **em memória**; reiniciar o servidor descarta tudo.
- **Persistência**: Para manter dados entre sessões, exporte antes de reiniciar.
- **Limites**: Não há limite configurado de arquivos ou tamanho (configurable em `app/config.py`).
- **Conversão automática**: GeoTIFF é automaticamente reprojetado para EPSG:4326 para compatibilidade com Leaflet.

---

## 🎓 Exemplos

### Exemplo 1: Workflow típico
```bash
# 1. Iniciar servidor
uvicorn app.main:app --reload

# 2. Abrir navegador
open http://127.0.0.1:8000

# 3. Redireciona para /import (pois está vazio)
# 4. Upload de cidades.geojson
# 5. Visualizar tabela
# 6. Upload de dem.tif
# 7. Ver mapa com dados + raster
# 8. Exportar como CSV
```

### Exemplo 2: Múltiplas camadas
```
1. /import → upload: "rio_shape.geojson"
2. /import → upload: "sp_shape.geojson" (marcar "Concatenar")
3. /import → upload: "srtm_dem.tif"
4. /map → mostra 3 camadas:
   - rio_shape.geojson (Features)
   - sp_shape.geojson (Features)
   - srtm_dem.tif (Limites)
```

---

**Pronto para começar? Acesse `/import` e importe seu primeiro arquivo!** 🚀
