# Day 16

Perfect 👍 Let’s continue the bootcamp with **Day 16**, using the same structured format we’ve been following (Goals → Step-by-step instructions → Summary), and building on everything you’ve done up to Day 15.

For Day 16, we’ll introduce **Authentication & Protected Routes** — a natural next step after CRUD, pagination, and validation. This will teach how to **secure your FastAPI + GraphQL APIs with JWT tokens**, and how to **test authentication flows**.

---

````markdown
# 📅 Day 16 – Authentication & Protected Routes

### 🎯 Goals
- Learn how to **secure APIs** with authentication.
- Add **JWT (JSON Web Tokens)** for login and authorization.
- Protect selected **REST** and **GraphQL** endpoints.
- Write tests for **login flow** and **access control**.

---

### 🛠 Step-by-Step Instructions

#### 1) Install JWT Dependency

Add `python-jose` for JWT handling and `passlib` for password hashing:

```bash
pip install python-jose passlib[bcrypt]
````

Update `requirements.txt`:

```
python-jose
passlib[bcrypt]
```

---

#### 2) Extend `src/main.py` with Authentication

At the top, import new dependencies:

```python
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
```

Add security configuration:

```python
SECRET_KEY = "supersecret"   # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

Add helper functions:

```python
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

#### 3) Add User Store (Fake In-Memory for Now)

Below Mongo setup:

```python
fake_users_db = {
    "alice": {
        "username": "alice",
        "hashed_password": get_password_hash("wonderland"),
        "role": "admin"
    },
    "bob": {
        "username": "bob",
        "hashed_password": get_password_hash("builder"),
        "role": "user"
    }
}
```

---

#### 4) Add Auth Routes

```python
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user["username"], "role": user["role"]}, expires_delta=access_token_expires)
    
    return {"access_token": token, "token_type": "bearer"}
```

---

#### 5) Protect a REST Endpoint

Modify `/products` list to require token:

```python
from fastapi import Security

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/products/secure")
async def list_products_secure(request: Request, user=Depends(get_current_user)):
    col = ensure_mongo(request)
    items = []
    async for doc in col.find().limit(5):
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return {"user": user["sub"], "items": items}
```

---

#### 6) Protect GraphQL Resolvers

Update `get_context`:

```python
async def get_context(request: Request):
    token = None
    if "authorization" in request.headers:
        token = request.headers["authorization"].split(" ")[1]
    user = None
    if token:
        try:
            user = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            pass
    return {"request": request, "user": user}
```

Update `Query`:

```python
@strawberry.type
class Query:
    @strawberry.field
    async def all_products_secure(self, info) -> List[ProductType]:
        user = info.context.get("user")
        if not user:
            raise Exception("Unauthorized")
        request: Request = info.context["request"]
        col = ensure_mongo(request)
        results = []
        async for doc in col.find().limit(5):
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results
```

---

#### 7) Tests for Authentication

Create `tests/test_auth.py`:

```python
import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_login_and_access_secure_products():
    async with AsyncClient(base_url=BASE) as ac:
        # login
        r = await ac.post("/token", data={"username": "alice", "password": "wonderland"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    async with AsyncClient(base_url=BASE) as ac:
        r2 = await ac.get("/products/secure", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["user"] == "alice"
    assert "items" in data
```

---

### ✅ Summary

* You learned **how authentication works in FastAPI** using JWT.
* You created a **login endpoint** (`/token`) and secured REST + GraphQL.
* You wrote **tests** for login and protected resource access.
* You now have a foundation to extend into **role-based access control** later.

---

### 🔍 How to Run & Check Coverage in Codespaces

1. Start everything:

```bash
./scripts/start.sh
```

2. Run tests:

```bash
pytest -q
```

3. With coverage:

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

4. Open coverage report:

```bash
python3 -m http.server 9000 --directory htmlcov
```

Forward **port 9000** in Codespaces → Open in browser.

```

---

👉 Next step (Day 17): we’ll expand authentication into **role-based access control (RBAC)**.  

Would you like me to already prep **Day 17** where we add admin-only mutations for GraphQL and secure REST endpoints further?
```

Run:
```bash
./scripts/start.sh
```
