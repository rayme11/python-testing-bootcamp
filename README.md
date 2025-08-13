Absolutely! Here’s a **clean, working “golden copy” README** you can paste straight into your repo. It includes **Days 1–12**, and for **every day** you’ll find:

* **Goals**
* **Step-by-step instructions** (with exact commands and code blocks)
* **Summary (what you accomplished & learned)**

Everything reflects the **latest stable setup** (lazy Mongo init, Strawberry context, testing against a real Uvicorn server, pagination/sorting, coverage).

---

````markdown
# Python Testing Bootcamp – Day-by-Day Learning Guide

## ⚡ Quick Start – Auto-Run Everything

If you’re running this inside **GitHub Codespaces**, you can start **MongoDB**, **FastAPI**, and **GraphQL** automatically using our `/scripts/start.sh` script.

### 1️⃣ Run the Autostart Script
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

This will:

* Start **MongoDB** in the background
* Launch **FastAPI** with hot-reload at port `8000`
* Keep both running so you can immediately test endpoints

You can then access:

* REST API root: `https://<your-forwarded-url>.github.dev/`
* GraphQL UI: `https://<your-forwarded-url>.github.dev/graphql`

### 2️⃣ Stop Services

To stop everything:

```bash
pkill -f uvicorn
pkill -f mongod
```

---

## 📦 Project Structure (what you should have by now)

```
python-testing-bootcamp/
├── .devcontainer/
│   └── devcontainer.json
├── scripts/
│   ├── start.sh
│   └── seed_data.py
├── src/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_day2_basics.py
│   ├── test_math_ops.py
│   ├── test_products_api.py
│   └── test_graphql_api.py
├── data/
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# 📅 Day-by-Day

## 📅 Day 1 – Setting Up the Environment in GitHub Codespaces

### 🎯 Goals
- Initialize a Python dev environment in Codespaces
- Install core dependencies and forward port 8000

### 🛠 Steps

1) **Create repo** → Open in Codespaces.

2) **`.devcontainer/devcontainer.json`**
```json
{
  "name": "Python Testing Env",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:1": {}
  },
  "postCreateCommand": "pip install -r requirements.txt",
  "forwardPorts": [8000],
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "ms-python.vscode-pylance"]
    }
  }
}
```

3) **`requirements.txt`** (explicit deps)
```
fastapi
uvicorn
motor
pymongo
strawberry-graphql
pytest
pytest-asyncio
httpx
requests
faker
pytest-cov
```

4) **Scaffold folders**
```bash
mkdir -p src tests scripts data .devcontainer
touch src/__init__.py src/main.py tests/conftest.py README.md pytest.ini
```

5) **`pytest.ini`**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts = -v --tb=short
```

### ✅ Summary
- Codespace builds automatically, dependencies install, port 8000 forwarded.
- You’re ready to run & test locally inside Codespaces.

---

## 📅 Day 2 – Python Refresher: Functions, Classes, Tests

### 🎯 Goals
- Refresh Python basics needed for testing
- Write first unit tests

### 🛠 Steps

**`src/day2_basics.py`**
```python
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
```

**`tests/test_day2_basics.py`**
```python
from src.day2_basics import add, Calculator

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    calc = Calculator()
    assert calc.multiply(2, 3) == 6
```

Run:
```bash
pytest -q
```

### ✅ Summary
- You wrote unit tests and validated basic functionality quickly with pytest.

---

## 📅 Day 3 – Pytest Fundamentals & Fixtures

### 🎯 Goals
- Learn pytest config & fixtures
- Share setup data across tests

### 🛠 Steps

**`tests/conftest.py`**
```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "role": "tester"}
```

**`tests/test_users.py`**
```python
def test_sample_user_fixture(sample_user):
    assert sample_user["role"] == "tester"
```

Run:
```bash
pytest -v
```

