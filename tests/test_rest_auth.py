# tests/test_rest_auth.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_secure_rest_with_valid_key():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post(
            "/secure/products",
            headers={"X-API-Key": "secret123"},
            json={"name": "SecureProd", "price": 5.5},
        )
    assert r.status_code == 200
    body = r.json()
    assert body.get("message") == "Secure product added"
    assert "id" in body

@pytest.mark.asyncio
async def test_secure_rest_missing_key():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post(
            "/secure/products",
            json={"name": "NoKey", "price": 1.0},
        )
    assert r.status_code == 403
    assert "Forbidden" in r.text
