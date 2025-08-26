Absolutely! Here’s **Day 15** as a single, copy-paste friendly README block that includes the new **JWT auth + MutationResult** changes **and** a dedicated section on **running pytest with coverage and viewing the HTML report in the Codespaces browser**.

---

````markdown
# 📅 Day 15 – Securing GraphQL Mutations with Auth + MutationResult (FastAPI + JWT)

This day builds on Days 1–14 (MongoDB, FastAPI, Strawberry GraphQL, pagination/sorting, real-server tests, coverage).  
You’ll add **JWT authentication** and standardize GraphQL mutation responses to `{ success, message }`.  
You’ll also learn how to run **pytest** with **coverage** and view the HTML coverage report in **GitHub Codespaces**.

---

## 🎯 Goals

- Add **JWT login** endpoint that issues **access tokens**.
- Protect GraphQL **mutations** (add/update/delete product) with **Bearer** tokens.
- Standardize mutation results using `MutationResult { success, message }`.
- Update tests to log in first and assert against the new mutation shape.
- Generate **coverage** (terminal + HTML) and **view HTML coverage in Codespaces**.

---

## 🛠 Step-by-Step Instructions

> Prereqs: Start your dev environment as usual:
>
> ```bash
> ./scripts/start.sh
> ```
> This launches **MongoDB** and **FastAPI** (and seeds sample data).

### 1) Dependencies

Add to `requirements.txt` (if not already present):

````

python-jose\[cryptography]
passlib\[bcrypt]
pytest-cov

````

Install:

```bash
pip install -r requirements.txt
````

---

### 2) Extend `src/main.py` – JWT + Auth Helpers

Add these imports near the top (alongside your existing imports):

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
```

Add config and helpers (place below imports and above your FastAPI routes):

```python
SECRET_KEY = "super-secret-key"  # for demo only; load from env in real apps
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simple in-memory user for the training exercise
fake_users_db = {
    "alice": {"username": "alice", "hashed_password": pwd_context.hash("wonderland")}
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str) -> dict | None:
    user = fake_users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return {"username": user["username"]}

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return {"username": user["username"]}
```

Add REST login and a simple “who am I” endpoint (place near your other REST routes):

```python
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"]}
```

For GraphQL auth in resolvers, add this helper (below your existing code, e.g., near the GraphQL types):

```python
def _require_bearer_username_from_request(request: Request) -> str:
    # Expect header: Authorization: Bearer <token>
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

### 3) Standardize GraphQL Mutations – `MutationResult`

Add the result type near your other Strawberry types:

```python
import strawberry

@strawberry.type
class MutationResult:
    success: bool
    message: str
```

Update your GraphQL mutations (inside `class Mutation`) to require auth and return `MutationResult`:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> MutationResult:
        request = info.context["request"]
        user = _require_bearer_username_from_request(request)
        col = ensure_mongo(request)
        await col.insert_one({"name": product.name, "price": float(product.price)})
        return MutationResult(success=True, message=f"Product '{product.name}' added by {user}.")

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> MutationResult:
        request = info.context["request"]
        _ = _require_bearer_username_from_request(request)
        col = ensure_mongo(request)
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID.")
        result = await col.update_one({"_id": oid}, {"$set": {"name": product.name, "price": float(product.price)}})
        if result.matched_count == 0:
            return MutationResult(success=False, message="Product not found.")
        return MutationResult(success=True, message="Product updated.")

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> MutationResult:
        request = info.context["request"]
        _ = _require_bearer_username_from_request(request)
        col = ensure_mongo(request)
        try:
            oid = ObjectId(id)
        except Exception:
            return MutationResult(success=False, message="Invalid product ID.")
        result = await col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return MutationResult(success=False, message="Product not found.")
        return MutationResult(success=True, message="Product deleted.")
```

> Note: Queries like `allProducts` remain public; only **mutations** require a token.

---

### 4) Update Tests – GraphQL now returns `{ success, message }`

**`tests/test_graphql_api.py`** (replace with this complete file):