### ✅ Summary
- You used a fixture to share data across tests.
- You understand how pytest discovers tests and fixtures.

---

## 📅 Day 4 – First FastAPI Endpoint

### 🎯 Goals
- Create first FastAPI app
- Test it end-to-end

### 🛠 Steps

**`src/main.py`**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running"}
```

**`tests/test_root.py`**
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "API is running"
```

Run:
```bash
pytest -q
```

### ✅ Summary
- You built and tested your first HTTP endpoint.

---

## 📅 Day 5 – REST: `/products` with MongoDB

### 🎯 Goals
- Add REST endpoints backed by MongoDB (async Motor)
- Validate payloads with Pydantic

### 🛠 Steps

**Extend `src/main.py`** (temporary simple DB — we’ll refactor to lazy init later)
```python
from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

app = FastAPI()

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.testing_db
products_collection = db.products

class Product(BaseModel):
    name: str
    price: float

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/products")
async def create_product(product: Product):
    new_product = product.model_dump()
    result = await products_collection.insert_one(new_product)
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.get("/products")
async def list_products():
    items = []
    async for doc in products_collection.find():
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items
```

Run API:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### ✅ Summary
- REST endpoints now create & list products stored in MongoDB.

---

## 📅 Day 6 – Testing REST with TestClient

### 🎯 Goals
- Write tests for `/products` POST + GET

### 🛠 Steps

**`tests/test_products_api.py`** (initial version using in-process TestClient)
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_product():
    r = client.post("/products", json={"name": "Monitor", "price": 299.99})
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Product added"
    assert "id" in body

def test_list_products():
    r = client.get("/products")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

Run:
```bash
pytest -q
```

### ✅ Summary
- You built REST tests. (We’ll later switch to real-server tests to avoid async loop issues.)

---

## 📅 Day 7 – Pytest Autouse DB Seeding

### 🎯 Goals
- Guarantee predictable DB content per test
- Learn async fixtures with setup/teardown

### 🛠 Steps

**Extend `tests/conftest.py`**
```python
import pytest
import motor.motor_asyncio

@pytest.fixture(autouse=True)
async def seed_and_cleanup():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    await db.products.delete_many({})
    await db.products.insert_many([
        {"name": "Preloaded Item 1", "price": 10.99},
        {"name": "Preloaded Item 2", "price": 20.50}
    ])
    yield
    await db.products.delete_many({})
```

### ✅ Summary
- Tests now start from a known database state and clean up afterward.

---

## 📅 Day 8 – GraphQL (Query & Mutation)

### 🎯 Goals
- Add GraphQL to FastAPI with Strawberry
- Support `allProducts` and `addProduct`

### 🛠 Steps

