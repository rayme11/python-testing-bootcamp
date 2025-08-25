````markdown
# Day 13 – Validation, Errors, and Negative-Path Testing (REST + GraphQL)

Today you’ll harden the API surface and your tests:
- Add **input validation** and **clear error responses** to REST & GraphQL
- Introduce **enums** and **whitelists** for `order`/`sort_by`
- Return **structured mutation results** in GraphQL (not just strings)
- Write **negative-path tests** (invalid payloads, IDs, query params)
- Use **parameterized tests** to cover multiple invalid cases concisely

---

## 🎯 Goals

- Enforce constraints on **body** (price ≥ 0, name length), **query params** (limit/skip ranges), **sorting** (safe fields), **order** (enum).
- Surface **friendly errors** with correct **HTTP status codes** (400/404).
- In GraphQL, replace mutation strings with a **typed result**: `{ success, message }`.
- Add negative-path tests for both REST and GraphQL (including **invalid ObjectId**, **bad sort/order**, **bad pagination**).
- Learn to use `pytest.mark.parametrize` to keep tests readable and comprehensive.

---

## 🛠 Step-by-step instructions

### 1) Update `src/main.py` with validation + errors

```python
# src/main.py
from typing import List, Optional, Literal
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, Query
from pydantic import BaseModel, Field
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI(title="Testing Bootcamp API", version="13.0.0")

def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

class Product(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    price: float = Field(..., ge=0.0)

SORTABLE_FIELDS = {"name", "price"}

@app.get("/")
def root():
    return {"message": "API is running", "version": app.version}

@app.post("/products")
async def create_product(product: Product, request: Request):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.get("/products")
async def list_products(
    request: Request,
    limit: int = Query(100, ge=1, le=200),
    skip: int = Query(0, ge=0, le=10_000),
    sort_by: str = Query("name"),
    order: Literal["asc", "desc"] = Query("asc"),
    name_contains: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
):
    col = ensure_mongo(request)

    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Allowed: {sorted(SORTABLE_FIELDS)}")

    if (min_price is not None and max_price is not None) and (min_price > max_price):
        raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price.")

    query: dict = {}
    if name_contains:
        query["name"] = {"$regex": name_contains, "$options": "i"}
    if min_price is not None or max_price is not None:
        price = {}
        if min_price is not None:
            price["$gte"] = float(min_price)
        if max_price is not None:
            price["$lte"] = float(max_price)
        query["price"] = price

    sort_dir = 1 if order == "asc" else -1

    items = []
    cursor = col.find(query).skip(skip).limit(limit).sort(sort_by, sort_dir)
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

@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

@strawberry.type
class MutationResult:
    success: bool
    message: str

async def get_context(request: Request):
    return {"request": request}

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(
        self,
        info,
        name_contains: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: Optional[int] = 100,
        skip: Optional[int] = 0,
        sort_by: Optional[str] = "name",
        order: Optional[str] = "asc",
    ) -> List[ProductType]:
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200.")
        if skip < 0 or skip > 10_000:
            raise ValueError("skip must be between 0 and 10000.")
        if sort_by not in SORTABLE_FIELDS:
            raise ValueError(f"Invalid sort_by. Allowed: {sorted(SORTABLE_FIELDS)}")
        if order.lower() not in ("asc", "desc"):
            raise ValueError("order must be 'asc' or 'desc'")
        if (min_price is not None and max_price is not None) and (min_price > max_price):
            raise ValueError("min_price cannot be greater than max_price.")

        query: dict = {}
        if name_contains:
            query["name"] = {"$regex": name_contains, "$options": "i"}
        if (min_price is not None) or (max_price is not None):
            price = {}
            if min_price is not None:
                price["$gte"] = float(min_price)
            if max_price is not None:
                price["$lte"] = float(max_price)
            query["price"] = price

        sort_dir = 1 if order.lower() == "asc" else -1

        out: list[ProductType] = []
        cursor = col.find(query).skip(skip).limit(limit).sort(sort_by, sort_dir)
        async for doc in cursor:
            out.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return out

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> MutationResult:
        name = (product.name or "").strip()
        price = float(product.price)
        if len(name) < 2 or len(name) > 80:
            return MutationResult(success=False, message="name must be 2..80 characters.")
        if price < 0:
            return MutationResult(success=False, message="price must be >= 0.")

        col = ensure_mongo(info.context["request"])
        await col.insert_one({"name": name, "price": price})
        return MutationResult(success=True, message=f"Product '{name}' added.")

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> MutationResult:
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID.")

        name = (product.name or "").strip()
        price = float(product.price)
        if len(name) < 2 or len(name) > 80:
            return MutationResult(success=False, message="name must be 2..80 characters.")
        if price < 0:
            return MutationResult(success=False, message="price must be >= 0.")

        result = await col.update_one({"_id": oid}, {"$set": {"name": name, "price": price}})
        if result.matched_count == 0:
            return MutationResult(success=False, message="Product not found.")
        return MutationResult(success=True, message="Product updated.")

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> MutationResult:
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID.")
        result = await col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return MutationResult(success=False, message="Product not found.")
        return MutationResult(success=True, message="Product deleted.")

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
````

---

### 2) REST negative tests

`tests/test_rest_validation.py`

```python
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_create_product_invalid_body():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r1 = await ac.post("/products", json={"name": "A", "price": 10})
        r2 = await ac.post("/products", json={"name": "Valid Name", "price": -5})
    assert r1.status_code == 422
    assert r2.status_code == 422

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params, expected_status",
    [
        ({"limit": 0}, 422),
        ({"limit": 1000}, 422),
        ({"skip": -1}, 422),
        ({"skip": 100000}, 422),
        ({"sort_by": "unknown"}, 400),
        ({"min_price": 10, "max_price": 5}, 400),
        ({"order": "SIDEWAYS"}, 422),
    ],
)
async def test_rest_invalid_query_params(params, expected_status):
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get("/products", params=params)
    assert r.status_code == expected_status
