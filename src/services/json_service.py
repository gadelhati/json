"""
Serviço responsável pela leitura e gravação dos arquivos JSON.
"""

import json
from pathlib import Path


def load_json(file_path: Path):
    """
    Carrega um arquivo JSON e retorna seu conteúdo
    convertido para objetos Python.
    """

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(
    file_path: Path,
    data,
):
    """
    Salva os dados no arquivo JSON.
    """

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )