import shutil

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .config import settings
from .services import store

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def index(request: Request):
    if not store.records:
        return RedirectResponse("/import")
    return templates.TemplateResponse(
        request,
        "datatable.html",
        {
            "columns": store.columns,
            "records": store.get_all(),
            "id_field": settings.id_field,
        },
    )


@router.get("/import")
def import_form(request: Request):
    return templates.TemplateResponse(request, "upload.html", {})


@router.post("/import")
async def import_json(file: UploadFile = File(...)):
    dest = settings.upload_dir / file.filename
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        store.load(dest)
    except (ValueError, Exception) as exc:  # json.JSONDecodeError herda de ValueError
        raise HTTPException(status_code=400, detail=f"Falha ao importar JSON: {exc}") from exc
    return RedirectResponse("/", status_code=303)


@router.get("/records/new")
def new_form(request: Request):
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "columns": store.columns,
            "id_field": settings.id_field,
            "record": {},
            "is_new": True,
        },
    )


@router.post("/records/new")
async def create_record(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items() if k != settings.id_field}
    store.create(data)
    return RedirectResponse("/", status_code=303)


@router.get("/records/{record_id}/edit")
def edit_form(request: Request, record_id: str):
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "columns": store.columns,
            "id_field": settings.id_field,
            "record": record,
            "is_new": False,
        },
    )


@router.post("/records/{record_id}/edit")
async def update_record(request: Request, record_id: str):
    form = await request.form()
    data = {k: v for k, v in form.items() if k != settings.id_field}
    if store.update(record_id, data) is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return RedirectResponse("/", status_code=303)


@router.post("/records/{record_id}/delete")
def delete_record(record_id: str):
    if not store.delete(record_id):
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return RedirectResponse("/", status_code=303)


@router.get("/export")
def export_json():
    if not store.records:
        raise HTTPException(status_code=400, detail="Nenhum dado importado para exportar")
    path = store.export()
    return FileResponse(path, filename=path.name, media_type="application/json")