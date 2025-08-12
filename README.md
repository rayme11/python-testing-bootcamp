---

````markdown
# Python Testing Bootcamp – Day-by-Day Learning Guide

## ⚡ Quick Start – Auto-Run Everything

If you’re running this inside **GitHub Codespaces**, you can start **MongoDB**, **FastAPI**, and **GraphQL** automatically using our `/scripts/start.sh` script.

### 1️⃣ Run the Autostart Script
```bash
chmod +x scripts/start.sh
./scripts/start.sh
````

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
│   ├── test_graphql_api.py
│   └── test_graphql_filters.py
├── data/
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 📅 Day 1 – Setting Up the Environment in GitHub Codespaces

**🎯 Objective:**
Set up a complete Python development environment in GitHub Codespaces with all required dependencies for API, MongoDB, and GraphQL development.

**📚 Concepts Covered:** Codespaces, Dev Containers, dependencies, port forwarding.

**🛠 Steps:**

1. **Create Repo** → open in Codespaces.
2. Add **`.devcontainer/devcontainer.json`**:

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

3. **requirements.txt** (explicit):

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
```

4. **Folders & files:**

```bash
mkdir -p src tests scripts data .devcontainer
touch src/__init__.py src/main.py tests/conftest.py README.md pytest.ini
```

**✅ Outcome:**
A bootable Codespace that installs deps and forwards port 8000.

---

## 📅 Day 2 – Python Refresher: Functions, Classes, Tests

**🎯 Objective:**
Refresh Python fundamentals for testing.

**📚 Concepts Covered:** functions, classes, pytest assertions.

**🛠 Steps:**

* `src/day2_basics.py`

```python
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
```

* `tests/test_day2_basics.py`

```python
from src.day2_basics import add, Calculator

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    calc = Calculator()
    assert calc.multiply(2, 3) == 6
```

* Run:

```bash
pytest -q
```

**✅ Outcome:**
Unit tests pass in Codespaces.

---

## 📅 Day 3 – Pytest Fundamentals & Fixtures

**🎯 Objective:**
Learn pytest config and fixtures.

**📚 Concepts Covered:** `pytest.ini`, fixtures, discovery.

**🛠 Steps:**

* `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
```

* `tests/conftest.py`

```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "role": "tester"}
```

* `tests/test_users.py`

```python
def test_sample_user_fixture(sample_user):
    assert sample_user["role"] == "tester"
```

* Run:

```bash
pytest -v
```

**✅ Outcome:**
Understand and use fixtures for setup.

---

## 📅 Day 4 – First FastAPI Endpoint

**🎯 Objective:**
Create & test a minimal FastAPI app.

**📚 Concepts Covered:** FastAPI app, TestClient.

**🛠 Steps:**

* `src/main.py`

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running"}
```

* `tests/test_root.py`

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "API is running"
```

* Run:

```bash
pytest -q
```

**✅ Outcome:**
First HTTP endpoint and test pass.

---

## 📅 Day 5 – REST: `/products` with MongoDB

**🎯 Objective:**
Add REST endpoints backed by MongoDB.

**📚 Concepts Covered:** Motor async client, Pydantic model.

**🛠 Steps:**

* `src/main.py` (extend)

```python
from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List

app = FastAPI()

# Mongo
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.testing_db
products_collection = db.products

@app.get("/")
def root():
    return {"message": "API is running"}

class Product(BaseModel):
    name: str
    price: float

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

# GraphQL (will fill in Day 6/9/11)
@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(self) -> List[ProductType]:
        results = []
        async for doc in products_collection.find():
            results.append(ProductType(name=doc["name"], price=doc["price"]))
        return results

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

* Run server:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**✅ Outcome:**
Mongo-backed REST list/create endpoints.

---

## 📅 Day 6 – Testing REST with TestClient

**🎯 Objective:**
Test `/products` POST + GET.

**📚 Concepts Covered:** API testing pattern, asserts.

**🛠 Steps:**

* `tests/test_products_api.py`

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

* Run:

```bash
pytest -q
```

**✅ Outcome:**
REST endpoints covered by tests.

---

## 📅 Day 7 – Pytest Autouse DB Seeding

**🎯 Objective:**
Ensure DB starts clean with known data for each test.

**📚 Concepts Covered:** autouse fixtures, async setup/teardown.

**🛠 Steps:**

* `tests/conftest.py` (extend)

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

**✅ Outcome:**
Repeatable tests with deterministic data.

---

## 📅 Day 8 – Testing GraphQL (Query & Mutation)

**🎯 Objective:**
Automate GraphQL testing with `httpx` + `pytest-asyncio`.

**📚 Concepts Covered:** Strawberry GraphQL, posting JSON `{ query: ... }`.

**🛠 Steps:**

* Update GraphQL **Mutation** in `src/main.py`:

```python
@strawberry.input
class ProductInput:
    name: str
    price: float

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductInput) -> str:
        await products_collection.insert_one({"name": product.name, "price": product.price})
        return f"Product '{product.name}' added."

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

