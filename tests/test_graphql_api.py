import asyncio
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str):
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query})

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
    # ensure server is reachable (helps in CI/cold start)
    assert await wait_for_up(f"{BASE}/"), "API not reachable at /"

    q = """
    mutation {
      addProduct(product: { name: "Keyboard", price: 49.99 })
    }
    """
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
    assert "Keyboard" in r.text

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
    assert payload.get("data") is not None, r.text
    data = payload["data"]["allProducts"]
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_graphql_filter_by_name_and_price():
    q1 = """{ allProducts(nameContains: "Preloaded") { name price } }"""
    r1 = await gql(q1)
    assert r1.status_code == 200, r1.text
    p1 = r1.json()
    assert p1.get("data") is not None, r1.text
    data1 = p1["data"]["allProducts"]
    assert len(data1) > 0
    assert all("Preloaded" in p["name"] for p in data1)

    q2 = """{ allProducts(minPrice: 10.0, maxPrice: 15.0) { name price } }"""
    r2 = await gql(q2)
    assert r2.status_code == 200, r2.text
    p2 = r2.json()
    assert p2.get("data") is not None, r2.text
    data2 = p2["data"]["allProducts"]
    assert len(data2) > 0
    assert all(10.0 <= p["price"] <= 15.0 for p in data2)

@pytest.mark.asyncio
async def test_graphql_update_and_delete_product():
    # Create via REST to get a real ID
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        create = await ac.post("/products", json={"name": "TempProd", "price": 9.99})
    assert create.status_code == 200, create.text
    pid = create.json()["id"]

    update_q = f'''
    mutation {{
      updateProduct(id: "{pid}", product: {{ name: "UpdatedProd", price: 19.99 }})
    }}
    '''
    r1 = await gql(update_q)
    assert r1.status_code == 200, r1.text
    p1 = r1.json()
    assert p1.get("data") is not None, r1.text
    assert "Product updated" in r1.text

    delete_q = f'''mutation {{ deleteProduct(id: "{pid}") }}'''
    r2 = await gql(delete_q)
    assert r2.status_code == 200, r2.text
    p2 = r2.json()
    assert p2.get("data") is not None, r2.text
    assert "Product deleted" in r2.text
