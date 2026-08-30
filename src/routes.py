import json
import shutil

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .config import settings
from .services import store

router = APIRouter()
templates = Jinja2Templates(directory="templates")

GEOMETRY_PLACEHOLDER = '{\n  "type": "Point",\n  "coordinates": [0, 0]\n}'

# Tipos de geometria previstos pela especificação GeoJSON (RFC 7946, seção 3.1).
GEOMETRY_TYPES = [
    "Point",
    "LineString",
    "Polygon",
    "MultiPoint",
    "MultiLineString",
    "MultiPolygon",
    "GeometryCollection",
]


def _display_records() -> list[dict]:
    """Cópia dos registros para exibição na tabela, com a geometria (se houver)
    resumida como texto curto em vez do objeto completo."""
    display = []
    for record in store.get_all():
        r = dict(record)
        geom = r.get(store.GEOMETRY_FIELD)
        if geom is not None:
            geom_str = json.dumps(geom, ensure_ascii=False)
            r[store.GEOMETRY_FIELD] = geom_str if len(geom_str) <= 60 else geom_str[:57] + "..."
        display.append(r)
    return display


@router.get("/")
def index(request: Request):
    if not store.records:
        return RedirectResponse("/import")
    return templates.TemplateResponse(
        request,
        "datatable.html",
        {
            "columns": store.columns,
            "records": _display_records(),
            "id_field": settings.id_field,
            "is_geojson": store.source_format == "geojson",
            "geometry_field": store.GEOMETRY_FIELD,
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
        raise HTTPException(status_code=400, detail=f"Falha ao importar JSON/GeoJSON: {exc}") from exc
    return RedirectResponse("/", status_code=303)


@router.get("/records/new")
def new_form(request: Request):
    is_geojson = store.source_format == "geojson"
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "columns": store.columns,
            "id_field": settings.id_field,
            "record": {},
            "is_new": True,
            "is_geojson": is_geojson,
            "geometry_field": store.GEOMETRY_FIELD,
            "geometry_value": GEOMETRY_PLACEHOLDER if is_geojson else "",
            "geometry_types": GEOMETRY_TYPES,
        },
    )


@router.post("/records/new")
async def create_record(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items() if k != settings.id_field}
    try:
        data = store.prepare_incoming(data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Geometria inválida (JSON malformado): {exc}") from exc
    store.create(data)
    return RedirectResponse("/", status_code=303)


@router.get("/records/{record_id}/edit")
def edit_form(request: Request, record_id: str):
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    is_geojson = store.source_format == "geojson"
    geometry_value = (
        json.dumps(record.get(store.GEOMETRY_FIELD), ensure_ascii=False, indent=2)
        if is_geojson
        else ""
    )
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "columns": store.columns,
            "id_field": settings.id_field,
            "record": record,
            "is_new": False,
            "is_geojson": is_geojson,
            "geometry_field": store.GEOMETRY_FIELD,
            "geometry_value": geometry_value,
            "geometry_types": GEOMETRY_TYPES,
        },
    )


@router.post("/records/{record_id}/edit")
async def update_record(request: Request, record_id: str):
    form = await request.form()
    data = {k: v for k, v in form.items() if k != settings.id_field}
    try:
        data = store.prepare_incoming(data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Geometria inválida (JSON malformado): {exc}") from exc
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
    media_type = "application/geo+json" if store.source_format == "geojson" else "application/json"
    return FileResponse(path, filename=path.name, media_type=media_type)