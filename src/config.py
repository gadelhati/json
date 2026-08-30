from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação. Pode ser sobrescrita por variáveis de ambiente ou .env."""

    app_name: str = "JSON CRUD"
    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    export_dir: Path = Path("data/exports")
    # Nome do campo usado como identificador único de cada registro.
    # Se o JSON importado não tiver esse campo, ele é gerado automaticamente.
    id_field: str = "id"

    # extra="ignore": variáveis desconhecidas em .env (ex.: sobras de outro projeto)
    # são simplesmente ignoradas em vez de derrubar a aplicação.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Garante que os diretórios de trabalho existam antes de qualquer import/export.
for directory in (settings.data_dir, settings.upload_dir, settings.export_dir):
    directory.mkdir(parents=True, exist_ok=True)