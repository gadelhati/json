"""Processa arquivos GeoTIFF e prepara metadados e prévias para o mapa."""

import os
os.environ.pop("PROJ_LIB", None)
os.environ.pop("PROJ_DATA", None)

import uuid
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image

UPLOAD_DIR = "uploads/geotiff"
PREVIEW_DIR = "static/previews"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

class TiffStore:
    """Salva GeoTIFFs e extrai informações para visualização geográfica."""

    def save_geotiff(self, file_bytes: bytes, filename: str) -> tuple[str, str]:
        """Salva o arquivo com um identificador único e retorna ID e caminho."""
        file_id = str(uuid.uuid4())
        path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
        with open(path, "wb") as f:
            f.write(file_bytes)
        return file_id, path

    def extract_geospatial_metadata(self, ds: rasterio.DatasetReader) -> dict:
        """Extrai CRS, transformação, limites, resolução e pontos de controle."""
        crs, transform = ds.crs, ds.transform
        gcps, _ = ds.get_gcps()
        return {
            "crs": crs.to_string() if crs else None,
            "epsg": crs.to_epsg() if crs else None,
            "wkt": crs.to_wkt() if crs else None,
            "transform": list(transform)[:6],
            "bounds": dict(zip(("left", "bottom", "right", "top"), ds.bounds)),
            "pixel_size": {"x": transform.a, "y": -transform.e},
            "width": ds.width,
            "height": ds.height,
            "gcps": [{"row": g.row, "col": g.col, "x": g.x, "y": g.y, "z": g.z} for g in (gcps or [])],
        }

    def extract_data_sensor_metadata(self, ds: rasterio.DatasetReader) -> dict:
        """Extrai informações, estatísticas e tags de cada banda e do sensor."""
        bands = []
        for i in range(1, ds.count + 1):
            arr = ds.read(i, masked=True)
            bands.append({
                "band": i,
                "dtype": str(ds.dtypes[i - 1]),
                "nodata": ds.nodatavals[i - 1],
                "color_interpretation": ds.colorinterp[i - 1].name,
                "description": ds.descriptions[i - 1],
                "stats": {
                    "min": float(arr.min()) if arr.count() else None,
                    "max": float(arr.max()) if arr.count() else None,
                    "mean": float(arr.mean()) if arr.count() else None,
                    "std": float(arr.std()) if arr.count() else None,
                },
            })
        sensor_keys = ("SATELLITE", "SENSOR", "INSTRUMENT", "ACQUISITIONDATETIME", "DATETIME")
        return {
            "band_count": ds.count,
            "bands": bands,
            "sensor_tags": {k: v for k, v in ds.tags().items() if k.upper() in sensor_keys},
        }

    def extract_descriptive_metadata(self, ds: rasterio.DatasetReader) -> dict:
        """Extrai metadados descritivos do GDAL e tags padrão do TIFF."""
        tags = ds.tags()
        return {
            "driver": ds.driver,
            "gdal_metadata": tags,
            "image_structure": ds.tags(ns="IMAGE_STRUCTURE"),
            "compression": ds.compression.name if ds.compression else None,
            "interleaving": ds.interleaving.name if ds.interleaving else None,
            "software": tags.get("TIFFTAG_SOFTWARE"),
            "datetime": tags.get("TIFFTAG_DATETIME"),
            "copyright": tags.get("TIFFTAG_COPYRIGHT"),
        }

    def extract_all_metadata(self, path: str) -> dict:
        """Agrupa metadados geoespaciais, de bandas e descritivos do arquivo."""
        with rasterio.open(path) as ds:
            return {
                "geoespacial": self.extract_geospatial_metadata(ds),
                "dados_sensores": self.extract_data_sensor_metadata(ds),
                "descritivo": self.extract_descriptive_metadata(ds),
            }

    def generate_leaflet_preview(self, path: str, file_id: str) -> dict:
        """Reprojeta o raster para EPSG:4326 e gera PNG e limites para o Leaflet.

        Retorna a URL da prévia e os limites no formato aceito por
        ``L.imageOverlay``.
        """
        dst_crs = "EPSG:4326"
        with rasterio.open(path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
            data = np.zeros((src.count, height, width), dtype=src.dtypes[0])
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i), destination=data[i - 1],
                    src_transform=src.transform, src_crs=src.crs,
                    dst_transform=transform, dst_crs=dst_crs,
                    resampling=Resampling.bilinear,
                )
            left, bottom, right, top = rasterio.transform.array_bounds(height, width, transform)

        rgb = np.stack([data[0]] * 3, axis=-1) if data.shape[0] < 3 else data[:3].transpose(1, 2, 0)
        rgb = rgb.astype(np.float32)
        for c in range(3):
            band = rgb[..., c]
            valid = band[band > 0]
            vmin, vmax = np.percentile(valid, (2, 98)) if valid.size else (0, 1)
            rgb[..., c] = np.clip((band - vmin) / (vmax - vmin + 1e-9), 0, 1) * 255

        preview_path = os.path.join(PREVIEW_DIR, f"{file_id}.png")
        Image.fromarray(rgb.astype(np.uint8), mode="RGB").save(preview_path)

        return {
            "preview_url": f"/static/previews/{file_id}.png",
            "bounds": [[bottom, left], [top, right]],
        }

store = TiffStore()