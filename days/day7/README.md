# Day 7

Perfect 👍 Let’s continue with **Day 7** while staying aligned with our **FastAPI + MongoDB + GraphQL training track**.

Here’s the detailed README content for **Day 7**:

---

````markdown
# Day 7 – Improving Tests with Fixtures and Setup/Teardown

Welcome to **Day 7** of the Python Testing Bootcamp.

At this point, your project has:
- A FastAPI application.
- MongoDB connected via Motor.
- REST endpoints for Create, Read, Update, Delete (CRUD).
- Basic tests for products.

But our tests are starting to **repeat code** (e.g., creating/deleting products in multiple files).  
Today we’ll make them **cleaner and more maintainable** by introducing **pytest fixtures**.

---

## 🎯 Goals

- Learn what **fixtures** are in pytest.
- Create reusable fixtures for:
  - **HTTP client** (`AsyncClient`) setup/teardown.
  - **MongoDB test cleanup**.
- Refactor tests to remove duplication.
- Understand why fixtures are critical for **scalable test suites**.

---

## 📖 Theory – Fixtures in Pytest

- **What is a fixture?**  
  A fixture is a function decorated with `@pytest.fixture` that provides a setup/teardown mechanism for tests.  
  They let you **reuse test dependencies** without repeating code.

- **Why use them?**  
  - Keep test code DRY (Don’t Repeat Yourself).  
  - Ensure every test starts from a **known clean state**.  
  - Separate setup logic from test logic.  
  - Improve readability and maintainability.

- **Scope:** Fixtures can run:
  - `function` (default) → once per test.  
  - `module` → once per file.  
  - `session` → once for the whole test run.

---

## 🛠 Step-by-step Instructions

### 1) Create a test fixtures file

Create `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from src.main import app

MONGO_URL = "mongodb://localhost:27017"
TEST_DB = "test_products_db"

@pytest.fixture(scope="function")
async def test_client():
    """Fixture for AsyncClient against FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="function", autouse=True)
async def clear_db():
    """Ensure DB is clean before each test."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[TEST_DB]
    await db.products.delete_many({})
    yield
    await db.products.delete_many({})
    client.close()
````

What happens here:

* `test_client` gives you a reusable `AsyncClient` bound to FastAPI.
* `clear_db` automatically runs **before and after every test**, ensuring MongoDB is clean.

---

### 2) Refactor existing tests to use fixtures

Example: `tests/test_products_api.py`:

```python
# tests/test_products_api.py
import pytest

@pytest.mark.asyncio
async def test_create_product(test_client):
    r = await test_client.post("/products", json={"name": "Book", "price": 15.99})
    assert r.status_code == 200
    assert "id" in r.json()

@pytest.mark.asyncio
async def test_list_products(test_client):
    # Create one product
    await test_client.post("/products", json={"name": "Pen", "price": 1.99})
    
    # Fetch all products
    r = await test_client.get("/products")
    assert r.status_code == 200
    products = r.json()
    assert isinstance(products, list)
    assert len(products) == 1
```

Notice:

* No more boilerplate for creating the client.
* No need to clean the database manually.
* Tests are **shorter, more readable, and reliable**.

---

### 3) Run tests

```bash
pytest -v
```

You should see all tests passing and a clean DB for each test run.

---

## ✅ Summary

Today you:

* Learned about **pytest fixtures** and why they matter.
* Created reusable fixtures for **HTTP client** and **DB cleanup**.
* Refactored tests to be **cleaner and safer**.
* Built a strong foundation for scaling test coverage as the project grows.

Next up (**Day 8**): We’ll start exploring **GraphQL with Strawberry + FastAPI**, writing our first GraphQL schema and queries!

```

---

```


Run:
```bash
./scripts/start.sh
```