* `tests/test_graphql_api.py`

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_add_product_graphql():
    query = """
    mutation {
      addProduct(product: { name: "Keyboard", price: 49.99 })
    }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": query})
    assert r.status_code == 200
    assert "Keyboard" in r.text

@pytest.mark.asyncio
async def test_all_products_graphql():
    query = """
    {
      allProducts {
        name
        price
      }
    }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": query})
    assert r.status_code == 200
    data = r.json()["data"]["allProducts"]
    assert isinstance(data, list)
```

* Run:

```bash
pytest -q
```

**✅ Outcome:**
Automated GraphQL tests passing.

---

## 📅 Day 9 – GraphQL Filtering (Name & Price)

**🎯 Objective:**
Add filter arguments to `allProducts`.

**📚 Concepts Covered:** GraphQL args → dynamic Mongo query.

**🛠 Steps:**

* Update `Query` in `src/main.py`:

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
        query = {}
        if name_contains:
            query["name"] = {"$regex": name_contains, "$options": "i"}
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price

        results = []
        async for doc in products_collection.find(query):
            results.append(ProductType(name=doc["name"], price=doc["price"]))
        return results
```

* `tests/test_graphql_filters.py`

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_filter_products_by_name():
    q = """
    { allProducts(nameContains: "Preloaded") { name price } }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": q})
    assert r.status_code == 200
    data = r.json()["data"]["allProducts"]
    assert len(data) > 0
    assert all("Preloaded" in p["name"] for p in data)

@pytest.mark.asyncio
async def test_filter_products_by_price_range():
    q = """
    { allProducts(minPrice: 10.0, maxPrice: 15.0) { name price } }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": q})
    assert r.status_code == 200
    data = r.json()["data"]["allProducts"]
    assert len(data) > 0
    assert all(10.0 <= p["price"] <= 15.0 for p in data)
```

* Run:

```bash
pytest -q
```

**✅ Outcome:**
GraphQL supports useful filters with tests.

---

## 📅 Day 10 – Seeding the Database Automatically

**🎯 Objective:**
Seed MongoDB with realistic data using Faker.

**📚 Concepts Covered:** scripts, auto-seed on start.

**🛠 Steps:**

* `scripts/seed_data.py`

```python
from faker import Faker
import motor.motor_asyncio
import asyncio

fake = Faker()

async def seed_products():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    products_collection = db.products
    await products_collection.delete_many({})
    products = [{"name": fake.word().title(), "price": round(fake.pyfloat(left_digits=2, right_digits=2, positive=True), 2)} for _ in range(10)]
    await products_collection.insert_many(products)
    print(f"✅ Seeded {len(products)} products.")

if __name__ == "__main__":
    asyncio.run(seed_products())
```

* `scripts/start.sh`

```bash
#!/bin/bash
mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
sleep 3
python scripts/seed_data.py
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

* Run:

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**✅ Outcome:**
Consistent seeded data every time you start.

---

## 📅 Day 11 – GraphQL Update & Delete (CRUD Completion) + Tests

**🎯 Objective:**
Add **update** and **delete** GraphQL mutations with validation & error handling, and write tests. You’ll complete CRUD for `Product` via GraphQL.

**📚 Concepts Covered:**

* Strawberry input types for updates
* Finding & updating Mongo docs
* Returning helpful mutation results (messages / booleans)
* Testing happy-path and error-path behavior

**🛠 Steps:**

### 1) Extend GraphQL schema (in `src/main.py`)

Add an ID-based update and delete:

