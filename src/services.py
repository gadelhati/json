import json
import uuid
from pathlib import Path
from typing import Any, Optional

from .config import settings


class JsonStore:
    """Guarda em memória os registros de um JSON (ou GeoJSON) importado, permitindo
    criar/ler/atualizar/remover registros antes de exportar o resultado.

    Em modo GeoJSON, cada registro corresponde a uma Feature: as chaves de
    'properties' viram colunas normais, e a geometria fica isolada no campo
    especial GEOMETRY_FIELD (editada como texto JSON no formulário)."""

    GEOMETRY_FIELD = "_geometry"

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.source_filename: Optional[str] = None
        self.source_format: str = "json"  # "json" ou "geojson"

    def load(self, file_path: Path) -> None:
        """Importa um arquivo JSON ou GeoJSON. O formato é detectado pelo conteúdo,
        não pela extensão do arquivo."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            self.records = self._features_to_records(data.get("features") or [])
            self.source_format = "geojson"
        elif isinstance(data, dict) and data.get("type") == "Feature":
            self.records = self._features_to_records([data])
            self.source_format = "geojson"
        else:
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                raise ValueError("O JSON precisa ser um objeto, uma lista de objetos, ou um GeoJSON válido.")
            for item in data:
                item.setdefault(settings.id_field, str(uuid.uuid4()))
            self.records = data
            self.source_format = "json"

        self.source_filename = file_path.name

    def _features_to_records(self, features: list[Any]) -> list[dict[str, Any]]:
        records = []
        for feature in features:
            if not isinstance(feature, dict):
                raise ValueError("Cada 'feature' do GeoJSON precisa ser um objeto.")
            record = dict(feature.get("properties") or {})
            record[self.GEOMETRY_FIELD] = feature.get("geometry")
            record.setdefault(settings.id_field, feature.get("id") or str(uuid.uuid4()))
            records.append(record)
        return records

    @property
    def columns(self) -> list[str]:
        """Lista de colunas 'normais' para exibição na tabela: união das chaves de
        todos os registros (exceto id e geometria, tratados à parte), com o
        campo de id sempre em primeiro lugar."""
        cols: list[str] = [settings.id_field]
        for record in self.records:
            for key in record:
                if key in (settings.id_field, self.GEOMETRY_FIELD):
                    continue
                if key not in cols:
                    cols.append(key)
        return cols

    def get_all(self) -> list[dict[str, Any]]:
        return self.records

    def get(self, record_id: str) -> Optional[dict[str, Any]]:
        return next((r for r in self.records if r.get(settings.id_field) == record_id), None)

    def prepare_incoming(self, data: dict[str, Any]) -> dict[str, Any]:
        """Converte os dados brutos vindos do formulário antes de create/update.
        Em modo GeoJSON, o campo de geometria chega como texto e precisa virar objeto.
        Lança json.JSONDecodeError se o texto não for um JSON válido."""
        data = dict(data)
        if self.source_format == "geojson" and self.GEOMETRY_FIELD in data:
            raw_geom = data[self.GEOMETRY_FIELD]
            if isinstance(raw_geom, str):
                raw_geom = raw_geom.strip()
                data[self.GEOMETRY_FIELD] = json.loads(raw_geom) if raw_geom else None
        return data

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        data.setdefault(settings.id_field, str(uuid.uuid4()))
        self.records.append(data)
        return data

    def update(self, record_id: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        record = self.get(record_id)
        if record is None:
            return None
        data[settings.id_field] = record_id
        record.update(data)
        return record

    def delete(self, record_id: str) -> bool:
        record = self.get(record_id)
        if record is None:
            return False
        self.records.remove(record)
        return True

    def export(self, filename: Optional[str] = None) -> Path:
        """Exporta os registros atuais (com as edições aplicadas). Em modo GeoJSON,
        reconstrói uma FeatureCollection válida; caso contrário, exporta a lista de objetos."""
        default_name = "export.geojson" if self.source_format == "geojson" else "export.json"
        filename = filename or self.source_filename or default_name
        export_path = settings.export_dir / filename

        if self.source_format == "geojson":
            features = []
            for record in self.records:
                properties = {
                    k: v for k, v in record.items()
                    if k not in (settings.id_field, self.GEOMETRY_FIELD)
                }
                features.append({
                    "type": "Feature",
                    "id": record.get(settings.id_field),
                    "geometry": record.get(self.GEOMETRY_FIELD),
                    "properties": properties,
                })
            payload: Any = {"type": "FeatureCollection", "features": features}
        else:
            payload = self.records

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return export_path


# Instância única (singleton simples) compartilhada por toda a aplicação.
store = JsonStore()