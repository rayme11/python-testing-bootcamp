# tests/test_products_api.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_rest_pagination_and_sorting():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products", params={"limit": 5, "skip": 0, "sort_by": "price", "order": "desc"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    if len(data) >= 2:
        assert data[0]["price"] >= data[-1]["price"]
