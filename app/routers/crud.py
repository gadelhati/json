"""Rotas web para importar, editar, exibir e exportar dados JSON e GeoJSON."""

import csv
import io
import json
import shutil

from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.crud import store

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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
    """Exibe a tabela de registros ou redireciona para a importação se vazia."""
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
            "show_layer": store.has_multiple_sources,
            "layer_field": store.SOURCE_FIELD,
        },
    )


@router.get("/map")
def map_view(request: Request, layer: str | None = None):
    """Renderiza o mapa com as camadas GeoJSON disponíveis."""
    layers = store.feature_collections_by_layer()
    has_geometries = any(l["featureCollection"]["features"] for l in layers)
    return templates.TemplateResponse(
        request,
        "map.html",
        {
            "layers": layers,
            "has_geometries": has_geometries,
            "layers_json": json.dumps(layers, ensure_ascii=False),
            "selected_layer": layer,
        },
    )


@router.get("/import")
def import_form(request: Request):
    """Exibe o formulário de importação e o estado atual dos dados."""
    return templates.TemplateResponse(
        request,
        "upload.html",
        {
            "has_data": bool(store.records),
            "current_format": store.source_format,
            "source_filenames": store.source_filenames,
        },
    )


@router.post("/import")
async def import_file(
    file: UploadFile = File(...),
    concatenar: bool = Form(False),
    substituir_geotiff: bool = Form(False),
):
    """Importa um arquivo JSON, GeoJSON ou GeoTIFF, substituindo ou concatenando registros.
    
    Aceita:
    - JSON/GeoJSON (.json, .geojson): carrega como registros
    - GeoTIFF (.tif, .tiff): processa raster e adiciona como registro com metadados
    
    Parâmetros:
    - concatenar: se True e arquivo é JSON/GeoJSON, concatena aos dados existentes
    - substituir_geotiff: se True e arquivo é GeoTIFF, remove GeoTIFFs anteriores
    """
    from app.routers.geotiff import _layers
    from app.services.geotiff import store as geotiff_store
    
    dest = settings.upload_dir / file.filename
    
    # Detecta o tipo de arquivo
    is_geotiff = file.filename.lower().endswith((".tif", ".tiff"))
    
    try:
        if is_geotiff:
            # Processa GeoTIFF
            if not file.filename.lower().endswith((".tif", ".tiff")):
                raise HTTPException(400, "Envie um arquivo .tif ou .tiff")

            file_bytes = await file.read()
            file_id, path = geotiff_store.save_geotiff(file_bytes, file.filename)

            metadata = geotiff_store.extract_all_metadata(path)
            preview = geotiff_store.generate_leaflet_preview(path, file_id)
            
            # Se substituir_geotiff, limpa os GeoTIFFs anteriores
            if substituir_geotiff:
                # Remove registros GeoTIFF anteriores
                store.records = [
                    r for r in store.records
                    if r.get(store.SOURCE_TYPE_FIELD) != "geotiff"
                ]
                _layers.clear()

            # Adiciona o novo GeoTIFF ao store
            bounds = preview.get("bounds", [0, 0, 0, 0])
            bounds_geom = preview.get("bounds_geojson")
            
            # Se bounds_geojson não foi gerado, cria a partir de bounds Leaflet:
            # [[sul, oeste], [norte, leste]].
            if not bounds_geom and len(bounds) == 2:
                south, west = bounds[0]
                north, east = bounds[1]
                bounds_geom = {
                    "type": "Polygon",
                    "coordinates": [[
                        [west, south],
                        [east, south],
                        [east, north],
                        [west, north],
                        [west, south],
                    ]]
                }
            else:
                # Fallback seguro
                bounds_geom = bounds_geom or {
                    "type": "Point",
                    "coordinates": [0, 0]
                }
            
            store.add_geotiff_metadata(
                file_id=file_id,
                filename=file.filename,
                metadata=metadata,
                bounds_geometry=bounds_geom,
                preview_path=str(preview.get("preview_url", "")),
            )
            
            # Mantém referência no _layers (compatibilidade com mapa)
            _layers[file_id] = {
                "path": path,
                "metadata": metadata,
                "preview": preview,
            }
        else:
            # Processa JSON/GeoJSON
            with open(dest, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            mode = "append" if concatenar else "replace"
            store.load(dest, mode=mode)
    
    except HTTPException:
        raise
    except (ValueError, Exception) as exc:
        detail = "Falha ao importar arquivo"
        if is_geotiff:
            detail = f"Falha ao processar GeoTIFF: {exc}"
        else:
            detail = f"Falha ao importar JSON/GeoJSON: {exc}"
        raise HTTPException(status_code=400, detail=detail) from exc
    
    return RedirectResponse("/", status_code=303)


@router.get("/records/new")
def new_form(request: Request):
    """Exibe o formulário para criar um registro."""
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
    """Cria um registro a partir do formulário e retorna à tabela."""
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
    """Exibe o formulário preenchido para editar o registro indicado."""
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
    """Valida e salva as alterações do registro indicado."""
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
    """Exclui o registro indicado e retorna à tabela."""
    if not store.delete(record_id):
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return RedirectResponse("/", status_code=303)


@router.get("/export")
def export_json():
    """Exporta os dados atuais como JSON ou GeoJSON para download."""
    if not store.records:
        raise HTTPException(status_code=400, detail="Nenhum dado importado para exportar")
    path = store.export()
    media_type = "application/geo+json" if store.source_format == "geojson" else "application/json"
    return FileResponse(path, filename=path.name, media_type=media_type)


@router.get("/export/csv")
def export_csv():
    """Exporta todos os registros atuais como arquivo CSV."""
    if not store.records:
        raise HTTPException(status_code=400, detail="Nenhum dado importado para exportar")

    fieldnames = [settings.id_field, *store.columns]
    if store.source_format == "geojson":
        fieldnames.append("geometry")
    if store.has_multiple_sources:
        fieldnames.append("source")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for record in store.get_all():
        row = dict(record)
        if store.source_format == "geojson":
            geometry = row.pop(store.GEOMETRY_FIELD, None)
            row["geometry"] = (
                json.dumps(geometry, ensure_ascii=False) if geometry is not None else ""
            )
        if store.has_multiple_sources:
            row["source"] = row.pop(store.SOURCE_FIELD, "")
        writer.writerow(row)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )