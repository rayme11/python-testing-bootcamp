
````markdown
# 🧪 Python Testing Bootcamp (3-Month Curriculum)

This bootcamp is for test engineers looking to master API/backend testing using Python, FastAPI, MongoDB, GraphQL, and modern CI/CD tooling — fully containerized via GitHub Codespaces.

> 👨‍💻 Everything runs in GitHub Codespaces using Dev Containers. No local setup required.

---

## 📚 Week 1: Environment Setup + Python Testing Foundation

---

### ✅ Day 1: Codespaces Setup + FastAPI + DevContainer + Pytest

1. **Create GitHub repo**: `python-testing-bootcamp`
2. **Open with GitHub Codespaces**
3. **Create `.devcontainer/devcontainer.json`**:
   ```json
   {
     "name": "Python Testing Env",
     "image": "mcr.microsoft.com/devcontainers/python:3.11",
     "features": {
       "ghcr.io/devcontainers/features/docker-in-docker:1": {}
     },
     "postCreateCommand": "pip install -r requirements.txt",
     "customizations": {
       "vscode": {
         "extensions": ["ms-python.python"]
       }
     }
   }
````

4. **Create `requirements.txt`** and paste:

   ```
   fastapi
   uvicorn
   pytest
   httpx
   pytest-asyncio
   faker
   pymongo
   motor
   graphene
   ```
5. **Set up folders**:

   ```bash
   mkdir src tests data
   touch src/main.py tests/test_dummy.py README.md
   ```
6. **Create root route in `main.py`**:

   ```python
   from fastapi import FastAPI
   app = FastAPI()

   @app.get("/")
   def root():
       return {"message": "API is running"}
   ```
7. **Run server**:

   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```
8. **Test root with curl**:

   ```bash
   curl http://localhost:8000/
   ```
9. **Create test in `tests/test_dummy.py`**:

   ```python
   def test_always_passes():
       assert True
   ```
10. **Run tests**:

```bash
pytest
```

---

### ✅ Day 2: Python Logic + Unit Tests

1. **Create `src/day2_basics.py`** with:

   ```python
   def greet(name: str): return f"Hello, {name}"
   def multiply(a, b): return a * b
   def is_even(n): return n % 2 == 0
   def factorial(n):
       if n < 0: raise ValueError("No negative values")
       result = 1
       for i in range(2, n + 1): result *= i
       return result
   ```
2. **Create `tests/test_day2_basics.py`**:

   ```python
   from src.day2_basics import *

   def test_greet(): assert greet("Ray") == "Hello, Ray"
   def test_multiply(): assert multiply(3, 4) == 12
   def test_is_even(): assert is_even(2); assert not is_even(3)
   def test_factorial(): assert factorial(5) == 120
   ```
3. **Run tests**:

   ```bash
   pytest -v
   ```

---

### ✅ Day 3: Pytest Fixtures + Parametrization

1. **Create `pytest.ini`**:

   ```ini
   [pytest]
   addopts = -v
   testpaths = tests
   python_files = test_*.py
   ```
2. **Create `tests/conftest.py`** with a fixture:

   ```python
   import pytest

   @pytest.fixture
   def sample_user():
       return {"id": 1, "username": "tester", "role": "admin"}
   ```
3. **Use fixture in `tests/test_users.py`**:

   ```python
   def test_user_role(sample_user):
       assert sample_user["role"] == "admin"
   ```
4. **Add parametrized test in `tests/test_math_ops.py`**:

   ```python
   import pytest
   from src.day2_basics import multiply

   @pytest.mark.parametrize("a,b,result", [(2,2,4), (3,3,9)])
   def test_multiply_params(a, b, result):
       assert multiply(a, b) == result
   ```
5. **Run all tests**:

   ```bash
   pytest
   ```

---

### ✅ Day 4: FastAPI POST API + curl + TestClient

1. **Edit `src/main.py`** to add item creation:

   ```python
   from pydantic import BaseModel

   class Item(BaseModel):
       name: str
       price: float

   @app.post("/items")
   def create_item(item: Item):
       return {"message": f"Item '{item.name}' added successfully.", "price": item.price}
   ```
2. **Test with curl**:

   ```bash
   curl -X POST http://localhost:8000/items \
     -H "Content-Type: application/json" \
     -d '{"name": "Monitor", "price": 299.99}'
   ```
3. **Create `tests/test_items_api.py`**:

   ```python
   from fastapi.testclient import TestClient
   from src.main import app

   client = TestClient(app)

   def test_create_item():
       response = client.post("/items", json={"name": "Monitor", "price": 299.99})
       assert response.status_code == 200
       assert "message" in response.json()
   ```
4. **Run tests**:

   ```bash
   pytest
   ```

---

### ✅ Day 5: MongoDB Integration + Seeding + Async API Test

1. **Start MongoDB container**:

   ```bash
   docker run -d --name mongo -p 27017:27017 mongo
   ```

2. **Connect MongoDB in `src/main.py`**:

   ```python
   import motor.motor_asyncio
   client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
   db = client.testing_db
   products_collection = db.products
   ```

3. **Add `/products` endpoints**:

   ```python
   @app.post("/products")
   async def create_product(product: Product):
       new_product = product.model_dump()
       result = await products_collection.insert_one(new_product)
       return {"message": "Product added", "id": str(result.inserted_id)}

   @app.get("/products")
   async def list_products():
       products = []
       async for product in products_collection.find():
           product["_id"] = str(product["_id"])
           products.append(product)
       return products
   ```

4. **Create `data/seed.py`**:

   ```python
   import asyncio
   import motor.motor_asyncio

   async def seed():
       client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
       db = client.testing_db
       await db.products.insert_many([
           {"name": "Laptop", "price": 999.99},
           {"name": "Mouse", "price": 29.99}
       ])
   asyncio.run(seed())
   ```

   Run:

   ```bash
   python data/seed.py
   ```

5. **Create `tests/test_products_api.py`**:

   ```python
   import pytest
   import httpx

   @pytest.mark.asyncio
   async def test_create_product():
       async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
           response = await client.post("/products", json={"name": "Monitor", "price": 299.99})
       assert response.status_code == 200
   ```

6. **Start FastAPI app** (in a second terminal):

   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Run tests**:

   ```bash
   pytest
   ```

---

## 📁 Project Structure

```
.
├── .devcontainer/
│   └── devcontainer.json
├── src/
│   └── main.py
├── tests/
│   ├── test_day2_basics.py
│   ├── test_math_ops.py
│   ├── test_items_api.py
│   ├── test_products_api.py
│   ├── test_users.py
│   └── conftest.py
├── data/
│   └── seed.py
├── requirements.txt
├── pytest.ini
├── README.md
```

---

## ✅ Week 1 Outcome

* ✅ Fully reproducible Python/Testing environment using Codespaces
* ✅ Pytest for logic testing, fixtures, parametrized tests
* ✅ FastAPI API routes + testing with `TestClient`
* ✅ MongoDB async backend + data seeding + real async testing

---

## 🔜 Next: Day 6 – GraphQL with Strawberry + MongoDB Querying

---

## 🤝 Contributors & Support

This curriculum is maintained for educational use. PRs welcome!

Happy testing! 🚀

```

---

