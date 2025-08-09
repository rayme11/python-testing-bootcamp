# tests/test_products_api.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_product():
    response = client.post("/products", json={"name": "Monitor", "price": 299.99})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Product added"
    assert "id" in data

def test_list_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
