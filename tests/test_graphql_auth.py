# tests/test_graphql_auth.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str, headers=None):
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query}, headers=headers or {})

@pytest.mark.asyncio
async def test_graphql_secret_with_valid_bearer():
    q = "{ secretProducts { name price } }"
    r = await gql(q, headers={"Authorization": "Bearer bearer-abc-123"})
    assert r.status_code == 200
    payload = r.json()
    assert "data" in payload and "secretProducts" in payload["data"]

@pytest.mark.asyncio
async def test_graphql_secret_invalid_bearer():
    q = "{ secretProducts { name price } }"
    r = await gql(q, headers={"Authorization": "Bearer wrong-token"})
    # Strawberry returns 200 with "errors" array on GraphQL errors
    assert r.status_code == 200
    payload = r.json()
    assert "errors" in payload
    assert "Invalid Bearer token" in str(payload["errors"][0]["message"])
