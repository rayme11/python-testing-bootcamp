
* Each day is written as **Goals → Step-by-step instructions → Summary**
* Everything reflects the **latest stable setup** (lazy Mongo init, Strawberry GraphQL with context, testing against a real Uvicorn server, pagination/sorting, and coverage)
* Includes the **final working code** for:

  * `src/main.py`
  * `scripts/start.sh`, `scripts/seed_data.py`
  * `requirements.txt`, `pytest.ini`
  * **Final passing tests** (`tests/test_graphql_api.py`, `tests/test_products_api.py`, etc.)

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

* **Goals**
  - Initialize a Python dev environment in Codespaces
  - Install core dependencies and forward port 8000

* **Step-by-step instructions** (with exact commands and code blocks)

1) Create repo → open in **Codespaces**.

2) Add **`.devcontainer/devcontainer.json`**:
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

3) Add **`requirements.txt`** (explicit deps):
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

4) Scaffold folders:
```bash
mkdir -p src tests scripts data .devcontainer
touch src/__init__.py src/main.py tests/conftest.py README.md pytest.ini
```

5) Add **`pytest.ini`**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts = -v --tb=short --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=0
```

* **Summary (what you accomplished & learned)**
  - Codespace builds automatically, dependencies install, port 8000 forwarded.
  - You’re ready to run & test locally inside Codespaces.

---

## 📅 Day 2 – Python Refresher: Functions, Classes, Tests

* **Goals**
  - Refresh Python basics needed for testing
  - Write first unit tests

* **Step-by-step instructions** (with exact commands and code blocks)

Create **`src/day2_basics.py`**:
```python
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
```

Create **`tests/test_day2_basics.py`**:
```python
from src.day2_basics import add, Calculator

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    calc = Calculator()
    assert calc.multiply(2, 3) == 6
```

Run tests:
```bash
pytest -q
```

* **Summary (what you accomplished & learned)**
  - You wrote unit tests and validated basic functionality quickly with pytest.

---

## 📅 Day 3 – Pytest Fundamentals & Fixtures

* **Goals**
  - Learn pytest config & fixtures
  - Share setup data across tests

* **Step-by-step instructions** (with exact commands and code blocks)

Create/extend **`tests/conftest.py`**:
```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "role": "tester"}
```

Create **`tests/test_users.py`**:
```python
def test_sample_user_fixture(sample_user):
    assert sample_user["role"] == "tester"
```

Run:
```bash
pytest -v
```

* **Summary (what you accomplished & learned)**
  - You used a fixture to share data across tests.
  - You understand how pytest discovers tests and fixtures.

---

## 📅 Day 4 – First FastAPI Endpoint

* **Goals**
  - Create first FastAPI app
  - Test it end-to-end

* **Step-by-step instructions** (with exact commands and code blocks)

Set **`src/main.py`**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running"}
```

Add **`tests/test_root.py`**:
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

* **Summary (what you accomplished & learned)**
  - You built and tested your first HTTP endpoint.

---

## 📅 Day 5 – REST: `/products` with MongoDB

* **Goals**
  - Add REST endpoints backed by MongoDB (async Motor)
  - Validate payloads with Pydantic

* **Step-by-step instructions** (with exact commands and code blocks)

Temporarily wire Mongo (we’ll refactor to lazy init later) — **extend `src/main.py`**:
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

* **Summary (what you accomplished & learned)**
  - REST endpoints now create & list products stored in MongoDB.

---

## 📅 Day 6 – Testing REST with TestClient

* **Goals**
  - Write tests for `/products` POST + GET

* **Step-by-step instructions** (with exact commands and code blocks)

Create **`tests/test_products_api.py`** (initial, in-process style):
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

* **Summary (what you accomplished & learned)**
  - You built REST tests. (We’ll later switch to real-server tests to avoid async loop issues.)

---

## 📅 Day 7 – Pytest Autouse DB Seeding

* **Goals**
  - Guarantee predictable DB content per test
  - Learn async fixtures with setup/teardown

* **Step-by-step instructions** (with exact commands and code blocks)

Extend **`tests/conftest.py`**:
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

* **Summary (what you accomplished & learned)**
  - Tests now start from a known database state and clean up afterward.

---

## 📅 Day 8 – GraphQL (Query & Mutation)

