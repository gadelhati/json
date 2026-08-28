"""
Aplicação principal do editor de arquivos JSON.

Responsável por inicializar o FastAPI, configurar os recursos
estáticos e registrar as rotas da aplicação.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.routes.json_routes import router


# Diretório raiz do pacote src
BASE_DIR = Path(__file__).resolve().parent

# Diretórios da aplicação
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


# Criação da aplicação
app = FastAPI(
    title="Editor JSON",
    description="Aplicação para upload, edição e gerenciamento de arquivos JSON.",
    version="1.0.0",
)


# Arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


# Templates Jinja2
templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)


# Rotas
app.include_router(router)