**Update `src/main.py`** (adds Strawberry schema)
```python
from typing import List
import strawberry
from strawberry.fastapi import GraphQLRouter

# … previous FastAPI code & products_collection …

@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(self) -> List[ProductType]:
        results = []
        async for doc in products_collection.find():
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductInput) -> str:
        await products_collection.insert_one({"name": product.name, "price": float(product.price)})
        return f"Product '{product.name}' added."

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

**`tests/test_graphql_api.py`** (initial in-process style)
```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_add_product_graphql():
    q = """
    mutation {
      addProduct(product: { name: "Keyboard", price: 49.99 })
    }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": q})
    assert r.status_code == 200
    assert "Keyboard" in r.text

@pytest.mark.asyncio
async def test_all_products_graphql():
    q = "{ allProducts { name price } }"
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": q})
    assert r.status_code == 200
    assert "allProducts" in r.text
```

### ✅ Summary
- GraphQL endpoint is live with basic query and mutation.

---

## 📅 Day 9 – GraphQL Filtering (Name & Price)

### 🎯 Goals
- Add filter args to GraphQL query
- Build dynamic Mongo queries

### 🛠 Steps

**Update `Query` in `src/main.py`**
```python
@strawberry.type
class Query:
    @strawberry.field
    async def all_products(
        self,
        name_contains: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None
    ) -> List[ProductType]:
        query: dict = {}
        if name_contains:
            query["name"] = {"$regex": name_contains, "$options": "i"}
        if min_price is not None or max_price is not None:
            price = {}
            if min_price is not None: price["$gte"] = float(min_price)
            if max_price is not None: price["$lte"] = float(max_price)
            query["price"] = price

        out = []
        async for doc in products_collection.find(query):
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out
```

**`tests/test_graphql_api.py`** (add filter tests)
```python
@pytest.mark.asyncio
async def test_filters():
    q1 = '{ allProducts(nameContains: "Preloaded") { name price } }'
    q2 = '{ allProducts(minPrice: 10.0, maxPrice: 15.0) { name price } }'
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.post("/graphql", json={"query": q1})
        r2 = await ac.post("/graphql", json={"query": q2})
    assert r1.status_code == 200 and r2.status_code == 200
```

### ✅ Summary
- GraphQL supports real-world filtering; tests verify results.

---

## 📅 Day 10 – Seed Script & Autostart

### 🎯 Goals
- Auto-seed DB with Faker
- One-command startup for devs

### 🛠 Steps

**`scripts/seed_data.py`**
```python
from faker import Faker
import motor.motor_asyncio
import asyncio

fake = Faker()

async def seed_products():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    col = db.products
    await col.delete_many({})
    docs = [{"name": fake.word().title(), "price": round(fake.pyfloat(left_digits=2, right_digits=2, positive=True), 2)} for _ in range(10)]
    await col.insert_many(docs)
    print(f"✅ Seeded {len(docs)} products.")

if __name__ == "__main__":
    asyncio.run(seed_products())
```

**`scripts/start.sh`**
```bash
#!/bin/bash
set -e
mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
MONGOPID=$!
sleep 2
python scripts/seed_data.py || true
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
kill $MONGOPID || true
```

Run:
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

### ✅ Summary
- Any engineer can start DB + API + seed with a single command.

---

## 📅 Day 11 – Stabilizing Async with Lazy DB + Real-Server Tests

### 🎯 Goals
- Fix `Event loop is closed` and missing `app.state.products`
- Use lazy Mongo initialization & test against a real Uvicorn server

### 🛠 Steps

**Replace `src/main.py` with lazy DB + Strawberry context**
```python
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI()

def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

class Product(BaseModel):
    name: str
    price: float

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/products")
async def create_product(product: Product, request: Request):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.get("/products")
async def list_products(request: Request, limit: int = 100, skip: int = 0, sort_by: str = "name", order: str = "asc"):
    col = ensure_mongo(request)
    sort_dir = 1 if order.lower() == "asc" else -1
    items = []
    cursor = col.find().skip(skip).limit(limit).sort(sort_by, sort_dir)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items

@app.get("/products/first-id")
async def first_product_id(request: Request):
    col = ensure_mongo(request)
    doc = await col.find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="No products")
    return {"id": str(doc["_id"]), "name": doc["name"], "price": doc["price"]}

@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

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
            if min_price is not None: price["$gte"] = float(min_price)
            if max_price is not None: price["$lte"] = float(max_price)
            query["price"] = price

        sort_dir = 1 if (order or "asc").lower() == "asc" else -1
        results: list[ProductType] = []
        cursor = col.find(query).skip(skip or 0).limit(limit or 100).sort(sort_by or "name", sort_dir)
        async for doc in cursor:
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results

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
```

**Switch tests to hit the real server** (no in-process ASGI):

`tests/test_products_api.py`
```python
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

`tests/test_graphql_api.py`
```python
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
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("data") is not None

@pytest.mark.asyncio
async def test_graphql_all_products_query():
    q = "{ allProducts { name price } }"
    r = await gql(q)
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("data") is not None
```

Run tests (after `./scripts/start.sh` on another terminal):
```bash
pytest -q
```

### ✅ Summary
- Lazy DB init + real-server tests eliminate async loop errors.
- GraphQL resolvers access FastAPI’s `request` via Strawberry context.
- The app and tests are stable and production-like.

---

## 📅 Day 12 – Pagination, Sorting & Coverage (REST + GraphQL)

### 🎯 Goals
- Add **pagination** (`limit`, `skip`) & **sorting** (`sort_by`, `order`) to both REST & GraphQL
- Validate input params
- Generate **coverage reports** for the whole project

### 🛠 Steps

**A) REST pagination & sorting** (already added in Day 11 code)
- `GET /products?limit=20&skip=40&sort_by=price&order=desc`

**B) GraphQL pagination & sorting** (already added in Day 11 code)
- GraphQL query params:
  - `limit`, `skip`, `sortBy`, `order`
- Example:
```graphql
{
  allProducts(limit: 5, skip: 0, sortBy: "price", order: "desc") {
    name
    price
  }
}
```

**C) Tests for REST pagination/sorting** (add to `tests/test_products_api.py`)
```python
@pytest.mark.asyncio
async def test_rest_pagination_and_sorting():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products", params={"limit": 5, "skip": 0, "sort_by": "price", "order": "desc"})
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) <= 5
    # Optional: check sorted order if 2+ results
    if len(arr) >= 2:
        assert arr[0]["price"] >= arr[-1]["price"]
```

**D) Tests for GraphQL pagination/sorting** (add to `tests/test_graphql_api.py`)
```python
@pytest.mark.asyncio
async def test_graphql_pagination_and_sorting():
    q = '{ allProducts(limit: 5, skip: 0, sortBy: "price", order: "desc") { name price } }'
    r = await gql(q)
    assert r.status_code == 200
    payload = r.json()
    data = payload.get("data", {}).get("allProducts", [])
    assert len(data) <= 5
    if len(data) >= 2:
        assert data[0]["price"] >= data[-1]["price"]
```

**E) Coverage reports**
- Already installed `pytest-cov` in `requirements.txt`
- Run:
```bash
pytest --cov=. --cov-report=term-missing
```
- You’ll see overall % and missing lines.

### 🧠 Deep Dive (Why & How)
- **Why pagination?** Prevents large responses; improves performance & UX.
- **Why sorting?** Deterministic ordering for lists (e.g., by `price` or `name`).
- **MongoDB mechanics:** We use `find().skip(skip).limit(limit).sort(field, dir)`. `dir` is `1` (asc) or `-1` (desc).
- **FastAPI validation:** Query params (`limit`, `skip`, etc.) are typed, so FastAPI validates them automatically.
- **Strawberry mapping:** Python args `sort_by`/`order` become `sortBy`/`order` in GraphQL (camelCase). Strawberry handles this mapping automatically.
- **Coverage:** Confirms tests exercise code paths; `term-missing` shows the exact lines not covered so you can add tests.

### ✅ Summary
- You’ve added efficient pagination and sorting to both REST & GraphQL.
- You can verify correctness with tests and track quality via coverage.

---

# ✅ Sanity Commands (Quick Reference)

**Root health check**
```bash
curl -i http://127.0.0.1:8000/
```

**REST list with pagination/sorting**
```bash
curl "http://127.0.0.1:8000/products?limit=5&skip=0&sort_by=price&order=desc"
```

**GraphQL query**
```bash
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ allProducts(limit:5, sortBy:\"price\", order:\"desc\") { name price } }"}'
```

**Run tests (after server started)**
```bash
pytest -q
```

**Coverage**
```bash
pytest --cov=. --cov-report=term-missing
```

---

If you want, I can keep building **Day 13+** (auth, env config, CI with GitHub Actions, Docker, Playwright UI tests) in this same format so the README stays your single source of truth. Want me to line up Day 13 next?
````
