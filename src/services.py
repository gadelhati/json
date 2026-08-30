import json
import uuid
from pathlib import Path
from typing import Any, Optional

from .config import settings


class JsonStore:
    """Guarda em memória os registros de um JSON importado, permitindo
    criar/ler/atualizar/remover registros antes de exportar o resultado."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.source_filename: Optional[str] = None

    def load(self, file_path: Path) -> None:
        """Importa um arquivo JSON. Aceita tanto um objeto único quanto uma lista de objetos."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("O JSON precisa ser um objeto ou uma lista de objetos (dicionários).")

        for item in data:
            item[settings.id_field] = str(item.get(settings.id_field, uuid.uuid4()))

        self.records = data
        self.source_filename = file_path.name

    @property
    def columns(self) -> list[str]:
        """Lista de colunas para exibição na tabela: união das chaves de todos os registros,
        com o campo de id sempre em primeiro lugar."""
        cols: list[str] = [settings.id_field]
        for record in self.records:
            for key in record:
                if key not in cols:
                    cols.append(key)
        return cols

    def get_all(self) -> list[dict[str, Any]]:
        return self.records

    def get(self, record_id: str) -> Optional[dict[str, Any]]:
        return next((r for r in self.records if r.get(settings.id_field) == record_id), None)

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
        """Exporta os registros atuais (com as edições aplicadas) para um novo arquivo JSON."""
        filename = filename or self.source_filename or "export.json"
        export_path = settings.export_dir / filename
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)
        return export_path


# Instância única (singleton simples) compartilhada por toda a aplicação.
store = JsonStore()