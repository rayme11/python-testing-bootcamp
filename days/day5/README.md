# Day 5

You’re absolutely right—my Day 5 write-up drifted into SQLite/SQLAlchemy, which doesn’t match our MongoDB + FastAPI track. Thanks for catching that! Here’s the **correct Day 5** that stays fully aligned with what we built earlier (FastAPI + **MongoDB via Motor**), and also reflects our **latest stable patterns** (lazy Mongo init, testing against the real Uvicorn server).

---

````markdown
# Day 5 – REST `/products` with MongoDB (Motor) ✅

Welcome to **Day 5** of the Python Testing Bootcamp.

Today we add real persistence to our REST API using **MongoDB** with the async **Motor** driver. We’ll expose two endpoints:

- `POST /products` → create a product
- `GET /products` → list products (with simple pagination/sorting compatible with later days)

We’ll keep everything consistent with our **latest stable setup**:
- **Lazy Mongo initialization** (no global clients; safe for tests & hot reload)
- **Pydantic** for input validation
- **Tests hit a real Uvicorn server** (not in-process) to avoid async loop issues

---

## 🎯 Goals

- Wire up **MongoDB (Motor)** to FastAPI using a **lazy initializer**.
- Implement `POST /products` and `GET /products`.
- Write REST tests that call the **running server** at `http://127.0.0.1:8000`.
- Verify the endpoints with **curl** and **pytest**.

---

## 🛠 Step-by-step instructions

> **Prereq:** Make sure your dev container has our dependencies:
> `fastapi`, `uvicorn`, `motor`, `pydantic`, `httpx`, `pytest`, `pytest-asyncio`, `faker`, `pytest-cov`  
> (These were added in earlier days; no changes needed to `requirements.txt` for today.)

### 1) Start MongoDB + API (Codespaces)

Use the autostart script we set up:

```bash
chmod +x scripts/start.sh
./scripts/start.sh
````

That will:

* Start **mongod** locally (127.0.0.1:27017)
* (Optionally) seed data if your script includes seeding
* Start **Uvicorn** on **0.0.0.0:8000**

**Health check:**

```bash
curl -i http://127.0.0.1:8000/
```

You should see `200 OK` and a JSON message.

---

### 2) Ensure your `src/main.py` has lazy Mongo + REST endpoints

> If your `main.py` already includes GraphQL/other routes from later days, **keep them**. Just ensure the **lazy Mongo helper** and these two REST endpoints exist.

```python
# src/main.py
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import motor.motor_asyncio

app = FastAPI()

# ---------- Lazy Mongo initializer ----------
def ensure_mongo(request: Request):
    """
    Create and memoize Mongo objects on app.state so we don't
    create global clients or re-open per request.
    """
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# ---------- Pydantic models ----------
class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0.0)

# ---------- Health check ----------
@app.get("/")
def root():
    return {"message": "API is running"}

# ---------- Create product ----------
@app.post("/products")
async def create_product(product: Product, request: Request):
    products = ensure_mongo(request)
    doc = product.model_dump()
    result = await products.insert_one(doc)
    return {"message": "Product added", "id": str(result.inserted_id)}

# ---------- List products (simple pagination/sorting) ----------
@app.get("/products")
async def list_products(
    request: Request,
    limit: int = 100,
    skip: int = 0,
    sort_by: str = "name",
    order: str = "asc",
):
    products = ensure_mongo(request)
    sort_dir = 1 if order.lower() == "asc" else -1
    out: List[dict] = []
    cursor = products.find().skip(skip).limit(limit).sort(sort_by, sort_dir)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out
```

**Why lazy init?**
We attach the Mongo client/DB/collection to `app.state` on first use. This avoids:

* global clients (bad for reload/tests)
* re-creating clients per request (wasteful)
* “event loop is closed” errors in tests

---

### 3) Test via curl (manual smoke test)

Create:

```bash
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Monitor","price":299.99}'
```

List:

```bash
curl -s "http://127.0.0.1:8000/products?limit=5&skip=0&sort_by=price&order=desc" | jq
```

You should see your product(s) back.

---

### 4) Add REST tests that hit the real server

Create or update `tests/test_products_api.py`:

```python
# tests/test_products_api.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def wait_for_up(url: str, attempts: int = 30, delay: float = 0.2):
    """Tiny helper so tests don't flake if server is still booting."""
    import asyncio
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
async def test_create_product():
    assert await wait_for_up(f"{BASE}/"), "API not reachable at /"
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post("/products", json={"name": "Desk Lamp", "price": 39.99})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"] == "Product added"
    assert "id" in body

@pytest.mark.asyncio
async def test_list_products():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products", params={"limit": 5, "skip": 0, "sort_by": "name", "order": "asc"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
```

**Run tests** (in **another terminal** while the server is running):

```bash
pytest -q
```

---

## ✅ Summary (what you accomplished & learned)

* You connected **FastAPI** to **MongoDB** using the async **Motor** driver.
* You implemented **POST /products** (create) and **GET /products** (list) with **pagination/sorting** options that match our later days.
* You used a **lazy Mongo initializer** (`ensure_mongo`) to avoid common async/test pitfalls.
* You wrote **integration tests** that call the **real running server**, which reflects production behavior and removes “event loop is closed” issues.


```
::contentReference[oaicite:0]{index=0}
```

Run:
```bash
./scripts/start.sh
```
