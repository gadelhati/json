"""Testes para GeoJSON upload, CRUD e exportação."""

import json
import pytest
from app.services.crud import store


class TestGeoJsonWorkflow:
    """Testes para workflow completo com GeoJSON."""

    @pytest.fixture(autouse=True)
    def setup_geojson(self, client, geojson_file_with_data):
        """Carrega dados GeoJSON de exemplo."""
        with open(geojson_file_with_data, "rb") as f:
            client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("test.geojson", f, "application/json")},
            )

    def test_upload_geojson_creates_records(self, client):
        """Upload GeoJSON deve criar registros com geometria."""
        # Store já tem os dados carregados pela fixture
        assert len(store.records) == 2
        assert store.source_format == "geojson"

    def test_geojson_preserves_geometry(self, client):
        """Geometria GeoJSON deve estar no campo especial."""
        record = store.records[0]
        assert store.GEOMETRY_FIELD in record
        assert record[store.GEOMETRY_FIELD]["type"] == "Point"
        assert record[store.GEOMETRY_FIELD]["coordinates"] == [-73.9857, 40.7484]

    def test_geojson_preserves_properties(self, client):
        """Propriedades GeoJSON devem se tornar campos normais."""
        record = store.records[0]
        assert record["name"] == "Central Park"
        assert record["city"] == "New York"

    def test_export_geojson_format(self, client):
        """Exportação deve retornar GeoJSON válido."""
        response = client.get("/export")
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 2

        feature = data["features"][0]
        assert feature["type"] == "Feature"
        assert "geometry" in feature
        assert "properties" in feature

    def test_export_geojson_geometry_integrity(self, client):
        """Geometrias devem ser preservadas na exportação."""
        response = client.get("/export")
        data = json.loads(response.content)

        feature = data["features"][0]
        assert feature["geometry"]["coordinates"] == [-73.9857, 40.7484]

    def test_geojson_append_multiple_files(self, client, geojson_file_with_data, tmp_path):
        """Append de múltiplos arquivos GeoJSON deve concatenar."""
        initial_count = len(store.records)

        new_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"id": "3", "name": "New Location", "city": "Test"},
                }
            ],
        }
        geojson_file2 = tmp_path / "new.geojson"
        geojson_file2.write_text(json.dumps(new_geojson))

        with open(geojson_file2, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": True},
                files={"file": ("new.geojson", f, "application/json")},
            )
        assert response.status_code in [200, 303]
        assert len(store.records) == initial_count + 1

    def test_delete_source_removes_all_its_records_and_map_layer(self, client, tmp_path):
        """A exclusão de um arquivo remove seus registros da tabela e do mapa."""
        first_source_id = store.records[0][store.SOURCE_ID_FIELD]
        second_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"id": "3", "name": "Second source"},
            }],
        }
        second_file = tmp_path / "second.geojson"
        second_file.write_text(json.dumps(second_geojson), encoding="utf-8")
        with open(second_file, "rb") as file:
            client.post(
                "/import",
                data={"concatenar": True},
                files={"file": ("second.geojson", file, "application/geo+json")},
            )

        map_content = client.get("/map").text
        assert map_content.count('id="imported-files-title"') == 1
        assert map_content.count('class="layer-toggle"') == 2
        assert map_content.count("Excluir arquivo") == 2
        assert f"/sources/{first_source_id}/delete" in map_content

        response = client.post(f"/sources/{first_source_id}/delete", follow_redirects=False)

        assert response.status_code == 303
        assert len(store.records) == 1
        assert all(record[store.SOURCE_ID_FIELD] != first_source_id for record in store.records)
        assert [layer["name"] for layer in store.feature_collections_by_layer()] == ["second.geojson"]
        assert "test.geojson" not in client.get("/").text

    def test_delete_unknown_source_returns_404(self, client):
        """A exclusão deve informar quando a importação não existe."""
        response = client.post("/sources/inexistente/delete")
        assert response.status_code == 404


class TestGeoJsonValidation:
    """Testes para validação de estrutura GeoJSON."""

    def test_single_feature_upload(self, client, tmp_path):
        """Uma Feature única deve ser aceita."""
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"id": "1", "name": "Test"},
        }
        geojson_file = tmp_path / "single.geojson"
        geojson_file.write_text(json.dumps(feature))

        with open(geojson_file, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("single.geojson", f, "application/json")},
            )
        assert response.status_code in [200, 303]
        assert len(store.records) == 1

    def test_null_geometry_acceptance(self, client, tmp_path):
        """Feature com geometria null deve ser aceita."""
        feature = {
            "type": "Feature",
            "geometry": None,
            "properties": {"id": "1", "name": "No Location"},
        }
        geojson_file = tmp_path / "null_geom.geojson"
        geojson_file.write_text(json.dumps(feature))

        with open(geojson_file, "rb") as f:
            response = client.post(
                "/import",
                data={"concatenar": False},
                files={"file": ("null_geom.geojson", f, "application/json")},
            )
        assert response.status_code in [200, 303]
        assert len(store.records) == 1
