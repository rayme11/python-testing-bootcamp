import asyncio
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str, token: str | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query}, headers=headers)

async def wait_for_up(url: str, attempts: int = 30, delay: float = 0.2):
    async with AsyncClient(timeout=5.0) as ac:
        for _ in range(attempts):
            try:
                r = await ac.get(url)
                if r.status_code < 500:
                    return True
            except Exception:
                pass
            await asyncio.sleep(delay)
    return False

@pytest.mark.asyncio
async def test_graphql_add_product_mutation():
    assert await wait_for_up(f"{BASE}/"), "API not reachable"

    # Login to get token
    async with AsyncClient(base_url=BASE) as ac:
        login = await ac.post("/token", data={"username":"alice","password":"wonderland"})
        token = login.json()["access_token"]

    q = """
    mutation {
      addProduct(product: { name: "Keyboard", price: 49.99 }) {
        success
        message
      }
    }
    """
    r = await gql(q, token)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["data"]["addProduct"]["success"] is True

@pytest.mark.asyncio
async def test_graphql_all_products_query():
    q = """
    {
      allProducts {
        name
        price
      }
    }
    """
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert isinstance(payload["data"]["allProducts"], list)

@pytest.mark.asyncio
async def test_graphql_filter_by_name_and_price():
    q1 = """{ allProducts(nameContains: "Preloaded") { name price } }"""
    r1 = await gql(q1)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()["data"]["allProducts"]
    assert len(data1) >= 0
    if data1:
        assert all("Preloaded" in p["name"] for p in data1)

    q2 = """{ allProducts(minPrice: 10.0, maxPrice: 15.0) { name price } }"""
    r2 = await gql(q2)
    assert r2.status_code == 200, r2.text
    data2 = r2.json()["data"]["allProducts"]
    if data2:
        assert all(10.0 <= p["price"] <= 15.0 for p in data2)

@pytest.mark.asyncio
async def test_graphql_update_and_delete_product():
    # Login to get token
    async with AsyncClient(base_url=BASE) as ac:
        login = await ac.post("/token", data={"username":"alice","password":"wonderland"})
        token = login.json()["access_token"]

    # Create via REST to get ID
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        create = await ac.post("/products", json={"name": "TempProd", "price": 9.99})
    assert create.status_code == 200, create.text
    pid = create.json()["id"]

    update_q = f"""
    mutation {{
      updateProduct(id: "{pid}", product: {{ name: "UpdatedProd", price: 19.99 }}) {{
        success
        message
      }}
    }}
    """
    r1 = await gql(update_q, token)
    assert r1.status_code == 200, r1.text
    assert r1.json()["data"]["updateProduct"]["success"] is True

    delete_q = f"""
    mutation {{
      deleteProduct(id: "{pid}") {{
        success
        message
      }}
    }}
    """
    r2 = await gql(delete_q, token)
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"]["deleteProduct"]["success"] is True
