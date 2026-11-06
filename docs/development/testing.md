# Resumo dos Testes Implementados

Foram implementados **44 testes automatizados** para os itens de testes
concluídos no [roadmap](roadmap.md).

| Arquivo | Testes | Cobertura principal |
|---|---:|---|
| `tests/test_json_crud.py` | 20 | Upload, download e CRUD de JSON |
| `tests/test_export.py` | 6 | Exportação JSON e CSV |
| `tests/test_geojson.py` | 8 | Importação e exportação GeoJSON |
| `tests/test_pages.py` | 14 | Páginas, templates e formulários |
| `tests/conftest.py` | — | Fixtures e isolamento do armazenamento em memória |

## Cobertura

- Importação de JSON e GeoJSON, incluindo concatenação e dados inválidos.
- Criação, leitura, atualização e exclusão de registros, inclusive respostas 404.
- Exportação JSON, GeoJSON e CSV, com validação de integridade.
- Renderização da tabela, mapa, formulários e rotas inexistentes.
- Casos de borda, como armazenamento vazio, IDs ausentes e geometria nula.

## Validação

```text
44 passed in 2.01s
```

## Execução

```bash
pytest tests/ -v
pytest tests/ --cov=app
```
