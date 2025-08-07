import pytest
import httpx

@pytest.mark.asyncio
async def test_create_product():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/products", json={
            "name": "Monitor",
            "price": 299.99
        })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Product added"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_products():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
