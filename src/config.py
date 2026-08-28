"""
Configurações da aplicação.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_FOLDER = BASE_DIR / os.getenv(
    "UPLOAD_FOLDER",
    "uploads",
)

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)