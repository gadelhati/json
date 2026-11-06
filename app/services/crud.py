"""Armazena, transforma e exporta registros JSON e GeoJSON em memória."""

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from app.config import settings


class JsonStore:
    """Guarda em memória os registros de um JSON (ou GeoJSON) importado, permitindo
    criar/ler/atualizar/remover registros antes de exportar o resultado.

    Em modo GeoJSON, cada registro corresponde a uma Feature: as chaves de
    'properties' viram colunas normais, e a geometria fica isolada no campo
    especial GEOMETRY_FIELD (editada como texto JSON no formulário).

    É possível importar múltiplos arquivos em sequência: por padrão cada
    importação substitui os dados atuais, mas usando modo "append" os
    registros do novo arquivo são concatenados aos já carregados (desde que
    ambos tenham o mesmo formato), permitindo depois exportar tudo junto em
    um único JSON/GeoJSON."""

    GEOMETRY_FIELD = "_geometry"
    SOURCE_FIELD = "_source"
    SOURCE_TYPE_FIELD = "_source_type"  # "json", "geojson" ou "geotiff"
    GEOTIFF_ID_FIELD = "_geotiff_id"
    GEOTIFF_PREVIEW_FIELD = "_geotiff_preview"

    def __init__(self) -> None:
        """Inicializa o armazenamento sem registros carregados."""
        self.records: list[dict[str, Any]] = []
        self.source_filenames: list[str] = []
        self.source_format: str = "json"  # "json" ou "geojson"
        self.geotiff_layers: dict[str, dict[str, Any]] = {}  # file_id -> {metadata, preview, bounds}

    @property
    def source_filename(self) -> Optional[str]:
        """Nome do arquivo mais recentemente importado (mantido por compatibilidade)."""
        return self.source_filenames[-1] if self.source_filenames else None

    def load(self, file_path: Path, mode: str = "replace") -> None:
        """Importa um arquivo JSON ou GeoJSON. O formato é detectado pelo conteúdo,
        não pela extensão do arquivo.

        mode="replace" (padrão): descarta os dados atuais e carrega só o novo arquivo.
        mode="append": concatena os registros do novo arquivo aos já carregados.
                       Só é permitido quando o novo arquivo tem o mesmo formato
                       dos dados já carregados (ambos "json" ou ambos "geojson");
                       caso contrário uma ValueError é lançada."""
        records, fmt = self._parse(file_path)

        if mode == "append" and self.records:
            if fmt != self.source_format:
                raise ValueError(
                    "Só é possível concatenar arquivos do mesmo formato "
                    f"(dados já carregados: {self.source_format}, novo arquivo: {fmt})."
                )
            existing_ids = {r.get(settings.id_field) for r in self.records}
            for record in records:
                # Evita colisão de id entre arquivos diferentes.
                if record.get(settings.id_field) in existing_ids:
                    record[settings.id_field] = str(uuid.uuid4())
                existing_ids.add(record.get(settings.id_field))
            self.records.extend(records)
            self.source_filenames.append(file_path.name)
        else:
            self.records = records
            self.source_format = fmt
            self.source_filenames = [file_path.name]

    def _parse(self, file_path: Path) -> tuple[list[dict[str, Any]], str]:
        """Lê e interpreta um arquivo, devolvendo (registros, formato) sem
        alterar o estado do store."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            records = self._features_to_records(data.get("features") or [])
            fmt = "geojson"
        elif isinstance(data, dict) and data.get("type") == "Feature":
            records = self._features_to_records([data])
            fmt = "geojson"
        else:
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                raise ValueError("O JSON precisa ser um objeto, uma lista de objetos, ou um GeoJSON válido.")
            for item in data:
                item.setdefault(settings.id_field, str(uuid.uuid4()))
            records = data
            fmt = "json"

        for record in records:
            record[self.SOURCE_FIELD] = file_path.name
        return records, fmt

    def _features_to_records(self, features: list[Any]) -> list[dict[str, Any]]:
        """Converte features GeoJSON em registros editáveis do armazenamento.

        A geometria e o identificador são preservados em campos próprios; as
        propriedades da feature permanecem disponíveis como colunas.
        """
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
        todos os registros (exceto id, geometria e arquivo de origem, tratados à
        parte), com o campo de id sempre em primeiro lugar."""
        cols: list[str] = []
        for record in self.records:
            for key in record:
                if key in (settings.id_field, self.GEOMETRY_FIELD, self.SOURCE_FIELD):
                    continue
                if key not in cols:
                    cols.append(key)
        return cols

    @property
    def has_multiple_sources(self) -> bool:
        """True quando os registros atuais vieram de mais de um arquivo importado
        (ou seja, quando houve concatenação)."""
        sources = {r.get(self.SOURCE_FIELD) for r in self.records if r.get(self.SOURCE_FIELD)}
        return len(sources) > 1

    def feature_collections_by_layer(self) -> list[dict[str, Any]]:
        """Agrupa os registros que têm geometria por arquivo de origem, devolvendo
        uma FeatureCollection por camada (uma por arquivo importado). Inclui camadas
        GeoTIFF. Usado para exibir as camadas no mapa, cada uma com sua própria cor."""
        layers = []

        # Camadas de GeoJSON
        if self.source_format == "geojson":
            grouped: dict[str, list[dict[str, Any]]] = {}
            for record in self.records:
                if record.get(self.SOURCE_TYPE_FIELD) == "geotiff":
                    continue  # GeoTIFF é tratado separadamente
                if record.get(self.GEOMETRY_FIELD) is None:
                    continue
                layer_name = record.get(self.SOURCE_FIELD) or "dados"
                grouped.setdefault(layer_name, []).append(record)

            for name, records in grouped.items():
                features = []
                for record in records:
                    properties = {
                        k: v for k, v in record.items()
                        if k not in (settings.id_field, self.GEOMETRY_FIELD, self.SOURCE_FIELD, self.SOURCE_TYPE_FIELD,
                                     self.GEOTIFF_ID_FIELD, self.GEOTIFF_PREVIEW_FIELD)
                    }
                    features.append({
                        "type": "Feature",
                        "id": record.get(settings.id_field),
                        "geometry": record.get(self.GEOMETRY_FIELD),
                        "properties": properties,
                    })
                layers.append({
                    "name": name,
                    "featureCollection": {"type": "FeatureCollection", "features": features},
                })

        # Camadas GeoTIFF (como limites)
        for record in self.records:
            if record.get(self.SOURCE_TYPE_FIELD) == "geotiff":
                layer_name = record.get(self.SOURCE_FIELD) or "GeoTIFF"
                features = [{
                    "type": "Feature",
                    "id": record.get(settings.id_field),
                    "geometry": record.get(self.GEOMETRY_FIELD),
                    "properties": {
                        "tipo": "GeoTIFF",
                        "crs": record.get("crs"),
                        "preview": record.get(self.GEOTIFF_PREVIEW_FIELD),
                    }
                }]
                layer = {
                    "name": layer_name,
                    "featureCollection": {"type": "FeatureCollection", "features": features},
                }
                geometry = record.get(self.GEOMETRY_FIELD)
                coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
                ring = coordinates[0] if isinstance(coordinates, list) and coordinates else None
                if (
                    isinstance(ring, list)
                    and len(ring) >= 3
                    and all(isinstance(point, list) and len(point) >= 2 for point in (ring[0], ring[2]))
                ):
                    layer["raster"] = {
                        "url": record.get(self.GEOTIFF_PREVIEW_FIELD),
                        "bounds": [
                            [
                                ring[0][1],
                                ring[0][0],
                            ],
                            [
                                ring[2][1],
                                ring[2][0],
                            ],
                        ],
                    }
                layers.append(layer)

        return layers

    def get_all(self) -> list[dict[str, Any]]:
        """Retorna a lista atual de registros."""
        return self.records

    def get(self, record_id: str) -> Optional[dict[str, Any]]:
        """Busca um registro pelo campo configurado como identificador."""
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
        """Adiciona um registro e gera um identificador quando necessário."""
        data.setdefault(settings.id_field, str(uuid.uuid4()))
        data.setdefault(self.SOURCE_TYPE_FIELD, "json" if self.source_format == "json" else "geojson")
        self.records.append(data)
        return data

    def add_geotiff_metadata(
        self,
        file_id: str,
        filename: str,
        metadata: dict[str, Any],
        bounds_geometry: dict[str, Any],
        preview_path: str,
    ) -> dict[str, Any]:
        """Adiciona um registro GeoTIFF com seus metadados e geometria de limites.
        
        Cria um registro que aparece na tabela com os metadados extraídos do GeoTIFF.
        A geometria do registro é os limites do raster (bbox em EPSG:4326).
        
        Retorna o registro criado."""
        # Extrai transformação com segurança
        geo_info = metadata.get("geo", {})
        transform = geo_info.get("transform", [None] * 6)
        resolucao_x = transform[1] if len(transform) > 1 else None
        resolucao_y = transform[5] if len(transform) > 5 else None
        
        # Extrai bounds com segurança
        bounds_info = geo_info.get("bounds", {})
        min_val = bounds_info.get("min")
        max_val = bounds_info.get("max")
        
        record = {
            settings.id_field: file_id,
            self.SOURCE_FIELD: filename,
            self.SOURCE_TYPE_FIELD: "geotiff",
            self.GEOMETRY_FIELD: bounds_geometry,
            self.GEOTIFF_ID_FIELD: file_id,
            self.GEOTIFF_PREVIEW_FIELD: preview_path,
            "crs": geo_info.get("crs"),
            "resolucao_x": resolucao_x,
            "resolucao_y": resolucao_y,
            "bandas": len(metadata.get("bands", [])),
            "min": min_val,
            "max": max_val,
        }
        
        # Adiciona metadados de bandas (se houver)
        for i, band in enumerate(metadata.get("bands", []), 1):
            if isinstance(band, dict) and band.get("statistics"):
                stats = band["statistics"]
                record[f"banda_{i}_media"] = stats.get("mean")
                record[f"banda_{i}_min"] = stats.get("min")
                record[f"banda_{i}_max"] = stats.get("max")
        
        self.records.append(record)
        self.geotiff_layers[file_id] = {
            "metadata": metadata,
            "preview": preview_path,
            "bounds": bounds_geometry,
        }
        return record

    def update(self, record_id: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Atualiza um registro existente e retorna-o, ou retorna ``None``."""
        record = self.get(record_id)
        if record is None:
            return None
        data[settings.id_field] = record_id
        record.update(data)
        return record

    def delete(self, record_id: str) -> bool:
        """Remove um registro pelo identificador e informa se foi encontrado."""
        record = self.get(record_id)
        if record is None:
            return False
        self.records.remove(record)
        return True

    def export(self, filename: Optional[str] = None) -> Path:
        """Exporta os registros atuais (com as edições aplicadas). Em modo GeoJSON,
        reconstrói uma FeatureCollection válida (com as features de todos os
        arquivos concatenados); caso contrário, exporta a lista de objetos."""
        default_name = "export.geojson" if self.source_format == "geojson" else "export.json"
        # Quando os dados vieram de mais de um arquivo (concatenação), usa um nome
        # genérico em vez do nome do último arquivo importado, para não sugerir
        # que o export contém apenas aquele arquivo.
        if filename is None:
            filename = default_name if len(self.source_filenames) != 1 else self.source_filenames[0]
        export_path = settings.export_dir / filename

        if self.source_format == "geojson":
            features = []
            for record in self.records:
                properties = {
                    k: v for k, v in record.items()
                    if k not in (settings.id_field, self.GEOMETRY_FIELD, self.SOURCE_FIELD)
                }
                features.append({
                    "type": "Feature",
                    "id": record.get(settings.id_field),
                    "geometry": record.get(self.GEOMETRY_FIELD),
                    "properties": properties,
                })
            payload: Any = {"type": "FeatureCollection", "features": features}
        else:
            payload = [
                {k: v for k, v in record.items() if k != self.SOURCE_FIELD}
                for record in self.records
            ]

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return export_path


# Instância única (singleton simples) compartilhada por toda a aplicação.
store = JsonStore()