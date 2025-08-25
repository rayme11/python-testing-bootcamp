# Day 8

Great 👍 Let’s move on with **Day 8** of the Python Testing Bootcamp, keeping everything consistent with our **FastAPI + MongoDB + GraphQL** journey.

Here’s the detailed README content for **Day 8**:

---

````markdown
# Day 8 – Introducing GraphQL with Strawberry + FastAPI

Welcome to **Day 8** of the Python Testing Bootcamp.

Until now, we’ve built:
- A **FastAPI REST API** with CRUD operations.
- A working **MongoDB** backend for persistence.
- **Tests with fixtures** for clean, reliable test runs.

Today we’ll start integrating **GraphQL** into our stack using **Strawberry**.  
GraphQL will allow us to **query and mutate** data more flexibly compared to REST.

---

## 🎯 Goals

- Understand the **differences between REST and GraphQL**.
- Install and configure **Strawberry** with FastAPI.
- Define a **GraphQL schema** for `Product`.
- Write our first **query** and **mutation** for products.
- Add initial **GraphQL tests**.

---

## 📖 Theory – Why GraphQL?

- **REST APIs** expose multiple endpoints (e.g., `/products`, `/products/{id}`).
- **GraphQL** exposes a **single endpoint** (`/graphql`) where you:
  - Ask exactly for the data you want.
  - Can combine queries in one request.
  - Support mutations (create/update/delete).

### Example:
- REST:  
  `GET /products` → returns all fields of all products.  
- GraphQL:  
  ```graphql
  {
    allProducts {
      id
      name
    }
  }
````

→ returns only `id` and `name`, nothing extra.

This **reduces over-fetching** and makes APIs more efficient for clients.

---

## 🛠 Step-by-Step Instructions

### 1) Install Strawberry GraphQL

Update `requirements.txt`:

```txt
strawberry-graphql[fastapi]==0.211.0
```

Install:

```bash
pip install -r requirements.txt
```

---

### 2) Add GraphQL schema

Create `src/graphql_schema.py`:

```python
# src/graphql_schema.py
import strawberry
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_products_db"
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

@strawberry.type
class Product:
    id: strawberry.ID
    name: str
    price: float

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(self) -> List[Product]:
        products = []
        cursor = db.products.find({})
        async for doc in cursor:
            products.append(Product(id=str(doc["_id"]), name=doc["name"], price=doc["price"]))
        return products

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, name: str, price: float) -> Product:
        doc = {"name": name, "price": price}
        result = await db.products.insert_one(doc)
        return Product(id=str(result.inserted_id), name=name, price=price)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

---

### 3) Hook GraphQL into FastAPI

Update `src/main.py`:

```python
# src/main.py
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from src.graphql_schema import schema

app = FastAPI()

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

Now you can open GraphQL Playground at:
👉 `http://localhost:8000/graphql`

---

### 4) Add GraphQL tests

Create `tests/test_graphql_api.py`:

```python
# tests/test_graphql_api.py
import pytest

@pytest.mark.asyncio
async def test_graphql_add_product(test_client):
    query = """
    mutation {
      addProduct(name: "Book", price: 15.99) {
        id
        name
        price
      }
    }
    """
    r = await test_client.post("/graphql", json={"query": query})
    data = r.json()
    assert "errors" not in data
    product = data["data"]["addProduct"]
    assert product["name"] == "Book"
    assert product["price"] == 15.99

@pytest.mark.asyncio
async def test_graphql_all_products_query(test_client):
    query = """
    {
      allProducts {
        id
        name
        price
      }
    }
    """
    r = await test_client.post("/graphql", json={"query": query})
    data = r.json()
    assert "errors" not in data
    assert isinstance(data["data"]["allProducts"], list)
```

---

### 5) Run Tests

```bash
pytest -v
```

You should see both REST **and** GraphQL tests running successfully 🎉.

---

## ✅ Summary

Today you:

* Learned **why GraphQL is useful** compared to REST.
* Added **Strawberry GraphQL** to your FastAPI app.
* Defined a **GraphQL schema** with queries and mutations.
* Wrote your first **GraphQL tests**.

Next up (**Day 9**): We’ll expand GraphQL with **update and delete mutations** to complete CRUD!

```

---

```

Run:
```bash
./scripts/start.sh
```
