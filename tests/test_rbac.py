# description: login as admin, create product via REST admin route, OK
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def _login(username: str, password: str) -> str:
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post("/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_admin_can_create_product_rest():
    token = await _login("alice", "wonderland")  # alice is admin from Day 16
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post(
            "/admin/products",
            json={"name": "RBAC-Monitor", "price": 123.45},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["message"] == "Product added"
    assert "id" in body

# description: login as user, attempt admin route, expect 403
@pytest.mark.asyncio
async def test_user_cannot_create_product_rest():
    token = await _login("bob", "builder")  # bob is user
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post(
            "/admin/products",
            json={"name": "Should-Fail", "price": 10.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 403

# description: GraphQL addProduct requires admin; user gets Forbidden
@pytest.mark.asyncio
async def test_graphql_add_product_forbidden_for_user():
    token = await _login("bob", "builder")
    q = """
    mutation {
      addProduct(product: { name: "GQL-User-Forbidden", price: 9.99 }) {
        success
        message
        id
      }
    }
    """
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        r = await ac.post("/graphql", json={"query": q}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    payload = r.json()
    data = payload.get("data", {}).get("addProduct")
    assert data is not None
    assert data["success"] is False
    assert "Forbidden" in data["message"]

# description: GraphQL addProduct works with admin
@pytest.mark.asyncio
async def test_graphql_add_product_allowed_for_admin():
    token = await _login("alice", "wonderland")
    q = """
    mutation {
      addProduct(product: { name: "GQL-Admin-OK", price: 49.99 }) {
        success
        message
        id
      }
    }
    """
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        r = await ac.post("/graphql", json={"query": q}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    payload = r.json()
    data = payload.get("data", {}).get("addProduct")
    assert data is not None
    assert data["success"] is True
    assert data["id"] is not None
