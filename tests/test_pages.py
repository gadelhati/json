
def test_home_page(client):
    """A página inicial deve responder corretamente."""
    response = client.get("/")
    assert response.status_code == 200

def test_import_page(client):
    """A página de importação deve ser exibida."""
    response = client.get("/import")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_unknown_route(client):
    """Uma rota inexistente deve retornar HTTP 404."""
    response = client.get("/__rota_inexistente__")
    assert response.status_code == 404
