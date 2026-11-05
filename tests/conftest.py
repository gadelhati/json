import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Adiciona a raiz do projeto ao caminho de importação.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
