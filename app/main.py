"""
Aplicação principal do editor de arquivos JSON.

Responsável por inicializar o FastAPI, configurar os recursos
estáticos e registrar as rotas da aplicação.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import crud, geotiff

APP_DIR = Path(__file__).resolve().parent

# Criação da aplicação
app = FastAPI(title=settings.app_name)

# Arquivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static",
)


# Rotas
app.include_router(crud.router)
app.include_router(geotiff.routers_geotiff)