```

---

### 3) GraphQL negative tests

`tests/test_graphql_negative.py`

```python
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str):
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query})

@pytest.mark.asyncio
async def test_graphql_add_product_invalid_inputs():
    q1 = 'mutation { addProduct(product: { name: "A", price: 9.99 }) { success message } }'
    q2 = 'mutation { addProduct(product: { name: "Good Name", price: -1.0 }) { success message } }'
    r1 = await gql(q1)
    r2 = await gql(q2)
    p1 = r1.json()["data"]["addProduct"]
    p2 = r2.json()["data"]["addProduct"]
    assert p1["success"] is False
    assert p2["success"] is False

@pytest.mark.asyncio
async def test_graphql_update_delete_invalid_id():
    up = 'mutation { updateProduct(id: "not-an-oid", product: { name: "Xy", price: 1 }) { success message } }'
    dd = 'mutation { deleteProduct(id: "not-an-oid") { success message } }'
    r1 = await gql(up)
    r2 = await gql(dd)
    p1 = r1.json()["data"]["updateProduct"]
    p2 = r2.json()["data"]["deleteProduct"]
    assert p1["success"] is False
    assert p2["success"] is False

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "q",
    [
        '{ allProducts(limit: 0) { name price } }',
        '{ allProducts(skip: -1) { name price } }',
        '{ allProducts(sortBy: "unknown") { name price } }',
        '{ allProducts(order: "SIDEWAYS") { name price } }',
        '{ allProducts(minPrice: 10, maxPrice: 5) { name price } }',
    ],
)
async def test_graphql_invalid_query_args(q):
    r = await gql(q)
    payload = r.json()
    assert "errors" in payload
```

---

## ✅ Summary

* REST now enforces stricter validation (body, query params).
* GraphQL now returns structured mutation results `{ success, message }`.
* Added **negative-path** and **parameterized tests**.
* System now surfaces **clear errors** instead of silent failures.

Next (Day 14): Add authentication stubs (API keys/bearer) and test protected endpoints.

```

Do you want me to also make a **script** that will automatically generate `day13/README.md` with this content so you don’t need to copy manually?
```

Run:
```bash
./scripts/start.sh
```
