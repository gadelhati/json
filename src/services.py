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
    especial GEOMETRY_FIELD (editada como texto JSON no formulário).

    É possível importar múltiplos arquivos em sequência: por padrão cada
    importação substitui os dados atuais, mas usando modo "append" os
    registros do novo arquivo são concatenados aos já carregados (desde que
    ambos tenham o mesmo formato), permitindo depois exportar tudo junto em
    um único JSON/GeoJSON."""

    GEOMETRY_FIELD = "_geometry"
    SOURCE_FIELD = "_source"

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.source_filenames: list[str] = []
        self.source_format: str = "json"  # "json" ou "geojson"

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
        cols: list[str] = [settings.id_field]
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