
"""Testes para páginas e templates."""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.crud import store
from app.config import settings


def test_home_page_redirect_when_empty(client):
    """A página inicial com dados vazios deve redirecionar para importação."""
    response = client.get("/", follow_redirects=False)
    # Se vazio, redireciona para /import
    assert response.status_code in [200, 307, 308]


def test_home_page_shows_datatable_with_data(client, json_file_with_data):
    """A página inicial deve exibir a tabela quando há dados."""
    with open(json_file_with_data, "rb") as f:
        client.post(
            "/import",
            data={"concatenar": False},
            files={"file": ("test.json", f, "application/json")},
        )

    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Verifica que a página contém elementos da tabela
    content = response.text
    assert "tabela" in content.lower() or "table" in content.lower()


def test_import_page_loaded(client):
    """A página de importação deve ser exibida."""
    response = client.get("/import")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    content = response.text
    assert "upload" in content.lower() or "import" in content.lower()


def test_import_page_with_existing_data(client, json_file_with_data):
    """A página de importação deve funcionar mesmo com dados carregados."""
    with open(json_file_with_data, "rb") as f:
        client.post(
            "/import",
            data={"concatenar": False},
            files={"file": ("test.json", f, "application/json")},
        )

    response = client.get("/import")
    assert response.status_code == 200


def test_map_page_with_geojson(client, geojson_file_with_data):
    """A página de mapa deve renderizar com dados GeoJSON."""
    with open(geojson_file_with_data, "rb") as f:
        client.post(
            "/import",
            data={"concatenar": False},
            files={"file": ("test.geojson", f, "application/json")},
        )

    response = client.get("/map")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    content = response.text
    assert "map" in content.lower() or "leaflet" in content.lower()


def test_unknown_route_returns_404(client):
    """Uma rota inexistente deve retornar HTTP 404."""
    response = client.get("/__rota_inexistente__")
    assert response.status_code == 404


class TestTemplateRendering:
    """Testes para renderização de templates."""

    def test_datatable_template_shows_columns(self, client, json_file_with_data):
        """O template da tabela deve exibir as colunas dos dados."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        response = client.get("/")
        content = response.text
        # Verifica que as colunas estão no HTML
        assert "name" in content.lower()
        assert "email" in content.lower()

    def test_datatable_template_shows_records(self, client, json_file_with_data):
        """O template da tabela deve exibir os registros."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        response = client.get("/")
        content = response.text
        # Verifica que os dados estão no HTML
        assert "Alice" in content
        assert "Bob" in content

    def test_datatable_geometry_display(self, client, geojson_file_with_data):
        """A geometria em GeoJSON deve ser exibida de forma resumida."""
        with open(geojson_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.geojson", f, "application/json")},
            )

        response = client.get("/")
        content = response.text
        # Geometria deve estar presente (resumida ou completa)
        assert "Point" in content or "coordinates" in content

    def test_upload_form_present(self, client):
        """A página de upload deve conter um formulário."""
        response = client.get("/import")
        content = response.text
        assert "form" in content.lower()
        assert "file" in content.lower() or "upload" in content.lower()

    def test_map_page_leaflet_integration(self, client, geojson_file_with_data):
        """A página de mapa deve integrar o Leaflet."""
        with open(geojson_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.geojson", f, "application/json")},
            )

        response = client.get("/map")
        content = response.text
        # Verifica integração com Leaflet
        assert "leaflet" in content.lower() or "L.map" in content or "coordinates" in content
        assert "btnUploadGeotiff" not in content
        assert "js/geotiff.js" not in content

    def test_legacy_geotiff_upload_route_is_not_available(self, client):
        """O upload de GeoTIFF deve ocorrer exclusivamente pela rota integrada."""
        response = client.post("/geotiff/upload")
        assert response.status_code == 404


class TestFormHandling:
    """Testes para manipulação de formulários."""

    def test_create_record_form_submission(self, client, json_file_with_data):
        """Submissão do formulário de criação deve criar novo registro."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        initial_count = len(store.records)

        response = client.post(
            "/records/new",
            data={"name": "Diana", "email": "diana@example.com", "age": "28"},
        )

        assert response.status_code in [200, 303]
        assert len(store.records) == initial_count + 1

    def test_update_record_form_submission(self, client, json_file_with_data):
        """Submissão do formulário de edição deve atualizar registro."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        record_id = store.records[0][settings.id_field]

        response = client.post(
            f"/records/{record_id}/edit",
            data={"name": "Alice Updated", "email": "alice.new@example.com", "age": "31"},
        )

        assert response.status_code in [200, 303]
        updated = store.get(record_id)
        assert updated["name"] == "Alice Updated"

    def test_export_form_json_format(self, client, json_file_with_data):
        """Exportação em formato JSON deve funcionar."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        response = client.get("/export")
        assert response.status_code == 200

    def test_export_form_csv_format(self, client, json_file_with_data):
        """Exportação em formato CSV deve funcionar."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        response = client.get("/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
