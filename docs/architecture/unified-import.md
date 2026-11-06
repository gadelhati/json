# Plano de Integração: Upload Unificado JSON/GeoJSON/GeoTIFF

## Visão Geral
Integrar os dois sistemas de import (JSON/GeoJSON e GeoTIFF) em uma única solução, permitindo:
- Upload de múltiplos tipos em um campo único
- Concatenação entre tipos
- Metadados de GeoTIFF como registros na tabela principal
- Camadas GeoTIFF no mapa com geometrias

## Arquitetura Proposta

### 1. Estrutura de Armazenamento

#### JsonStore (app/services/crud.py)
- Continua armazenando registros JSON/GeoJSON em memória
- **Novo**: Adiciona suporte para registros gerados a partir de GeoTIFF
  - Cada GeoTIFF carregado gera um registro com seus metadados
  - Campo `_geotiff_id`: referência ao arquivo GeoTIFF
  - Campo `_geotiff_preview`: caminho da prévia PNG

#### GeotiffStore (novo conceito)
- Continua gerenciando GeoTIFF como "camadas"
- Cada GeoTIFF tem: metadados, limites (geometry), preview, PNG
- Acesso integrado ao JsonStore para leitura dos registros

### 2. Rotas Consolidadas

#### POST /import (modificada)
```
Aceita: multipart/form-data
- file: JSON | GeoJSON | GeoTIFF (.tif, .tiff, .json, .geojson)
- concatenar: boolean
- replace_geotiff: boolean (se True, substitui GeoTIFFs anteriores)

Retorna: Redirect para / (302)
```

Comportamento:
1. Detecta tipo do arquivo
2. Se JSON/GeoJSON: carrega normalmente na JsonStore
3. Se GeoTIFF:
   - Processa com geotiff_service
   - Cria registro com metadados na JsonStore
   - Mantém camada no GeotiffStore

### 3. Formulário de Importação (upload.html)

**Antes:**
- Campo único aceita `application/json, application/geo+json`
- Botão de importação

**Depois:**
- Campo único aceita `application/json, application/geo+json, .tif, .tiff`
- Checkbox "Concatenar com dados já carregados" (aplica a JSON/GeoJSON)
- Checkbox "Substituir GeoTIFFs anteriores" (aplica a GeoTIFF)
- Info do formato atual + arquivos

### 4. Visualização na Tabela

Registros de GeoTIFF aparecem com:
- Colunas padrão: id, nome do arquivo, CRS, resolução, bandas
- Campo especial `_geometry` com limites (EPSG:4326)
- Ícone/indicador visual que é GeoTIFF

Ação: "Visualizar no mapa" (redireciona com layer selecionada)

### 5. Visualização no Mapa

GeoTIFF:
- Aparece como camada com limites (bounding box como Polygon)
- Toggle para ativar/desativar
- Controle de opacidade
- Preview PNG como overlay

### 6. Exportação

Integrada:
- JSON: inclui apenas registros JSON/GeoJSON (exclui metadados de GeoTIFF)
- GeoJSON: inclui geometrias de JSON/GeoJSON + limites de GeoTIFF
- CSV: registros normais + metadados de GeoTIFF como colunas

## Mudanças de Código

### app/services/crud.py (JsonStore)
- Adicionar tipo `geotiff_record` para distinguir
- Método `add_geotiff_metadata(file_id, metadata, bounds_geom, preview_path)`
- Marcar registros GeoTIFF com `_source_type: "geotiff"`

### app/routers/crud.py
- Modificar `/import` para detectar e processar GeoTIFF
- Consolidar lógica de importação

### app/routers/geotiff.py
- Remover `/geotiff/upload` (agora integrado em `/import`)
- Manter `/geotiff/{file_id}/metadata` (consulta)

### app/templates/upload.html
- Campo accept atualizado
- Adicionar checkboxes para comportamento de concatenação/substituição

### app/templates/datatable.html
- Indicador visual para registros GeoTIFF
- Link "Visualizar no mapa" para GeoTIFF

### app/main.py
- Sem mudanças (rotas já registradas)

## Implementação Passo a Passo

1. ✅ Modificar `JsonStore` para suportar metadados de GeoTIFF
2. ✅ Criar helper para gerar record a partir de GeoTIFF
3. ✅ Modificar rota `/import` para detectar tipo de arquivo
4. ✅ Atualizar template `upload.html`
5. ✅ Atualizar template `datatable.html`
6. ✅ Testar fluxo completo

## Benefícios

- ✨ UX mais simples: um campo para tudo
- 🔄 Suporta mistura de tipos (JSON + GeoTIFF no mesmo projeto)
- 📊 Metadados de GeoTIFF visíveis na tabela
- 🗺️ GeoTIFF com geometrias no mapa
- 📥 Concatenação flexível entre tipos
