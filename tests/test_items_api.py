from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_item():
    response = client.post("/items", json={
        "name": "Monitor",
        "price": 299.99
    })

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Item 'Monitor' added successfully."
    assert data["price"] == 299.99
