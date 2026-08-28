"""
Rotas relacionadas ao gerenciamento dos arquivos JSON.

Responsabilidades:
- Exibir a página inicial;
- Receber arquivos JSON;
- Validar e carregar o conteúdo;
- Exibir o editor;
- Gerar e disponibilizar o JSON atualizado para download.
"""

from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import UPLOAD_FOLDER
from src.services.json_service import load_json, save_json


router = APIRouter()

templates = Jinja2Templates(
    directory="src/templates"
)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Exibe a página inicial para upload do arquivo JSON.
    """

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Recebe um arquivo JSON, salva temporariamente e
    exibe seu conteúdo no editor.
    """

    destination = UPLOAD_FOLDER / "current.json"

    content = await file.read()

    destination.write_bytes(content)

    try:
        data = load_json(destination)

    except Exception as exc:

        destination.unlink(missing_ok=True)

        return HTMLResponse(
            content=f"JSON inválido: {exc}",
            status_code=400,
        )

    if not isinstance(data, list):

        return HTMLResponse(
            content="O JSON deve conter uma lista de objetos.",
            status_code=400,
        )

    return templates.TemplateResponse(
        request=request,
        name="editor.html",
        context={
            "data": data,
        },
    )


@router.post("/download")
async def download(request: Request):
    """
    Recebe o JSON atualizado pelo frontend, salva o arquivo
    e retorna o arquivo para download.
    """

    data = await request.json()

    if not isinstance(data, list):

        return HTMLResponse(
            content="Formato JSON inválido.",
            status_code=400,
        )

    destination = UPLOAD_FOLDER / "current.json"

    save_json(
        destination,
        data,
    )

    return FileResponse(
        path=destination,
        media_type="application/json",
        filename="dados.json",
    )
