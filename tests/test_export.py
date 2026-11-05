"""Testes para exportação de dados em diferentes formatos."""

import json
import csv
import io
import pytest
from app.services.crud import store


class TestExportFormats:
    """Testes para integridade e formatos de exportação."""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, json_file_with_data):
        """Carrega dados JSON de exemplo."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

    def test_export_json_preserves_records(self, client):
        """Exportação JSON deve preservar todos os registros."""
        response = client.get("/export")
        assert response.status_code == 200

        data = json.loads(response.content)
        assert len(data) == 3
        assert data[0]["name"] == "Alice"

    def test_export_json_preserves_types(self, client):
        """Exportação JSON deve preservar tipos de dados."""
        response = client.get("/export")
        data = json.loads(response.content)

        record = data[0]
        assert isinstance(record["age"], int)

    def test_export_csv_format(self, client):
        """Exportação em CSV deve incluir todos os campos."""
        response = client.get("/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        csv_text = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"


class TestExportEdgeCases:
    """Testes para casos extremos na exportação."""

    def test_export_empty_store(self, client):
        """Exportação com store vazio deve retornar erro."""
        response = client.get("/export")
        assert response.status_code == 400

    def test_export_csv_empty_store(self, client):
        """Exportação CSV com store vazio deve retornar erro."""
        response = client.get("/export/csv")
        assert response.status_code == 400

    def test_export_after_deletion(self, client, json_file_with_data):
        """Exportação após deleção deve refletir mudanças."""
        with open(json_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        record_id = store.records[0]["id"]
        client.post(f"/records/{record_id}/delete")

        response = client.get("/export")
        data = json.loads(response.content)
        assert len(data) == 2