* **Goals**
  - Add GraphQL to FastAPI with Strawberry
  - Support `allProducts` and `addProduct`

* **Step-by-step instructions** (with exact commands and code blocks)

Add Strawberry schema (initial) — **update `src/main.py`**:
```python
from typing import List
import strawberry
from strawberry.fastapi import GraphQLRouter
# ... keep previous fastapi + mongo wiring ...

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

Add **`tests/test_graphql_api.py`** (initial, in-process style):
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

* **Summary (what you accomplished & learned)**
  - GraphQL endpoint is live with basic query and mutation.

---

## 📅 Day 9 – GraphQL Filtering (Name & Price)

* **Goals**
  - Add filter args to GraphQL query
  - Build dynamic Mongo queries

* **Step-by-step instructions** (with exact commands and code blocks)

Update GraphQL query with filters — **update `src/main.py`**:
```python
@strawberry.type
class Query:
    @strawberry.field
    async def all_products(
        self,
        nameContains: str | None = None,
        minPrice: float | None = None,
        maxPrice: float | None = None
    ) -> List[ProductType]:
        query: dict = {}
        if nameContains:
            query["name"] = {"$regex": nameContains, "$options": "i"}
        if minPrice is not None or maxPrice is not None:
            price = {}
            if minPrice is not None: price["$gte"] = float(minPrice)
            if maxPrice is not None: price["$lte"] = float(maxPrice)
            query["price"] = price

        out = []
        async for doc in products_collection.find(query):
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out
```

Add filter tests (in-process style for now) — **extend `tests/test_graphql_api.py`**:
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

* **Summary (what you accomplished & learned)**
  - GraphQL supports real-world filtering; tests verify results.

---

## 📅 Day 10 – Seed Script & Autostart

* **Goals**
  - Auto-seed DB with Faker
  - One-command startup for devs

* **Step-by-step instructions** (with exact commands and code blocks)

Create **`scripts/seed_data.py`**:
```python
import asyncio
from faker import Faker
import motor.motor_asyncio

fake = Faker()

async def seed_products():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    col = db.products
    await col.delete_many({})
    docs = [
        {"name": "Preloaded Item 1", "price": 10.99},
        {"name": "Preloaded Item 2", "price": 20.50},
    ]
    for _ in range(8):
        docs.append({
            "name": fake.word().title(),
            "price": round(fake.pyfloat(left_digits=2, right_digits=2, positive=True), 2)
        })
    await col.insert_many(docs)
    print(f"✅ Seeded {len(docs)} products.")

if __name__ == "__main__":
    asyncio.run(seed_products())
```

Create **`scripts/start.sh`**:
```bash
#!/usr/bin/env bash
set -euo pipefail

# 1) Start MongoDB
mkdir -p /data/db
if ! pgrep -x mongod >/dev/null; then
  mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
  sleep 2
fi

# 2) Seed data (best-effort)
python scripts/seed_data.py || true

# 3) Run API
exec uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Run:
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

* **Summary (what you accomplished & learned)**
  - Any engineer can start DB + API + seed with a single command.

---

## 📅 Day 11 – Stabilizing Async with Lazy DB + Real-Server Tests

* **Goals**
  - Fix `Event loop is closed` & missing `app.state.products`
  - Use **lazy Mongo init** and test against a running **Uvicorn** server

* **Step-by-step instructions** (with exact commands and code blocks)

