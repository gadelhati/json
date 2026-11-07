"""Testes para operações CRUD de JSON."""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.crud import store
from app.config import settings


@pytest.fixture(autouse=True)
def clear_store():
    """Limpa o store antes de cada teste."""
    store.records = []
    store.source_filenames = []
    store.source_format = "json"
    store.geotiff_layers = {}
    store.source_paths = {}
    store.source_names = {}
    store.xml_root_tag = None
    store.xml_root_attributes = {}
    store.xml_uses_root_record = False
    yield
    # Limpa após o teste
    store.records = []
    store.source_filenames = []
    store.source_format = "json"
    store.geotiff_layers = {}
    store.source_paths = {}
    store.source_names = {}
    store.xml_root_tag = None
    store.xml_root_attributes = {}
    store.xml_uses_root_record = False


@pytest.fixture
def sample_json_file(tmp_path):
    """Cria um arquivo JSON de exemplo para testes."""
    data = [
        {"id": "1", "name": "Alice", "age": 30},
        {"id": "2", "name": "Bob", "age": 25},
    ]
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(data))
    return json_file


class TestJsonUpload:
    """Testes para upload de arquivos JSON."""

    def test_upload_valid_json(self, client, sample_json_file):
        """Upload de um arquivo JSON válido deve retornar sucesso."""
        with open(sample_json_file, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )
        assert response.status_code in [200, 303]
        assert len(store.records) == 2

    def test_upload_json_with_append_mode(self, client, sample_json_file, tmp_path):
        """Upload com modo 'append' deve concatenar registros."""
        # Primeiro upload
        with open(sample_json_file, "rb") as f:
            response1 = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )
        assert response1.status_code in [200, 303]
        assert len(store.records) == 2

        # Segundo upload em modo append
        data2 = [{"id": "3", "name": "Charlie", "age": 35}]
        json_file2 = tmp_path / "test2.json"
        json_file2.write_text(json.dumps(data2))

        with open(json_file2, "rb") as f:
            response2 = client.post(
                "/import",
                data={"concatenar": True},
                files={"file": ("test2.json", f, "application/json")},
            )
        assert response2.status_code in [200, 303]
        assert len(store.records) == 3

    def test_upload_invalid_json(self, client, tmp_path):
        """Upload de um arquivo JSON inválido deve retornar erro."""
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("{ invalid json }")

        with open(invalid_json, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("invalid.json", f, "application/json")},
            )
        assert response.status_code in [400, 422]

    def test_upload_json_with_missing_id_field(self, client, tmp_path):
        """Upload de JSON sem o campo ID deve gerar UUIDs automaticamente."""
        data = [{"name": "Alice", "age": 30}]
        json_file = tmp_path / "no_id.json"
        json_file.write_text(json.dumps(data))

        with open(json_file, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("no_id.json", f, "application/json")},
            )
        assert response.status_code in [200, 303]
        assert len(store.records) == 1
        assert settings.id_field in store.records[0]

    def test_upload_empty_json_list(self, client, tmp_path):
        """Upload de um arquivo JSON vazio (lista vazia) deve ser aceito."""
        json_file = tmp_path / "empty.json"
        json_file.write_text(json.dumps([]))

        with open(json_file, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("empty.json", f, "application/json")},
            )
        assert response.status_code in [200, 303]
        assert len(store.records) == 0

    def test_json_source_is_listed_and_can_be_deleted(self, client, sample_json_file):
        """Arquivos JSON devem aparecer na lista comum e poder ser excluídos."""
        with open(sample_json_file, "rb") as file:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", file, "application/json")},
            )

        source_id = store.records[0][store.SOURCE_ID_FIELD]
        for path in ("/", "/map", "/import"):
            page = client.get(path)
            assert "Arquivos importados" in page.text
            assert "test.json" in page.text
            assert f"/sources/{source_id}/delete" in page.text

        response = client.post(f"/sources/{source_id}/delete", follow_redirects=False)
        assert response.status_code == 303
        assert store.records == []
        assert store.source_summaries() == []


class TestJsonDownload:
    """Testes para download de arquivos JSON."""

    def test_download_json_after_upload(self, client, sample_json_file):
        """Download deve exportar os dados carregados em JSON."""
        # Upload
        with open(sample_json_file, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        # Download
        response = client.get("/export")
        assert response.status_code == 200

        # Verifica o conteúdo
        data = json.loads(response.content)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_download_json_empty_store(self, client):
        """Download com store vazio deve retornar erro."""
        response = client.get("/export")
        assert response.status_code == 400

    def test_download_json_filename(self, client, sample_json_file):
        """O arquivo baixado deve ter um nome apropriado."""
        with open(sample_json_file, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

        response = client.get("/export")
        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")


class TestJsonCrud:
    """Testes para operações CRUD (Create, Read, Update, Delete)."""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, sample_json_file):
        """Carrega dados de exemplo antes de cada teste."""
        with open(sample_json_file, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.json", f, "application/json")},
            )

    def test_create_new_record(self, client):
        """Criação de um novo registro deve adicionar à lista."""
        new_record = {"name": "Diana", "age": "28"}
        response = client.post("/records/new", data=new_record, follow_redirects=False)
        assert response.status_code in [200, 303]
        assert len(store.records) == 3

    def test_read_all_records(self, client):
        """Leitura de todos os registros deve retornar a lista completa."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_update_existing_record(self, client):
        """Atualização de um registro deve modificar seus dados."""
        record_id = store.records[0][settings.id_field]
        updated_data = {"name": "Alice Updated", "age": "31"}
        response = client.post(f"/records/{record_id}/edit", data=updated_data, follow_redirects=False)
        assert response.status_code in [200, 303]
        
        updated_record = store.get(record_id)
        assert updated_record["name"] == "Alice Updated"

    def test_update_nonexistent_record(self, client):
        """Atualização de um registro inexistente deve retornar 404."""
        response = client.post("/records/nonexistent/edit", data={"name": "Test"})
        assert response.status_code == 404

    def test_delete_existing_record(self, client):
        """Exclusão de um registro deve removê-lo da lista."""
        record_id = store.records[0][settings.id_field]
        initial_count = len(store.records)
        
        response = client.post(f"/records/{record_id}/delete", follow_redirects=False)
        assert response.status_code in [200, 303]
        assert len(store.records) == initial_count - 1

    def test_delete_nonexistent_record(self, client):
        """Exclusão de um registro inexistente deve retornar 404."""
        response = client.post("/records/nonexistent/delete")
        assert response.status_code == 404

    def test_crud_preserves_data_integrity(self, client):
        """Operações CRUD não devem corromper dados de outros registros."""
        original_record_id = store.records[1][settings.id_field]
        original_record = store.get(original_record_id)

        # Atualiza primeiro registro
        first_record_id = store.records[0][settings.id_field]
        client.post(f"/records/{first_record_id}/edit", data={"name": "Updated"})

        # Verifica se o segundo registro permanece intacto
        updated_record = store.get(original_record_id)
        assert updated_record == original_record
