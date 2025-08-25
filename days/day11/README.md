# Day 11

Awesome — here’s a **fully detailed Day 11** that picks up exactly from Days 1–10 and introduces the **stable, production-like setup** we’ve been converging on: **lazy Mongo initialization**, **Strawberry context**, and **testing against a real Uvicorn server** to eliminate “event loop is closed” issues.

---

````markdown
# Day 11 – Stabilizing Async: Lazy Mongo Init + Strawberry Context + Real-Server Tests

Today we’ll harden our app so it behaves like a real service:
- No more flaky event loops during tests
- MongoDB connections created **on demand** (and reused)
- GraphQL resolvers get FastAPI’s **Request** via Strawberry **context**
- Tests call a **real** running server (not in-process), just like a client would

---

## 🎯 Goals

- Introduce **lazy Mongo initialization** using `app.state`.
- Provide Strawberry GraphQL resolvers access to `Request` (via `context_getter`).
- Replace brittle in-process testing with **real Uvicorn server tests**.
- Keep pagination/sorting primitives compatible with the new setup.

---

## 🛠 Step-by-step instructions

> Prereqs:
> - Your Codespace is running
> - `mongod` + `uvicorn` started (you can use `./scripts/start.sh`)
> - You have the structure from earlier days (src/, tests/, scripts/)

### 1) Replace `src/main.py` with a **lazy Mongo + Strawberry context** version

Create/overwrite `src/main.py` with:

```python
# src/main.py
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI()

# --- Lazy Mongo initializer ---
def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# --- Pydantic model for REST POST ---
class Product(BaseModel):
    name: str
    price: float

# --- Basic health route ---
@app.get("/")
def root():
    return {"message": "API is running"}

# --- REST: create + list with pagination/sorting (still work with lazy Mongo) ---
@app.post("/products")
async def create_product(product: Product, request: Request):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Product added", "id": str(result.inserted_id)}

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

    # Build dynamic query (compatible with Day 10)
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

# Optional helper to fetch an example product ID from REST
@app.get("/products/first-id")
async def first_product_id(request: Request):
    col = ensure_mongo(request)
    doc = await col.find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="No products")
    return {"id": str(doc["_id"]), "name": doc["name"], "price": doc["price"]}

# --- GraphQL types & schema ---
@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

# Strawberry context: carry FastAPI Request into resolvers
async def get_context(request: Request):
    return {"request": request}

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
        out: list[ProductType] = []
        cursor = col.find(query).skip(skip or 0).limit(limit or 100).sort(sort_by or "name", sort_dir)
        async for doc in cursor:
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> str:
        col = ensure_mongo(info.context["request"])
        await col.insert_one({"name": product.name, "price": float(product.price)})
        return f"Product '{product.name}' added."

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> str:
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await col.update_one({"_id": oid}, {"$set": {"name": product.name, "price": float(product.price)}})
        if result.matched_count == 0:
            return "Product not found."
        return "Product updated."

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> str:
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return "Product not found."
        return "Product deleted."

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
````

**Why this works:**

* `ensure_mongo(request)` lazily creates a Mongo client/db/collection on first use and stores them in `app.state`. Every later request reuses them.
* Strawberry’s `context_getter` injects the FastAPI `Request` so your resolvers can call `ensure_mongo(...)` too.
* REST and GraphQL share the same underlying collection.

---

### 2) Switch tests to hit the **real** server (not in-process)

This avoids ASGI loop conflicts and matches real-world I/O.

**Important:** Open a terminal and run the app first (or use your autostart script):

```bash
./scripts/start.sh
# or:
# mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Then, in a separate terminal, run tests that call `http://127.0.0.1:8000`.

#### `tests/test_products_api.py`

```python
# tests/test_products_api.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_create_product():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post("/products", json={"name": "Monitor", "price": 299.99})
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Product added"
    assert "id" in body

@pytest.mark.asyncio
async def test_list_products():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

#### `tests/test_graphql_api.py`

```python
# tests/test_graphql_api.py
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
    assert await wait_for_up(f"{BASE}/"), "API not reachable"
    q = 'mutation { addProduct(product: { name: "Keyboard", price: 49.99 }) }'
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text

@pytest.mark.asyncio
async def test_graphql_all_products_query():
    q = "{ allProducts { name price } }"
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
```

Run:

```bash
pytest -q
```

---

### 3) Keep Day 10 features working (filters/pagination/sorting)

We already merged the optional filter args into both REST and GraphQL in Step 1. Sanity test manually:

**REST:**

```bash
curl "http://127.0.0.1:8000/products?limit=5&skip=0&sort_by=price&order=desc"
```

**GraphQL:**

```bash
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ allProducts(limit:5, sortBy:\"price\", order:\"desc\") { name price } }"}'
```

---

## ✅ Summary (what you accomplished & learned)

* Implemented **lazy initialization** of MongoDB in `app.state`, removing noisy event loop errors and ensuring connections are reused correctly.
* Provided **Strawberry context** (`context_getter`) so GraphQL resolvers can access the FastAPI `Request` and use the same Mongo handle as REST endpoints.
* Switched tests to call a **real Uvicorn server** (via HTTP with `httpx.AsyncClient`), which is closer to production and avoids in-process ASGI pitfalls.
* Preserved and verified **pagination/sorting/filtering** features across REST and GraphQL.

> From here, your service behaves like a real app: stable startup, deterministic tests, and a clean async model that scales.

```

---

```

Run:
```bash
./scripts/start.sh
```
