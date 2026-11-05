"""Configuração de fixtures e hooks para testes."""

import sys
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

# Adiciona a raiz do projeto ao caminho de importação.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app
from app.services.crud import store


@pytest.fixture
def client():
    """Cliente de teste para a aplicação FastAPI."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    """Reseta o store antes de cada teste para isolar testes."""
    store.records = []
    store.source_filenames = []
    store.source_format = "json"
    yield
    # Limpa após o teste
    store.records = []
    store.source_filenames = []
    store.source_format = "json"


@pytest.fixture
def sample_json_data():
    """Dados JSON de exemplo para testes."""
    return [
        {"id": "1", "name": "Alice", "email": "alice@example.com", "age": 30},
        {"id": "2", "name": "Bob", "email": "bob@example.com", "age": 25},
        {"id": "3", "name": "Charlie", "email": "charlie@example.com", "age": 35},
    ]


@pytest.fixture
def sample_geojson_data():
    """Dados GeoJSON de exemplo para testes."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-73.9857, 40.7484]},
                "properties": {"id": "1", "name": "Central Park", "city": "New York"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
                "properties": {"id": "2", "name": "Golden Gate Park", "city": "San Francisco"},
            },
        ],
    }


@pytest.fixture
def json_file_with_data(tmp_path, sample_json_data):
    """Cria um arquivo JSON temporário com dados de teste."""
    json_file = tmp_path / "test_data.json"
    json_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    return json_file


@pytest.fixture
def geojson_file_with_data(tmp_path, sample_geojson_data):
    """Cria um arquivo GeoJSON temporário com dados de teste."""
    geojson_file = tmp_path / "test_locations.geojson"
    geojson_file.write_text(json.dumps(sample_geojson_data), encoding="utf-8")
    return geojson_file
