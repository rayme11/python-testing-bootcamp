# Day 17

````markdown
# 📅 Day 17 – Role-Based Access Control (RBAC) for REST & GraphQL

### 🎯 Goals
- Add **roles** (`admin`, `user`) to our auth story.
- Enforce **RBAC** on sensitive operations (create/update/delete).
- Protect **REST admin routes** and **GraphQL mutations** using the JWT’s `role` claim.
- Write tests for **unauthorized**, **forbidden**, and **allowed** paths.

---

## 🛠 Step-by-Step Instructions

> Prereqs: Your Day 16 auth is in place (JWT login at `/token`, context in GraphQL).  
> Start everything as usual in a Codespaces terminal:
>
> ```bash
> ./scripts/start.sh
> ```

### 1) Update `src/main.py` – add role helpers

Add these imports (near your other FastAPI imports):

```python
from fastapi import Depends, Security
from fastapi import status
````

Add **role helpers** (place near your auth helpers in Day 16):

```python
def has_role(user: dict | None, required: str) -> bool:
    if not user:
        return False
    return user.get("role") == required

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Reuse your Day 16 SECRET_KEY/ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # payload contains { sub, role, exp }
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_role(required_role: str):
    async def _inner(user: dict = Depends(get_current_user)):
        if not has_role(user, required_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return _inner
```

> You now have:
>
> * `get_current_user` → validates/decodes JWT and returns `{sub, role}`
> * `require_role("admin")` → raises **403** unless `role == "admin"`

### 2) REST: add **admin-only** endpoints (new routes)

**Keep your existing `/products` endpoints unchanged** to avoid breaking earlier exercises.
Add admin-only routes under an `/admin` prefix:

```python
from pydantic import BaseModel

class AdminProduct(BaseModel):
    name: str
    price: float

@app.post("/admin/products", status_code=201)
async def admin_create_product(product: AdminProduct, request: Request, user=Depends(require_role("admin"))):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.put("/admin/products/{pid}")
async def admin_update_product(pid: str, product: AdminProduct, request: Request, user=Depends(require_role("admin"))):
    col = ensure_mongo(request)
    try:
        oid = ObjectId(pid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    res = await col.update_one({"_id": oid}, {"$set": product.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated"}

@app.delete("/admin/products/{pid}", status_code=204)
async def admin_delete_product(pid: str, request: Request, user=Depends(require_role("admin"))):
    col = ensure_mongo(request)
    try:
        oid = ObjectId(pid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    res = await col.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return
```

> These endpoints **require** a Bearer token for a user with `role: "admin"`.

### 3) GraphQL: enforce **admin** on mutations

> Your Day 14/15 work likely returned a `MutationResult` object for mutations.
> If not present yet, add:

```python
from typing import Optional

@strawberry.type
class MutationResult:
    success: bool
    message: str
    id: Optional[str] = None
```

Now, **require admin** on GraphQL mutations by checking the context user:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> MutationResult:
        user = info.context.get("user")
        if not has_role(user, "admin"):
            return MutationResult(success=False, message="Forbidden: admin only")
        col = ensure_mongo(info.context["request"])
        result = await col.insert_one({"name": product.name, "price": float(product.price)})
        return MutationResult(success=True, message="Product added", id=str(result.inserted_id))

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> MutationResult:
        user = info.context.get("user")
        if not has_role(user, "admin"):
            return MutationResult(success=False, message="Forbidden: admin only")
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID")

        res = await col.update_one({"_id": oid}, {"$set": {"name": product.name, "price": float(product.price)}})
        if res.matched_count == 0:
            return MutationResult(success=False, message="Product not found")
        return MutationResult(success=True, message="Product updated", id=id)

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> MutationResult:
        user = info.context.get("user")
        if not has_role(user, "admin"):
            return MutationResult(success=False, message="Forbidden: admin only")
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID")

        res = await col.delete_one({"_id": oid})
        if res.deleted_count == 0:
            return MutationResult(success=False, message="Product not found")
        return MutationResult(success=True, message="Product deleted", id=id)
```

> Your **queries** (e.g., `allProducts`) can stay public or you can add secure variants (e.g., `all_products_secure`) like Day 16.

### 4) Tests – new RBAC coverage

Create **`tests/test_rbac.py`**:

```python
# description: login as admin, create product via REST admin route, OK
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def _login(username: str, password: str) -> str:
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post("/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_admin_can_create_product_rest():
    token = await _login("alice", "wonderland")  # alice is admin from Day 16
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post(
            "/admin/products",
            json={"name": "RBAC-Monitor", "price": 123.45},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["message"] == "Product added"
    assert "id" in body

# description: login as user, attempt admin route, expect 403
@pytest.mark.asyncio
async def test_user_cannot_create_product_rest():
    token = await _login("bob", "builder")  # bob is user
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.post(
            "/admin/products",
            json={"name": "Should-Fail", "price": 10.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 403

# description: GraphQL addProduct requires admin; user gets Forbidden
@pytest.mark.asyncio
async def test_graphql_add_product_forbidden_for_user():
    token = await _login("bob", "builder")
    q = """
    mutation {
      addProduct(product: { name: "GQL-User-Forbidden", price: 9.99 }) {
        success
        message
        id
      }
    }
    """
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        r = await ac.post("/graphql", json={"query": q}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    payload = r.json()
    data = payload.get("data", {}).get("addProduct")
    assert data is not None
    assert data["success"] is False
    assert "Forbidden" in data["message"]

# description: GraphQL addProduct works with admin
@pytest.mark.asyncio
async def test_graphql_add_product_allowed_for_admin():
    token = await _login("alice", "wonderland")
    q = """
    mutation {
      addProduct(product: { name: "GQL-Admin-OK", price: 49.99 }) {
        success
        message
        id
      }
    }
    """
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        r = await ac.post("/graphql", json={"query": q}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    payload = r.json()
    data = payload.get("data", {}).get("addProduct")
    assert data is not None
    assert data["success"] is True
    assert data["id"] is not None
```

> These tests cover:
>
> * **Admin allow** (REST + GraphQL)
> * **User forbid** (REST + GraphQL)

---

## ✅ Summary (What You Accomplished & Learned)

* Introduced **RBAC** with helpers to validate a user’s **role** from the JWT.
* Secured **admin-only REST endpoints** under `/admin/products`.
* Enforced **admin-only GraphQL mutations** (`addProduct`, `updateProduct`, `deleteProduct`).
* Wrote tests covering:

  * **Happy path** (admin succeeds)
  * **Forbidden** path (user receives 403 / mutation returns `{ success: false }`)

This mirrors real production constraints where write operations (create/update/delete) are restricted to privileged roles.

---

## 🔍 Pytest & Coverage in Codespaces (Quick Reference)

**Run the app & DB:**

```bash
./scripts/start.sh
```

**Run tests:**

```bash
pytest -q
```

**Coverage in terminal + HTML:**

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

**Open coverage in Codespaces browser (recommended):**

```bash
python3 -m http.server 9000 --directory htmlcov
```

Then open **Ports** tab → forward **9000** → click the URL to view the HTML report.

---

```
::contentReference[oaicite:0]{index=0}
```

Run:
```bash
./scripts/start.sh
```
