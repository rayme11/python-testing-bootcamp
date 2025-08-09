Alright — here’s the **complete README.md** from **Day 1 through Day 8**, rebuilt so it’s a *teaching + doing* guide.
You can paste this into your repo and it will have **objectives, concepts, steps, and outcomes** for every day.

---

````markdown
# Python Testing Bootcamp – Full Learning Log (Day 1–8)

This bootcamp takes you from **Python testing basics** to building a **fully tested FastAPI app with MongoDB and GraphQL** in GitHub Codespaces.

Each day includes:

- **🎯 Objective** – what you’re learning
- **📚 Concepts Covered** – theory you’ll touch
- **🛠 Steps** – commands and code
- **✅ Outcome** – what you’ll have working at the end

---

## 📅 Day 1 – GitHub Codespaces Environment Setup

**🎯 Objective:**  
Create a reproducible cloud development environment that includes Python, FastAPI, MongoDB, and testing tools.

**📚 Concepts Covered:**
- GitHub Codespaces & Dev Containers
- Python environment setup
- Installing project dependencies automatically
- Forwarding ports for API access
- Auto-starting MongoDB

**🛠 Steps:**

1. **Create a GitHub repo** → Enable GitHub Codespaces in settings.
2. **Add `.devcontainer/devcontainer.json`:**
```json
{
  "name": "Python Testing Env",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:1": {}
  },
  "postCreateCommand": "pip install -r requirements.txt && sudo mkdir -p /data/db && sudo chown -R $(whoami) /data/db && mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &",
  "forwardPorts": [8000],
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  }
}
````

3. **Add `requirements.txt`:**

```
fastapi
uvicorn
pytest
requests
pymongo
motor
strawberry-graphql
httpx
pytest-asyncio
faker
```

4. **Create folder structure:**

```
.devcontainer/
src/
tests/
data/
README.md
requirements.txt
```

5. Commit & push → open Codespace → wait for build.

**✅ Outcome:**
A Codespaces dev environment that runs Python, auto-installs dependencies, starts MongoDB, and forwards port `8000` for API testing.

---

## 📅 Day 2 – Python Basics Refresher

**🎯 Objective:**
Review Python fundamentals you’ll use for testing.

**📚 Concepts Covered:**

* Functions & return values
* Parametrized tests
* `pytest` basics

**🛠 Steps:**

1. **Create `src/day2_basics.py`:**

```python
def multiply(a, b):
    return a * b
```

2. **Create `tests/test_math_ops.py`:**

```python
import pytest
from src.day2_basics import multiply

@pytest.mark.parametrize("a,b,result", [(2,2,4), (3,3,9)])
def test_multiply_param(a, b, result):
    assert multiply(a, b) == result
```

3. Run tests:

```bash
pytest -q
```

**✅ Outcome:**
You can run Python code + tests in Codespaces and see passing results.

---

## 📅 Day 3 – Pytest Fundamentals

**🎯 Objective:**
Learn core `pytest` features and test organization.

**📚 Concepts Covered:**

* Test discovery rules
* Fixtures for reusable setup
* Assertions

**🛠 Steps:**

1. **Add `pytest.ini`:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

2. Run:

```bash
pytest -q
```

**✅ Outcome:**
Your test folder is automatically discovered, and `pytest` knows where to look.

---

## 📅 Day 4 – Project Structure

**🎯 Objective:**
Make the app importable and ready for modular testing.

**📚 Concepts Covered:**

* Python packages (`__init__.py`)
* Organizing code for tests

**🛠 Steps:**

```bash
touch src/__init__.py
```

**✅ Outcome:**
Your `src` code can now be imported in tests.

---

## 📅 Day 5 – FastAPI REST API

**🎯 Objective:**
Create a FastAPI app with `/products` REST endpoints.

**📚 Concepts Covered:**

* FastAPI basics
* Async MongoDB with `motor`
* REST endpoints

**🛠 Steps:**

`src/main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List

app = FastAPI()

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
            results.append(ProductType(name=doc["name"], price=doc["price"]))
        return results

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductInput) -> str:
        await products_collection.insert_one({"name": product.name, "price": product.price})
        return f"Product '{product.name}' added."

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

Run:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**✅ Outcome:**
You now have a REST + GraphQL API running inside Codespaces.

---

## 📅 Day 6 – Testing REST Endpoints

**🎯 Objective:**
Write tests for `/products` endpoints.

**📚 Concepts Covered:**

* FastAPI’s `TestClient`
* Testing POST & GET endpoints

**🛠 Steps:**

`tests/test_products_api.py`:

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_product():
    response = client.post("/products", json={"name": "Monitor", "price": 299.99})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Product added"
    assert "id" in data

def test_list_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

Run:

```bash
pytest -q
```

**✅ Outcome:**
You can programmatically test REST endpoints.

---

## 📅 Day 7 – Fixtures & MongoDB Seed Data

**🎯 Objective:**
Use pytest fixtures to auto-seed and clean test data.

**📚 Concepts Covered:**

* Autouse fixtures
* Async DB setup/teardown

**🛠 Steps:**

`tests/conftest.py`:

```python
import pytest
import motor.motor_asyncio

@pytest.fixture
def sample_user():
    return {"id": 1, "username": "tester", "role": "admin"}

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
Your DB has known test data before every test run.

---

## 📅 Day 8 – Testing GraphQL

**🎯 Objective:**
Write automated tests for `/graphql` queries and mutations.

**📚 Concepts Covered:**

* Testing GraphQL queries
* Sending JSON payloads to `/graphql`
* Using `pytest-asyncio` with `httpx`

**🛠 Steps:**

`tests/test_graphql_api.py`:

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_add_product_graphql():
    query = """
    mutation {
        addProduct(product: {name: "GraphQL Item", price: 42.0})
    }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/graphql", json={"query": query})
    assert response.status_code == 200
    assert "GraphQL Item" in response.text

@pytest.mark.asyncio
async def test_list_products_graphql():
    query = """
    query {
        allProducts {
            name
            price
        }
    }
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/graphql", json={"query": query})
    assert response.status_code == 200
    assert "name" in response.text
```

Run:

```bash
pytest -q
```

**✅ Outcome:**
You can now fully test GraphQL queries & mutations with Python.

---

## 🔄 Developer Automation

* MongoDB auto-start in Codespaces
* Port `8000` auto-forward
* Makefile:

```make
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
test:
	pytest tests/
```

---

**Next step → Day 9:** Explore more advanced GraphQL queries, filtering, and test coverage reports.

```

---


