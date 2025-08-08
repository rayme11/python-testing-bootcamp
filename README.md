Here is the full `README.md` with everything we've done so far — fully copy-pasteable:

---

````markdown
# 🧪 Python Testing Bootcamp in GitHub Codespaces

Welcome to a 3-month guided bootcamp to become a mid-to-senior-level test engineer using Python, FastAPI, MongoDB, GraphQL, and modern testing tools — all inside **GitHub Codespaces**. This README covers your full journey, step by step.

---

## 🗓️ WEEK 1: Environment, Python, Testing Basics

---

### ✅ Day 1: Setting Up the Environment in GitHub Codespaces

1. **Create GitHub Repo** (e.g., `python-testing-bootcamp`)
2. **Enable Codespaces** via the green `<> Code` button → "Create codespace on main"
3. **Add `.devcontainer/devcontainer.json`:**

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

4. **Add `requirements.txt`:**

```txt
fastapi
uvicorn
pymongo
motor
httpx
pytest
pytest-asyncio
strawberry-graphql
```

5. **Add `README.md`** (you’re reading it!)
6. **Create folder structure:**

```bash
mkdir src tests
touch src/main.py
```

---

### ✅ Day 2: Python Refresher

* Write simple Python functions in `src/day2_basics.py`
* Create `tests/test_day2_basics.py` to test them using `pytest`
* Run tests:

```bash
pytest
```

---

### ✅ Day 3: Pytest Essentials

* Create a `pytest.ini` to organize tests:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

* Use `fixtures`, `assert`, and parametrize
* Example fixture in `conftest.py`

---

### ✅ Day 4: Build Your FastAPI App

In `src/main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

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
    return {
        "message": "Product added",
        "id": str(result.inserted_id)
    }

@app.get("/products")
async def list_products():
    products = []
    async for product in products_collection.find():
        product["_id"] = str(product["_id"])
        products.append(product)
    return products
```

* Run server:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

### ✅ Day 5: Write API Tests

In `tests/test_products_api.py`:

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_product():
    response = client.post("/products", json={"name": "Monitor", "price": 299.99})
    assert response.status_code == 200
    assert "id" in response.json()

def test_list_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

* Run with:

```bash
pytest
```

---

### ✅ Day 6: Add GraphQL to FastAPI

Install Strawberry GraphQL (already in requirements.txt).

Update `src/main.py`:

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(self) -> list[ProductType]:
        products = []
        async for product in products_collection.find():
            products.append(ProductType(name=product["name"], price=product["price"]))
        return products

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductType) -> str:
        await products_collection.insert_one(product.__dict__)
        return "Product added"

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

* Visit `/graphql` in Codespaces UI:

  * Example mutation:

```graphql
mutation {
  addProduct(product: { name: "Laptop", price: 149.99 })
}
```

* Example query:

```graphql
{
  allProducts {
    name
    price
  }
}
```

---

## 🛠️ Appendix: Automatically Start MongoDB in Codespaces

To avoid manually starting MongoDB each time your Codespace starts:

### ✅ Step 1: Add to `postCreateCommand`

Already included:

```json
"postCreateCommand": "pip install -r requirements.txt && sudo mkdir -p /data/db && sudo chown -R $(whoami) /data/db && mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &"
```

---

## 🔄 Recommended Automation Improvements

### ✅ Forward Ports Automatically

```json
"forwardPorts": [8000]
```

### ✅ Add a `Makefile`

```make
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/
```

### ✅ Add Dev Script

`scripts/start.sh`:

```bash
#!/bin/bash
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Make executable:

```bash
chmod +x scripts/start.sh
```

Then run:

```bash
./scripts/start.sh
```

---
