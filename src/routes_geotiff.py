from fastapi import APIRouter, UploadFile, File, HTTPException
from .geotiff_service import store

routers_geotiff = APIRouter(prefix="/geotiff", tags=["geotiff"])
_layers: dict[str, dict] = {}

@routers_geotiff.post("/upload")
async def upload_geotiff(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(400, "Envie um arquivo .tif ou .tiff")

    file_bytes = await file.read()
    file_id, path = store.save_geotiff(file_bytes, file.filename)

    try:
        metadata = store.extract_all_metadata(path)
        preview = store.generate_leaflet_preview(path, file_id)
    except Exception as e:
        raise HTTPException(422, f"Falha ao processar GeoTIFF: {e}")

    _layers[file_id] = {"path": path, "metadata": metadata, "preview": preview}
    return {"id": file_id, **preview, "metadata": metadata}


@routers_geotiff.get("/{file_id}/metadata")
async def get_metadata(file_id: str):
    layer = _layers.get(file_id)
    if not layer:
        raise HTTPException(404, "Camada não encontrada")
    return layer["metadata"]