**Replace `src/main.py` with lazy DB + Strawberry context + REST/GraphQL**
```python
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, Query
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI()

# ---------- Lazy Mongo initialization ----------
def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# ---------- REST ----------
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
async def list_products(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("name", pattern="^(name|price)$"),
    order: str = Query("asc", pattern="^(?i)(asc|desc)$"),
):
    col = ensure_mongo(request)
    sort_dir = 1 if order.lower() == "asc" else -1
    items: list[dict] = []
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

# ---------- GraphQL ----------
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
class QueryGQL:
    @strawberry.field
    async def all_products(
        self,
        info,
        nameContains: Optional[str] = None,
        minPrice: Optional[float] = None,
        maxPrice: Optional[float] = None,
        limit: Optional[int] = 100,
        skip: Optional[int] = 0,
        sortBy: Optional[str] = "name",
        order: Optional[str] = "asc",
    ) -> List[ProductType]:
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        query: dict = {}
        if nameContains:
            query["name"] = {"$regex": nameContains, "$options": "i"}
        if minPrice is not None or maxPrice is not None:
            price = {}
            if minPrice is not None: price["$gte"] = float(minPrice)
            if maxPrice is not None: price["$lte"] = float(maxPrice)
            query["price"] = price

        # normalize args
        limit = max(1, min(int(limit or 100), 500))
        skip = max(0, int(skip or 0))
        sortBy = sortBy if sortBy in {"name", "price"} else "name"
        sort_dir = 1 if (order or "asc").lower() == "asc" else -1

        out: list[ProductType] = []
        cursor = col.find(query).skip(skip).limit(limit).sort(sortBy, sort_dir)
        async for doc in cursor:
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out

@strawberry.type
class MutationGQL:
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

schema = strawberry.Schema(query=QueryGQL, mutation=MutationGQL)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
```

Switch tests to hit the **real server** (no in-process ASGI).  
(We’ll add final working tests in Day 12.)

* **Summary (what you accomplished & learned)**
  - Lazy DB init + real-server tests eliminate async loop errors.
  - GraphQL resolvers access FastAPI’s `request` via Strawberry context.
  - The app is stable and closer to production.

---

## 📅 Day 12 – Pagination, Sorting & Coverage (REST + GraphQL) **(+ Final Working Tests)**

* **Goals**
  - Add **pagination** (`limit`, `skip`) & **sorting** (`sort_by`/`sortBy`, `order`) to REST & GraphQL
  - Validate inputs and normalize defaults
  - Generate **coverage reports** (terminal + HTML)
  - Provide **final working tests** that hit the live server

* **Step-by-step instructions** (with exact commands and code blocks)

A) REST pagination & sorting (**already in `src/main.py` Day 11**)
- Example:
```bash
curl "http://127.0.0.1:8000/products?limit=5&skip=0&sort_by=price&order=desc"
```

B) GraphQL pagination & sorting (**already in `src/main.py` Day 11**)
- Example:
```graphql
{
  allProducts(limit: 5, skip: 0, sortBy: "price", order: "desc") {
    name
    price
  }
}
```

C) **Final working tests** (hit the real Uvicorn server).  
> Keep your server running in one terminal (`./scripts/start.sh`) and run tests in another.

Create/replace **`tests/test_graphql_api.py`**:
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
    assert await wait_for_up(f"{BASE}/"), "API not reachable at /"
    q = 'mutation { addProduct(product: { name: "Keyboard", price: 49.99 }) }'
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
    assert "Keyboard" in r.text

@pytest.mark.asyncio
async def test_graphql_all_products_query():
    q = "{ allProducts { name price } }"
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
    data = payload["data"]["allProducts"]
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_graphql_filter_by_name_and_price():
    q1 = '{ allProducts(nameContains: "Preloaded") { name price } }'
    r1 = await gql(q1)
    assert r1.status_code == 200, r1.text
    p1 = r1.json()
    assert p1.get("data") is not None, r1.text
    data1 = p1["data"]["allProducts"]
    assert len(data1) > 0
    assert all("Preloaded" in p["name"] for p in data1)

    q2 = '{ allProducts(minPrice: 10.0, maxPrice: 15.0) { name price } }'
    r2 = await gql(q2)
    assert r2.status_code == 200, r2.text
    p2 = r2.json()
    assert p2.get("data") is not None, r2.text
    data2 = p2["data"]["allProducts"]
    assert len(data2) > 0
    assert all(10.0 <= p["price"] <= 15.0 for p in data2)

@pytest.mark.asyncio
async def test_graphql_pagination_and_sorting():
    q = '{ allProducts(limit: 5, skip: 0, sortBy: "price", order: "desc") { name price } }'
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    data = payload.get("data", {}).get("allProducts", [])
    assert len(data) <= 5
    if len(data) >= 2:
        assert data[0]["price"] >= data[-1]["price"]
```

Create/replace **`tests/test_products_api.py`**:
```python
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

@pytest.mark.asyncio
async def test_rest_pagination_and_sorting():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products", params={"limit": 5, "skip": 0, "sort_by": "price", "order": "desc"})
    assert r.status_code == 200, r.text
    arr = r.json()
    assert len(arr) <= 5
    if len(arr) >= 2:
        assert arr[0]["price"] >= arr[-1]["price"]