```python
import asyncio
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str, token: str | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query}, headers=headers)

async def wait_for_up(url: str, attempts: int = 30, delay: float = 0.2):
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
async def test_graphql_add_product_mutation():
    assert await wait_for_up(f"{BASE}/"), "API not reachable"

    # Login to get token
    async with AsyncClient(base_url=BASE) as ac:
        login = await ac.post("/token", data={"username":"alice","password":"wonderland"})
        token = login.json()["access_token"]

    q = """
    mutation {
      addProduct(product: { name: "Keyboard", price: 49.99 }) {
        success
        message
      }
    }
    """
    r = await gql(q, token)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["data"]["addProduct"]["success"] is True

@pytest.mark.asyncio
async def test_graphql_all_products_query():
    q = """
    {
      allProducts {
        name
        price
      }
    }
    """
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert isinstance(payload["data"]["allProducts"], list)

@pytest.mark.asyncio
async def test_graphql_filter_by_name_and_price():
    q1 = """{ allProducts(nameContains: "Preloaded") { name price } }"""
    r1 = await gql(q1)
    assert r1.status_code == 200, r1.text
    data1 = r1.json()["data"]["allProducts"]
    assert len(data1) >= 0  # some envs may seed differently
    if data1:
        assert all("Preloaded" in p["name"] for p in data1)

    q2 = """{ allProducts(minPrice: 10.0, maxPrice: 15.0) { name price } }"""
    r2 = await gql(q2)
    assert r2.status_code == 200, r2.text
    data2 = r2.json()["data"]["allProducts"]
    if data2:
        assert all(10.0 <= p["price"] <= 15.0 for p in data2)

@pytest.mark.asyncio
async def test_graphql_update_and_delete_product():
    # Login to get token
    async with AsyncClient(base_url=BASE) as ac:
        login = await ac.post("/token", data={"username":"alice","password":"wonderland"})
        token = login.json()["access_token"]

    # Create via REST to get ID
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        create = await ac.post("/products", json={"name": "TempProd", "price": 9.99})
    assert create.status_code == 200, create.text
    pid = create.json()["id"]

    update_q = f"""
    mutation {{
      updateProduct(id: "{pid}", product: {{ name: "UpdatedProd", price: 19.99 }}) {{
        success
        message
      }}
    }}
    """
    r1 = await gql(update_q, token)
    assert r1.status_code == 200, r1.text
    assert r1.json()["data"]["updateProduct"]["success"] is True

    delete_q = f"""
    mutation {{
      deleteProduct(id: "{pid}") {{
        success
        message
      }}
    }}
    """
    r2 = await gql(delete_q, token)
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"]["deleteProduct"]["success"] is True
```

(Your REST tests in `tests/test_products_api.py` remain valid and unchanged.)

---

## 🧪 Using Pytest & Viewing Coverage in Codespaces (Browser)

You can run tests and generate coverage **in the terminal** or **open an HTML report in the Codespaces browser**.

### Option A – Serve `htmlcov/` on a Codespaces Port (recommended)

1. Run tests and produce HTML coverage:

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

This prints coverage to the terminal and creates `htmlcov/index.html`.

2. Serve the coverage folder on port **9000**:

```bash
python -m http.server 9000 --directory htmlcov
```

3. In Codespaces:

   * Open the **Ports** tab.
   * Find port **9000** → set **Visibility** to **Public** (if needed).
   * Click the URL (it will look like `https://<hash>-9000.app.github.dev/`) to open the coverage report in the browser.

### Option B – Open locally inside Codespaces webview (if you prefer)

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
xdg-open htmlcov/index.html  # May open a preview tab in the editor (depends on image)
```

> If `xdg-open` isn’t available, stick with **Option A**.

**Re-run quickly** while iterating:

```bash
pytest -q
pytest --cov=. --cov-report=term-missing --cov-report=html
```

---

## 🧠 Theory & Rationale

* **JWT** is a signed token containing claims (we store `sub=username`). It is stateless and verified by the API on each request.
* **OAuth2PasswordBearer** extracts `Authorization: Bearer <token>` and hands it to our `get_current_user`.
* **Strawberry context** gives resolvers access to the underlying FastAPI `request`, so we can enforce auth per mutation.
* **MutationResult** is a GraphQL best practice: clients don’t have to parse strings; they read `{ success, message }` reliably.
* **Coverage** shows what’s tested and what’s missing; the HTML view makes it easy to drill into untested lines.

---

## ✅ Summary (What You Accomplished)

* Implemented **JWT login** (`/token`) and a `GET /me` endpoint.
* Secured GraphQL **mutations** with Bearer tokens (queries remain public).
* Standardized mutation results with `MutationResult { success, message }`.
* Updated tests to **log in**, send tokens, and assert success.
* Generated and **viewed coverage reports** inside Codespaces via a public port.

---

## 🔎 Quick Sanity Checks

**Login & use token (REST):**

```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=wonderland"

# Then:
curl http://127.0.0.1:8000/me -H "Authorization: Bearer <PASTE_TOKEN_HERE>"
```

**GraphQL mutation with token (GraphiQL Headers):**

```json
{ "Authorization": "Bearer <PASTE_TOKEN_HERE>" }
```

**Run tests + coverage (HTML):**

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
python -m http.server 9000 --directory htmlcov
# Open via Codespaces Ports tab
```

```

---


```
