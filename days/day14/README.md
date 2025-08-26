# Day 14

Here’s a **clean Day 14 guide** in the same style as Day 13, focused on **Authentication & Authorization**. It assumes everything from Days 1–13 is in place (FastAPI, MongoDB, Strawberry GraphQL, validation, testing, etc.).

---

````markdown
# Day 14 – Authentication & Protected Endpoints (API Keys / Bearer Tokens)

Today we’ll introduce **authentication** concepts into our project.  
Until now, all endpoints (REST + GraphQL) were public. Real-world APIs require **auth checks**.  

We’ll add:
- A **simple API key system** for REST endpoints
- A **Bearer token system** for GraphQL resolvers
- Middleware/utility helpers to validate keys
- Tests for **protected routes** (both success and failure)

---

## 🎯 Goals

- Understand difference between **authentication** (who you are) and **authorization** (what you can do).
- Implement **API key auth** in REST endpoints using FastAPI `Depends`.
- Implement **Bearer token auth** in GraphQL using Strawberry `context`.
- Add **negative tests** for missing/invalid tokens.
- Learn how this paves the way for **real auth systems** (JWT, OAuth2).

---

## 🛠 Step-by-step instructions

### 1) Update `src/main.py` with API key + bearer logic

```python
# src/main.py (auth additions)

from fastapi import Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

# Define constants (in real apps use env vars / DB)
VALID_API_KEYS = {"secret123", "topkey456"}
VALID_BEARER_TOKENS = {"bearer-abc-123"}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing API Key")
    return api_key

def verify_bearer(credentials: HTTPAuthorizationCredentials = Security(http_bearer)):
    if not credentials or credentials.credentials not in VALID_BEARER_TOKENS:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing Bearer token")
    return credentials.credentials
````

---

### 2) Apply auth to REST endpoints

```python
@app.post("/secure/products")
async def secure_create_product(product: Product, request: Request, api_key: str = Depends(verify_api_key)):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Secure product added", "id": str(result.inserted_id)}
```

This endpoint requires header:

```
X-API-Key: secret123
```

---

### 3) Apply auth to GraphQL resolvers

```python
@strawberry.type
class SecureQuery:
    @strawberry.field
    async def secret_products(self, info) -> List[ProductType]:
        request: Request = info.context["request"]
        # Perform auth
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise Exception("Unauthorized: Bearer token required")
        token = auth.split(" ")[1]
        if token not in VALID_BEARER_TOKENS:
            raise Exception("Forbidden: Invalid Bearer token")

        col = ensure_mongo(request)
        results = []
        async for doc in col.find().limit(3):
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results

# Merge schemas
schema = strawberry.Schema(query=Query | SecureQuery, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
```

Now GraphQL queries like:

```graphql
{
  secretProducts { name price }
}
```

require:

```
Authorization: Bearer bearer-abc-123
```

---

### 4) Tests for Auth

**REST tests** (`tests/test_rest_auth.py`)

```python
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_secure_rest_with_valid_key():
    async with AsyncClient(base_url=BASE) as ac:
        r = await ac.post("/secure/products",
                          headers={"X-API-Key": "secret123"},
                          json={"name": "SecureProd", "price": 5.5})
    assert r.status_code == 200
    assert "id" in r.json()

@pytest.mark.asyncio
async def test_secure_rest_missing_key():
    async with AsyncClient(base_url=BASE) as ac:
        r = await ac.post("/secure/products", json={"name": "NoKey", "price": 1.0})
    assert r.status_code == 403
```

**GraphQL tests** (`tests/test_graphql_auth.py`)

```python
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query, headers=None):
    async with AsyncClient(base_url=BASE) as ac:
        return await ac.post("/graphql", json={"query": query}, headers=headers or {})

@pytest.mark.asyncio
async def test_graphql_secret_with_valid_bearer():
    q = "{ secretProducts { name price } }"
    r = await gql(q, headers={"Authorization": "Bearer bearer-abc-123"})
    assert r.status_code == 200
    assert "secretProducts" in r.text

@pytest.mark.asyncio
async def test_graphql_secret_invalid_bearer():
    q = "{ secretProducts { name price } }"
    r = await gql(q, headers={"Authorization": "Bearer wrong-token"})
    assert r.status_code == 200
    payload = r.json()
    assert "errors" in payload


**GraphQL tests**
Secure REST (valid key):

curl -s -X POST "http://127.0.0.1:8000/secure/products" \
  -H "X-API-Key: secret123" \
  -H "Content-Type: application/json" \
  -d '{"name":"Premium Mouse Pad","price":12.99}' | jq


Secure REST (missing key):

curl -s -X POST "http://127.0.0.1:8000/secure/products" \
  -H "Content-Type: application/json" \
  -d '{"name":"No Auth","price":1.00}' | jq


Secure GraphQL (valid bearer):

curl -s -X POST "http://127.0.0.1:8000/graphql" \
  -H "Authorization: Bearer bearer-abc-123" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ secretProducts { name price } }"}' | jq


Secure GraphQL (invalid bearer):

curl -s -X POST "http://127.0.0.1:8000/graphql" \
  -H "Authorization: Bearer nope" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ secretProducts { name price } }"}' | jq


Run tests:

pytest -q

    
```

---

## 🧠 Theory Recap

* **API Keys**: Simple, static strings shared between client and server. Best for service-to-service auth, but **not secure** if exposed.
* **Bearer Tokens**: Represent identity (user or service). Usually JWTs with expiry + claims. In production, you’d verify signature & expiry.
* **FastAPI**: Provides `Depends`, `Security`, and `fastapi.security` helpers to enforce auth at endpoint level.
* **Strawberry GraphQL**: Auth must be handled manually (in resolvers, or via middleware) since GraphQL is schema-driven.
* **Negative Testing**: Ensures your system rejects invalid/missing credentials and surfaces the right errors.

---

## ✅ Summary

* REST `/secure/products` requires **X-API-Key**.
* GraphQL `secretProducts` requires **Bearer token**.
* Tests validate both **happy path** and **failure path**.
* You now understand **auth basics** and how to integrate them into FastAPI + Strawberry.

Next (Day 15): Implement **JWT auth** with expiry and integrate into tests.

```

---

```

Run:
```bash
./scripts/start.sh
```
