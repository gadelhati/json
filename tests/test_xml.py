"""Testes para importação, edição e exportação de XML."""

import xml.etree.ElementTree as ET
from pathlib import Path

from app.services.crud import store


def _import_xml(client, path, filename="livro.xml"):
    """Importa um arquivo XML de teste."""
    with open(path, "rb") as file:
        return client.post(
            "/import",
            data={"concatenar": False},
            files={"file": (filename, file, "application/xml")},
        )


def test_import_simple_xml_creates_editable_record(client, tmp_path):
    """Elementos filhos simples da raiz devem se tornar colunas editáveis."""
    xml_file = tmp_path / "livro.xml"
    xml_file.write_text(
        "<livro><titulo>Dominando XML</titulo><autor>Ana</autor></livro>",
        encoding="utf-8",
    )

    response = _import_xml(client, xml_file)

    assert response.status_code in [200, 303]
    assert store.source_format == "xml"
    assert store.records[0]["titulo"] == "Dominando XML"
    assert store.records[0]["autor"] == "Ana"
    page = client.get("/")
    assert "Dominando XML" in page.text
    assert "/export/xml" in page.text


def test_edit_and_export_simple_xml_preserves_structure(client, tmp_path):
    """A edição da tabela deve ser refletida no XML exportado."""
    xml_file = tmp_path / "livro.xml"
    xml_file.write_text(
        "<livro><titulo>Dominando XML</titulo><autor>Ana</autor></livro>",
        encoding="utf-8",
    )
    _import_xml(client, xml_file)
    record_id = store.records[0]["id"]

    update = client.post(
        f"/records/{record_id}/edit",
        data={"titulo": "XML Avançado", "autor": "Ana"},
        follow_redirects=False,
    )
    response = client.get("/export/xml")
    root = ET.fromstring(response.content)

    assert update.status_code == 303
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert root.tag == "livro"
    assert root.findtext("titulo") == "XML Avançado"
    assert root.findtext("autor") == "Ana"


def test_import_and_export_repeated_xml_records(client, tmp_path):
    """Uma coleção XML deve manter sua raiz e seus elementos de registro."""
    xml_file = tmp_path / "livros.xml"
    xml_file.write_text(
        "<livros><livro><titulo>Primeiro</titulo></livro>"
        "<livro><titulo>Segundo</titulo></livro></livros>",
        encoding="utf-8",
    )

    _import_xml(client, xml_file, "livros.xml")
    response = client.get("/export/xml")
    root = ET.fromstring(response.content)

    assert len(store.records) == 2
    assert root.tag == "livros"
    assert [element.findtext("titulo") for element in root.findall("livro")] == [
        "Primeiro",
        "Segundo",
    ]


def test_nested_xml_fields_are_editable_and_exported_with_hierarchy(client, tmp_path):
    """Caminhos aninhados devem editar e reconstruir a hierarquia XML."""
    xml_file = tmp_path / "pedido.xml"
    xml_file.write_text(
        "<pedido><cliente><nome>Ana</nome></cliente>"
        "<itens><item><descricao>Livro</descricao></item>"
        "<item><descricao>Caneta</descricao></item></itens></pedido>",
        encoding="utf-8",
    )
    _import_xml(client, xml_file, "pedido.xml")
    record = store.records[0]

    assert record["cliente.nome"] == "Ana"
    assert record["itens.item[1].descricao"] == "Livro"
    assert record["itens.item[2].descricao"] == "Caneta"

    response = client.post(
        f"/records/{record['id']}/edit",
        data={
            "cliente.nome": "Beatriz",
            "itens.item[1].descricao": "Livro revisado",
            "itens.item[2].descricao": "Caneta",
        },
        follow_redirects=False,
    )
    exported = ET.fromstring(client.get("/export/xml").content)

    assert response.status_code == 303
    assert exported.findtext("cliente/nome") == "Beatriz"
    assert [item.findtext("descricao") for item in exported.findall("itens/item")] == [
        "Livro revisado",
        "Caneta",
    ]


def test_reference_nfe_xml_imports_nested_paths(client):
    """A NF-e de referência deve manter dados e namespace após a exportação."""
    xml_file = Path(__file__).resolve().parents[1] / "references" / "xml.xml"
    _import_xml(client, xml_file, "nfe.xml")

    record = store.records[0]
    exported = ET.fromstring(client.get("/export/xml").content)
    namespace = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    assert record["NFe.infNFe.ide.cUF"] == "35"
    assert record["NFe.infNFe.det[1].prod.cProd"] == "B17025056"
    assert exported.tag == "{http://www.portalfiscal.inf.br/nfe}nfeProc"
    assert exported.findtext(".//nfe:ide/nfe:cUF", namespaces=namespace) == "35"


def test_invalid_xml_returns_client_error(client, tmp_path):
    """XML malformado deve retornar erro claro de importação."""
    xml_file = tmp_path / "invalido.xml"
    xml_file.write_text("<livro><titulo>Sem fechar</livro>", encoding="utf-8")

    response = _import_xml(client, xml_file, "invalido.xml")

    assert response.status_code == 400
    assert "XML inválido" in response.json()["detail"]
