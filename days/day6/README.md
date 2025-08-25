# Day 6

Got it ✅ — thanks for pointing that out earlier on Day 5. Let’s keep our Day 6 **aligned with the FastAPI + MongoDB track** we’ve been consistently building.

Here’s the detailed **Day 6** README content:

---

````markdown
# Day 6 – Updating and Deleting Products (REST CRUD)

Welcome to **Day 6** of the Python Testing Bootcamp.

By now, you have:
- A working FastAPI app with MongoDB (via Motor).
- Endpoints for creating (`POST /products`) and listing (`GET /products`).
- Tests that hit a real running server.

Today, we’ll expand our REST API with **update** and **delete** operations so we have the full CRUD cycle.

---

## 🎯 Goals

- Implement `PUT /products/{id}` → update a product.
- Implement `DELETE /products/{id}` → delete a product.
- Return proper **HTTP status codes** and error messages if a product isn’t found.
- Add tests for these new endpoints.
- Confirm full CRUD (Create, Read, Update, Delete) works end-to-end.

---

## 🛠 Step-by-step Instructions

### 1) Update `src/main.py` with new routes

We extend the same `ensure_mongo` pattern:

```python
# src/main.py (add to existing code)
from bson import ObjectId

# Helper: convert str -> ObjectId safely
def to_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

@app.put("/products/{id}")
async def update_product(id: str, product: Product, request: Request):
    products = ensure_mongo(request)
    obj_id = to_object_id(id)
    result = await products.update_one({"_id": obj_id}, {"$set": product.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated"}

@app.delete("/products/{id}")
async def delete_product(id: str, request: Request):
    products = ensure_mongo(request)
    obj_id = to_object_id(id)
    result = await products.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}
````

Key points:

* We validate `id` using `bson.ObjectId` → returns **400 Bad Request** if malformed.
* If no document matches, return **404 Not Found**.
* Otherwise return **200 OK** with a success message.

---

### 2) Test with curl (manual)

Create a product:

```bash
curl -s -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Chair","price":49.99}'
```

Copy the returned `"id"`.

Update it:

```bash
curl -s -X PUT http://127.0.0.1:8000/products/<ID_HERE> \
  -H "Content-Type: application/json" \
  -d '{"name":"Ergonomic Chair","price":89.99}'
```

Delete it:

```bash
curl -s -X DELETE http://127.0.0.1:8000/products/<ID_HERE>
```

Confirm deletion:

```bash
curl -s http://127.0.0.1:8000/products
```

---

### 3) Add tests

Create `tests/test_products_crud.py`:

```python
# tests/test_products_crud.py
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_update_and_delete_product():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        # 1. Create product
        r = await ac.post("/products", json={"name": "Temp Item", "price": 10.0})
        assert r.status_code == 200
        product_id = r.json()["id"]

        # 2. Update product
        r = await ac.put(f"/products/{product_id}", json={"name": "Updated Item", "price": 20.0})
        assert r.status_code == 200
        assert r.json()["message"] == "Product updated"

        # 3. Delete product
        r = await ac.delete(f"/products/{product_id}")
        assert r.status_code == 200
        assert r.json()["message"] == "Product deleted"

        # 4. Confirm product no longer exists
        r = await ac.put(f"/products/{product_id}", json={"name": "X", "price": 1})
        assert r.status_code == 404
        r = await ac.delete(f"/products/{product_id}")
        assert r.status_code == 404
```

Run:

```bash
pytest -q
```

---

## ✅ Summary

Today you completed **CRUD** with MongoDB:

* `POST /products` → Create
* `GET /products` → Read
* `PUT /products/{id}` → Update
* `DELETE /products/{id}` → Delete

You learned:

* How to handle **invalid ObjectIds** with clear errors.
* How to return **404 Not Found** for missing docs.
* How to test full lifecycle: create → update → delete → confirm gone.

**Next up (Day 7):** We’ll explore **testing strategies**, introducing **fixtures** for setup/teardown and preparing for our shift into **GraphQL** queries (Day 8).

```

---

```

Run:
```bash
./scripts/start.sh
```
