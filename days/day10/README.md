# Day 10

Awesome — let’s keep rolling! Here’s a **fully detailed Day 10** that builds directly on Days 1–9 (FastAPI + MongoDB + Strawberry GraphQL). Today we add **filtering & advanced queries** to both REST and GraphQL, with clear tests and curl examples.

---

````markdown
# Day 10 – Filtering & Advanced Queries (REST + GraphQL)

Welcome to **Day 10** of the Python Testing Bootcamp.

So far you have:
- FastAPI + MongoDB (Motor) with REST CRUD.
- Strawberry GraphQL with create/update/delete.
- Clean tests and fixtures.

Today we’ll add **filtering** to fetch only what you need:
- REST: `/products?name_contains=...&min_price=...&max_price=...`
- GraphQL: `allProducts(nameContains: "...", minPrice: ..., maxPrice: ...)`

We’ll also discuss **indexes** and **regex** in Mongo for efficient lookups.

---

## 🎯 Goals

- Implement **server-side filtering** for products:
  - Case-insensitive **name** contains
  - **min/max price** range
- Return consistent, predictable results
- Add **tests** that validate these behaviors
- Learn why **MongoDB indexes** matter (and how to add one)

---

## 📖 Theory – How Filtering Works

- **Name search:** We’ll use a `{ "$regex": ..., "$options": "i" }` query for case-insensitive substring matches in MongoDB.
- **Price range:** We’ll build a `{ "price": { "$gte": min, "$lte": max } }` filter only when provided.
- **Indexes:** Regex + unindexed fields can get slow for large data sets. Creating an index on `name` and `price` dramatically helps query performance.

> Tip: In production, consider **text indexes**, **prefix-only regex**, or **search services** (Atlas Search, OpenSearch, Meilisearch) for large-scale fuzzy search.

---

## 🛠 Step-by-step Instructions

> We’ll assume your `src/main.py` already has:
> - `ensure_mongo(request)` helper
> - REST `/products` endpoints
> - Strawberry `Query` / `Mutation` setup with GraphQL router

### 1) Add REST filtering parameters to `/products`

Open `src/main.py` and update the **list endpoint** to accept filters:

```python
# src/main.py (extend the existing list endpoint signature & logic)
from typing import Optional

@app.get("/products")
async def list_products(
    request: Request,
    limit: int = 100,
    skip: int = 0,
    sort_by: str = "name",
    order: str = "asc",
    name_contains: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    col = ensure_mongo(request)

    # Build dynamic query
    query: dict = {}
    if name_contains:
        query["name"] = {"$regex": name_contains, "$options": "i"}
    if min_price is not None or max_price is not None:
        price = {}
        if min_price is not None:
            price["$gte"] = float(min_price)
        if max_price is not None:
            price["$lte"] = float(max_price)
        query["price"] = price

    sort_dir = 1 if order.lower() == "asc" else -1

    items = []
    cursor = col.find(query).skip(skip).limit(limit).sort(sort_by, sort_dir)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items
````

Now you can filter via:

```
GET /products?name_contains=pro&min_price=10&max_price=50
```

---

### 2) Add GraphQL filters to `allProducts` query

Open the GraphQL `Query` type in `src/main.py` and extend `all_products`:

```python
# src/main.py – extend Strawberry Query (already present from Day 11/12)
@strawberry.type
class Query:
    @strawberry.field
    async def all_products(
        self,
        info,
        name_contains: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: Optional[int] = 100,
        skip: Optional[int] = 0,
        sort_by: Optional[str] = "name",
        order: Optional[str] = "asc",
    ) -> List[ProductType]:
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        query: dict = {}
        if name_contains:
            query["name"] = {"$regex": name_contains, "$options": "i"}
        if min_price is not None or max_price is not None:
            price = {}
            if min_price is not None:
                price["$gte"] = float(min_price)
            if max_price is not None:
                price["$lte"] = float(max_price)
            query["price"] = price

        sort_dir = 1 if (order or "asc").lower() == "asc" else -1

        results: list[ProductType] = []
        cursor = col.find(query).skip(skip or 0).limit(limit or 100).sort(sort_by or "name", sort_dir)
        async for doc in cursor:
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results
```

You can query like:

```graphql
{
  allProducts(nameContains: "load", minPrice: 10, maxPrice: 25, sortBy: "price", order: "asc") {
    name
    price
  }
}
```

> Note: Strawberry maps Python’s `name_contains` to GraphQL’s `nameContains` automatically (camelCase).

---

### 3) (Optional but recommended) Add MongoDB indexes

Add a tiny init step to ensure indexes exist (once). You can place this where you do other startup tasks (e.g., in `start.sh` or in an endpoint you run once):

```python
# src/main.py – optional helper to create indexes on name & price
@app.get("/admin/create-indexes")
async def create_indexes(request: Request):
    col = ensure_mongo(request)
    await col.create_index("name")
    await col.create_index("price")
    return {"message": "Indexes created"}