```python
import bson  # at top (for ObjectId)

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductInput) -> str:
        await products_collection.insert_one({"name": product.name, "price": product.price})
        return f"Product '{product.name}' added."

    @strawberry.mutation
    async def update_product(
        self,
        id: str,
        product: ProductInput
    ) -> str:
        # Validate ObjectId
        try:
            oid = bson.ObjectId(id)
        except Exception:
            return "Invalid product ID."

        result = await products_collection.update_one(
            {"_id": oid},
            {"$set": {"name": product.name, "price": product.price}}
        )
        if result.matched_count == 0:
            return "Product not found."
        return "Product updated."

    @strawberry.mutation
    async def delete_product(self, id: str) -> str:
        try:
            oid = bson.ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await products_collection.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return "Product not found."
        return "Product deleted."
```

> Tip: We’re returning **strings** for clarity. You could return a richer type `{ success: Boolean, message: String }` if you prefer.

### 2) Add a helper REST route to fetch a single product ID (optional for demos)

This makes it easy to grab an ID to test updates/deletes:

```python
from fastapi import HTTPException

@app.get("/products/first-id")
async def first_product_id():
    doc = await products_collection.find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="No products")
    return {"id": str(doc["_id"]), "name": doc["name"], "price": doc["price"]}
```

### 3) Test mutations (create `tests/test_graphql_mutations.py`)

```python
import pytest
from httpx import AsyncClient
from src.main import app, products_collection
from bson import ObjectId

@pytest.mark.asyncio
async def test_update_and_delete_product_graphql():
    # Seed one known product manually here to control the ID
    inserted = await products_collection.insert_one({"name": "TempProd", "price": 9.99})
    pid = str(inserted.inserted_id)

    # Update
    update_q = f"""
    mutation {{
      updateProduct(id: "{pid}", product: {{ name: "UpdatedProd", price: 19.99 }})
    }}
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.post("/graphql", json={"query": update_q})
    assert r1.status_code == 200
    assert "Product updated" in r1.text

    # Verify update
    doc = await products_collection.find_one({"_id": ObjectId(pid)})
    assert doc["name"] == "UpdatedProd"
    assert float(doc["price"]) == 19.99

    # Delete
    delete_q = f"""
    mutation {{
      deleteProduct(id: "{pid}")
    }}
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r2 = await ac.post("/graphql", json={"query": delete_q})
    assert r2.status_code == 200
    assert "Product deleted" in r2.text

    # Verify deletion
    gone = await products_collection.find_one({"_id": ObjectId(pid)})
    assert gone is None

@pytest.mark.asyncio
async def test_update_with_invalid_id_graphql():
    q = """
    mutation {
      updateProduct(id: "not-an-oid", product: { name: "X", price: 1.0 })
    }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/graphql", json={"query": q})
    assert r.status_code == 200
    assert "Invalid product ID" in r.text
```

### 4) Run the tests

```bash
pytest -q
```

### 5) Try the mutations in GraphiQL

* Get a product ID:

```bash
curl -s https://<your-forwarded-url>.github.dev/products/first-id | jq
```

* Update in GraphiQL:

```graphql
mutation {
  updateProduct(id: "PASTE_ID_HERE", product: { name: "Pro Desk Mat", price: 29.99 })
}
```

* Delete in GraphiQL:

```graphql
mutation {
  deleteProduct(id: "PASTE_ID_HERE")
}
```

**✅ Outcome:**
You now have **full CRUD** for `Product` via GraphQL with clear messages and automated tests, including validation for invalid IDs and not-found cases.

---

## 🚀 Auto-Start Environment in Codespaces (Recap)

To avoid manual steps:

* **scripts/start.sh** (already created):

```bash
#!/bin/bash
mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
sleep 3
python scripts/seed_data.py
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Run any time:

```bash
./scripts/start.sh
```

---

## ✅ Sanity Commands

* Check API root:

```bash
curl -i http://localhost:8000/
```

* Query GraphQL from terminal:

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ allProducts { name price } }"}'
```

* Open GraphQL UI (Codespaces):

```
https://<your-forwarded-url>.github.dev/graphql
```

---

## 🧭 What’s Next (Day 12 preview)

* Add pagination + sorting to GraphQL queries
* Introduce input validation rules and constraints
* Generate coverage reports for REST + GraphQL tests

---

```

Want me to immediately tee up **Day 12** (pagination + sorting + coverage) in this same format so your README stays perfectly in sync each day?
```
