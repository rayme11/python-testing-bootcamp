import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_create_product():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post("/products", json={"name": "Monitor", "price": 299.99})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"] == "Product added"
    assert "id" in body

@pytest.mark.asyncio
async def test_list_products():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