```

Call once:

```bash
curl -s http://127.0.0.1:8000/admin/create-indexes
```

---

### 4) Test filtering – REST

Create `tests/test_products_filters_rest.py`:

```python
# tests/test_products_filters_rest.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_rest_name_contains_filter():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        # Seed a few known products
        await ac.post("/products", json={"name": "Pro Keyboard", "price": 49.99})
        await ac.post("/products", json={"name": "Basic Keyboard", "price": 19.99})
        await ac.post("/products", json={"name": "Pro Mouse", "price": 39.99})

        # Filter by 'pro' (case-insensitive)
        r = await ac.get("/products", params={"name_contains": "pro", "sort_by": "name", "order": "asc"})
        assert r.status_code == 200
        names = [p["name"] for p in r.json()]
        # Should include both "Pro Keyboard" and "Pro Mouse"
        assert any("Pro Keyboard" == n for n in names)
        assert any("Pro Mouse" == n for n in names)
        # Should not include "Basic Keyboard" when filtering 'pro'
        assert not any("Basic Keyboard" == n for n in names)

@pytest.mark.asyncio
async def test_rest_price_range_filter():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        await ac.post("/products", json={"name": "Budget Stand", "price": 9.99})
        await ac.post("/products", json={"name": "Mid Stand", "price": 24.99})
        await ac.post("/products", json={"name": "Premium Stand", "price": 59.99})

        r = await ac.get("/products", params={"min_price": 10.0, "max_price": 30.0, "sort_by": "price", "order": "asc"})
        assert r.status_code == 200
        prices = [p["price"] for p in r.json()]
        assert all(10.0 <= float(x) <= 30.0 for x in prices)
        # The list should include 24.99 but not 9.99 or 59.99
        assert 24.99 in prices
        assert 9.99 not in prices and 59.99 not in prices
```

Run:

```bash
pytest -q
```

---

### 5) Test filtering – GraphQL

Create `tests/test_products_filters_graphql.py`:

```python
# tests/test_products_filters_graphql.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str):
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query})

@pytest.mark.asyncio
async def test_graphql_name_contains_filter():
    # Seed (via REST for simplicity)
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        await ac.post("/products", json={"name": "Preloaded Widget", "price": 12.5})
        await ac.post("/products", json={"name": "Another Widget", "price": 18.0})
        await ac.post("/products", json={"name": "Gadget", "price": 22.0})

    q = '{ allProducts(nameContains: "widget", sortBy: "name", order: "asc") { name price } }'
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
    data = payload["data"]["allProducts"]
    names = [p["name"] for p in data]
    assert "Preloaded Widget" in names
    assert "Another Widget" in names
    assert "Gadget" not in names

@pytest.mark.asyncio
async def test_graphql_price_range_filter():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        await ac.post("/products", json={"name": "Cheap Mat", "price": 5.0})
        await ac.post("/products", json={"name": "Desk Mat", "price": 25.0})
        await ac.post("/products", json={"name": "Luxury Mat", "price": 75.0})

    q = '{ allProducts(minPrice: 10, maxPrice: 30, sortBy: "price", order: "asc") { name price } }'
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
    data = payload["data"]["allProducts"]
    prices = [p["price"] for p in data]
    assert all(10.0 <= float(x) <= 30.0 for x in prices)
    assert 25.0 in prices
    assert 5.0 not in prices and 75.0 not in prices
```

Run:

```bash
pytest -q
```

---

### 6) Manual sanity via curl

**REST (name contains):**

```bash
curl "http://127.0.0.1:8000/products?name_contains=pro&sort_by=name&order=asc"
```

**REST (price range):**

```bash
curl "http://127.0.0.1:8000/products?min_price=10&max_price=30&sort_by=price&order=asc"
```

**GraphQL (name contains):**

```bash
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ allProducts(nameContains: \"widget\", sortBy:\"name\", order:\"asc\") { name price } }"}'
```

**GraphQL (price range):**

```bash
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ allProducts(minPrice:10, maxPrice:30, sortBy:\"price\", order:\"asc\") { name price } }"}'
```

---

## ✅ Summary (What you accomplished & learned)

* Added **filtering** to **REST** and **GraphQL**:

  * **Name substring** (case-insensitive)
  * **Price range** (`min`/`max`)
* Ensured **consistent sorting/pagination** behaviors continue to work harmoniously with filters.
* Wrote tests that:

  * Seed products
  * Query filtered results
  * Assert only the expected items are returned
* Understood why **indexes** matter and how to create them to keep filtered queries fast.

```

Run:
```bash
./scripts/start.sh
```
