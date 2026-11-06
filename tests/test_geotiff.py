"""Testes da prévia raster e dos limites de GeoTIFF."""

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_bounds

from app.services.crud import store
from app.services.geotiff import TiffStore
import app.services.geotiff as geotiff_module


def test_generate_leaflet_preview_uses_public_url_palette_and_polygon(tmp_path, monkeypatch):
    """A prévia deve manter a paleta e fornecer limites para os dois mapas."""
    raster_path = tmp_path / "palette.tif"
    preview_dir = tmp_path / "previews"
    monkeypatch.setattr(geotiff_module, "PREVIEW_DIR", str(preview_dir))
    preview_dir.mkdir()

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_bounds(-50, -20, -40, -10, 2, 2),
    ) as dataset:
        dataset.write(np.array([[1, 2], [2, 1]], dtype=np.uint8), 1)
        dataset.write_colormap(1, {1: (255, 0, 0, 255), 2: (0, 0, 255, 255)})

    preview = TiffStore().generate_leaflet_preview(str(raster_path), "palette-preview")

    assert preview["preview_url"] == "/static/previews/palette-preview.png"
    assert preview["bounds"] == [[-20.0, -50.0], [-10.0, -40.0]]
    assert preview["bounds_geojson"]["coordinates"][0] == [
        [-50.0, -20.0],
        [-40.0, -20.0],
        [-40.0, -10.0],
        [-50.0, -10.0],
        [-50.0, -20.0],
    ]
    with Image.open(preview_dir / "palette-preview.png") as image:
        assert image.mode == "RGBA"
        assert set(image.getdata()) == {(255, 0, 0, 255), (0, 0, 255, 255)}


def test_geotiff_layer_exposes_raster_overlay_data():
    """A camada integrada deve fornecer URL e limites à sobreposição Leaflet."""
    bounds = {
        "type": "Polygon",
        "coordinates": [[
            [-50.0, -20.0],
            [-40.0, -20.0],
            [-40.0, -10.0],
            [-50.0, -10.0],
            [-50.0, -20.0],
        ]],
    }
    store.add_geotiff_metadata(
        file_id="raster-id",
        filename="palette.tif",
        metadata={},
        bounds_geometry=bounds,
        preview_path="/static/previews/raster-id.png",
    )

    layer = store.feature_collections_by_layer()[0]

    assert layer["raster"] == {
        "url": "/static/previews/raster-id.png",
        "bounds": [[-20.0, -50.0], [-10.0, -40.0]],
    }
