# Day 4

Got it ✅ — let’s prepare **Day 4** in the same detailed style as your Day 3 README.

Here’s the full `day04/README.md` content:

---

````markdown
# Day 4 – Introduction to FastAPI and First REST Endpoints

Welcome to **Day 4** of the Python Testing Bootcamp.  
Up until now (Days 1–3), we covered the basics of setting up our environment, installing dependencies, writing simple unit tests, and understanding pytest. Today, we expand into **FastAPI**, a modern Python web framework for building APIs quickly and efficiently. This day is important because it lays the foundation for the **API testing** we will build upon in later days.

---

## 🎯 Goals for Day 4
1. Learn what **FastAPI** is and why we use it.  
2. Create a simple **FastAPI app** (`main.py`).  
3. Add our first **REST endpoints** for health check and product creation.  
4. Understand the difference between **unit tests** and **API integration tests**.  
5. Write our first **pytest-based REST API tests** using `httpx`.  

---

## 📖 Theory

### What is FastAPI?
FastAPI is a modern, high-performance web framework built on top of **Starlette** (for the web server parts) and **Pydantic** (for data validation). Key benefits include:
- **Automatic validation**: Ensures request data matches expected schemas.
- **Async support**: Uses Python’s `async/await` for fast I/O operations.
- **Interactive API docs**: Automatically generates Swagger and Redoc docs.
- **Great testing support**: Easily test endpoints with `httpx` or the built-in TestClient.

---

### REST API Basics
- **Endpoint**: A URL that your app exposes, e.g., `/products`.  
- **HTTP methods**:  
  - `GET` → retrieve data  
  - `POST` → create data  
  - `PUT`/`PATCH` → update data  
  - `DELETE` → remove data  

In our bootcamp, products will be the central resource we manage through REST and, later, GraphQL.

---

### Unit Tests vs. API Integration Tests
- **Unit Tests**: Validate functions in isolation (e.g., testing a sum function).  
- **API Integration Tests**: Validate endpoints as if a client is calling them. These often spin up the app and check HTTP requests/responses.

---

## 🛠 Step 1 – Update Requirements

Add **FastAPI** and **httpx** to `requirements.txt`:

```txt
fastapi==0.110.0
uvicorn==0.29.0
httpx==0.27.0
````

Install them:

```bash
pip install -r requirements.txt
```

---

## 🛠 Step 2 – Create `main.py` with FastAPI App

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Product model
class Product(BaseModel):
    id: int
    name: str
    price: float

# Fake in-memory DB
products: List[Product] = []

@app.get("/")
def read_root():
    return {"message": "Welcome to Day 4 - FastAPI Bootcamp"}

@app.get("/products")
def list_products():
    return products

@app.post("/products")
def create_product(product: Product):
    products.append(product)
    return product
```

* We define a `Product` model with Pydantic.
* We store products in an in-memory list (`products`).
* Endpoints:

  * `GET /` → health check
  * `GET /products` → list all products
  * `POST /products` → create a product

Run the app:

```bash
uvicorn main:app --reload
```

Visit:

* Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Health check: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🛠 Step 3 – Write Tests for the API

Create `tests/test_products_api.py`:

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_root_message():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Day 4 - FastAPI Bootcamp"}

@pytest.mark.asyncio
async def test_create_product():
    product = {"id": 1, "name": "Laptop", "price": 1299.99}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/products", json=product)
    assert response.status_code == 200
    assert response.json() == product

@pytest.mark.asyncio
async def test_list_products():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0
```

---

## 🛠 Step 4 – Run Tests

```bash
pytest -v
```

Expected output:

```
tests/test_products_api.py::test_root_message PASSED
tests/test_products_api.py::test_create_product PASSED
tests/test_products_api.py::test_list_products PASSED
```

---

## 📝 Summary for Day 4

* We installed **FastAPI** and built a basic API.
* We created `GET` and `POST` endpoints.
* We wrote integration tests using `httpx.AsyncClient`.
* We learned the difference between unit tests and integration tests.

This is the foundation for the next steps:
👉 Day 5 will introduce **data persistence (SQLite)** and begin testing against a real database.

---

```

---


Do you want me to continue with **Day 5** next in the same format?
```



Run:
```bash
./scripts/start.sh
```