```

D) **Coverage reports** (terminal + HTML)
```bash
pytest --cov=. --cov-report=term-missing
```
- HTML report generated at `htmlcov/index.html`

**View HTML coverage in Codespaces (best way):**
```bash
python -m http.server 9000 -d htmlcov
```
- Open **Ports** tab → click the globe icon next to **9000** → open `index.html`

* **Summary (what you accomplished & learned)**
  - You added efficient pagination/sorting to REST & GraphQL with input validation.
  - You now have **final passing tests** that hit a running server (more realistic/reliable).
  - You generate coverage both in terminal and rich HTML, easy to open in Codespaces.

---

# ✅ Sanity Commands (Quick Reference)

**Root health check**
```bash
curl -i http://127.0.0.1:8000/
```

**REST create**
```bash
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Monitor","price":299.99}' | jq
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

**Run tests (server running in another terminal via ./scripts/start.sh)**
```bash
pytest -q
```

**Coverage**
```bash
pytest --cov=. --cov-report=term-missing
python -m http.server 9000 -d htmlcov   # View via Ports tab
```

---

## 📚 Appendix — Final, Working `src/main.py` (for reference)

```python
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, Query
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI()

# ---------- Lazy Mongo initialization ----------
def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# ---------- REST ----------
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
async def list_products(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("name", pattern="^(name|price)$"),
    order: str = Query("asc", pattern="^(?i)(asc|desc)$"),
):
    col = ensure_mongo(request)
    sort_dir = 1 if order.lower() == "asc" else -1
    items: list[dict] = []
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

# ---------- GraphQL ----------
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
class QueryGQL:
    @strawberry.field
    async def all_products(
        self,
        info,
        nameContains: Optional[str] = None,
        minPrice: Optional[float] = None,
        maxPrice: Optional[float] = None,
        limit: Optional[int] = 100,
        skip: Optional[int] = 0,
        sortBy: Optional[str] = "name",
        order: Optional[str] = "asc",
    ) -> List[ProductType]:
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        query: dict = {}
        if nameContains:
            query["name"] = {"$regex": nameContains, "$options": "i"}
        if minPrice is not None or maxPrice is not None:
            price = {}
            if minPrice is not None: price["$gte"] = float(minPrice)
            if maxPrice is not None: price["$lte"] = float(maxPrice)
            query["price"] = price

        limit = max(1, min(int(limit or 100), 500))
        skip = max(0, int(skip or 0))
        sortBy = sortBy if sortBy in {"name", "price"} else "name"
        sort_dir = 1 if (order or "asc").lower() == "asc" else -1

        out: list[ProductType] = []
        cursor = col.find(query).skip(skip).limit(limit).sort(sortBy, sort_dir)
        async for doc in cursor:
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out

@strawberry.type
class MutationGQL:
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

schema = strawberry.Schema(query=QueryGQL, mutation=MutationGQL)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
```

---

## 🧩 Shared Config Files (for convenience)

**`requirements.txt`**
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

**`pytest.ini`**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts = -v --tb=short --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=0
```

**`scripts/seed_data.py`**
```python
import asyncio
from faker import Faker
import motor.motor_asyncio

fake = Faker()

async def seed_products():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    col = db.products
    await col.delete_many({})
    docs = [
        {"name": "Preloaded Item 1", "price": 10.99},
        {"name": "Preloaded Item 2", "price": 20.50},
    ]
    for _ in range(8):
        docs.append({
            "name": fake.word().title(),
            "price": round(fake.pyfloat(left_digits=2, right_digits=2, positive=True), 2)
        })
    await col.insert_many(docs)
    print(f"✅ Seeded {len(docs)} products.")

if __name__ == "__main__":
    asyncio.run(seed_products())
```

**`scripts/start.sh`**
```bash
#!/usr/bin/env bash
set -euo pipefail

# 1) Start MongoDB
mkdir -p /data/db
if ! pgrep -x mongod >/dev/null; then
  mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
  sleep 2
fi

# 2) Seed data (best-effort)
python scripts/seed_data.py || true

# 3) Run API
exec uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---
````
