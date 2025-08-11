Got it ✅
Here’s your **entire README** from **Day 1 to Day 10** in a single copy-and-paste block, including the **Quick Start** and the new **autostart with `/scripts/start.sh`** instructions.

---

````markdown
# Python Testing Bootcamp – Day-by-Day Learning Guide

## ⚡ Quick Start – Auto-Run Everything

If you’re running this inside **GitHub Codespaces**, you can start **MongoDB**, **FastAPI**, and **GraphQL** automatically using our `/scripts/start.sh` script.

### 1️⃣ Run the Autostart Script
```bash
chmod +x scripts/start.sh
./scripts/start.sh
````

This will:

* Start **MongoDB** in the background
* Launch **FastAPI** with hot-reload at port `8000`
* Keep both running so you can immediately test endpoints

You can then access:

* REST API root: `https://<your-forwarded-url>.github.dev/`
* GraphQL UI: `https://<your-forwarded-url>.github.dev/graphql`

### 2️⃣ Stop Services

To stop everything:

```bash
pkill -f uvicorn
pkill -f mongod
```

---

## 📅 Day 1 – Setting Up the Environment in GitHub Codespaces

**Objective:**
Set up a complete Python development environment in GitHub Codespaces with all required dependencies for API, MongoDB, and GraphQL development.

**Steps:**

1. **Create GitHub Repository**
2. **Enable Codespaces** in repo settings.
3. **Add `.devcontainer/devcontainer.json`**:

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
      "extensions": ["ms-python.python", "ms-python.vscode-pylance"]
    }
  }
}
```

4. **Create `requirements.txt`**:

```
pytest
pytest-asyncio
requests
httpx
fastapi
pymongo
motor
graphene
uvicorn
faker
```

5. **Add initial folder structure:**

```
.devcontainer/
scripts/
src/
tests/
data/
README.md
requirements.txt
```

6. **Create README.md** (this file).
7. **Commit & push** to GitHub.
8. **Open in Codespaces**.
9. **Verify Python version**:

```bash
python --version
```

---

## 📅 Day 2 – Python Refresher: Functions, Loops, Classes

**Objective:**
Review essential Python syntax for later use in API and test code.

**Steps:**

1. Create `src/day2_basics.py` with examples of:

   * Functions
   * Loops
   * Classes
2. Create `tests/test_day2_basics.py` with pytest assertions.
3. Run tests:

```bash
pytest -v
```

**Outcome:** You now have working unit tests verifying Python fundamentals.

---

## 📅 Day 3 – Pytest Fundamentals

**Objective:**
Learn to write and run tests with `pytest`.

**Steps:**

1. Install `pytest` (already in `requirements.txt`).
2. Create `pytest.ini`:

```ini
[pytest]
asyncio_mode=auto
```

3. Write simple test in `tests/test_math_ops.py`:

```python
def multiply(a, b):
    return a * b

def test_multiply():
    assert multiply(2, 3) == 6
```

4. Run:

```bash
pytest -v
```

**Outcome:** Able to execute tests and see pass/fail output.

---

## 📅 Day 4 – Project Structure & TestClient API Testing

**Objective:**
Organize project for API testing.

**Steps:**

1. Create `src/main.py` with FastAPI app and MongoDB connection.
2. Add sample `/products` GET & POST endpoints.
3. Create `tests/test_products_api.py` using `TestClient` from FastAPI:

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
```

4. Run:

```bash
pytest -v
```

---

## 📅 Day 5 – Review & Git Push

**Objective:**
Push working setup to GitHub.

**Steps:**

1. Run full test suite:

```bash
pytest -v
```

2. Commit & push:

```bash
git add .
git commit -m "Day 5 setup complete"
git push
```

**Outcome:** Codespaces environment with working API and tests stored in GitHub.

---

## 📅 Day 6 – Adding GraphQL Support

**Objective:**
Add GraphQL endpoint to FastAPI.

**Steps:**

1. Install `graphene` (already in requirements).
2. Update `src/main.py` to include GraphQL schema:

```python
import graphene
from fastapi import FastAPI
from starlette.graphql import GraphQLApp

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hi there!")

app = FastAPI()
app.add_route("/graphql", GraphQLApp(schema=graphene.Schema(query=Query)))
```

3. Run:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

4. Test in browser `/graphql`.

---

## 📅 Day 7 – Testing GraphQL Endpoints

**Objective:**
Write tests for GraphQL queries.

**Steps:**

1. Create `tests/test_graphql.py`:

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_graphql_hello():
    query = '{ hello }'
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    assert response.json()["data"]["hello"] == "Hi there!"
```

2. Run:

```bash
pytest -v
```

**Outcome:** GraphQL queries are tested alongside REST endpoints.

---

## 📅 Day 8 – MongoDB Auto-Start in Codespaces

**Objective:**
Run MongoDB automatically in Codespaces.

**Steps:**

1. Create `/scripts/start.sh`:

```bash
#!/bin/bash
mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
sleep 3
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

2. Make executable:

```bash
chmod +x scripts/start.sh
```

3. Run:

```bash
./scripts/start.sh
```

**Outcome:** MongoDB and FastAPI start with one command.

---

## 📅 Day 9 – GraphQL Products Query

**Objective:**
Extend GraphQL to list MongoDB products.

**Steps:**

1. Update GraphQL schema to query `products` from MongoDB.
2. Verify in `/graphql` UI.

---

## 📅 Day 10 – Seeding the Database with Test Data

**Objective:**
Populate MongoDB with fake data for testing.

**Steps:**

1. Install Faker:

```bash
pip install faker
```

2. Create `scripts/seed_data.py`:

```python
from faker import Faker
import motor.motor_asyncio
import asyncio

fake = Faker()

async def seed_products():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    products_collection = db.products
    await products_collection.delete_many({})
    products = [{"name": fake.word().title(), "price": round(fake.random_number(digits=3), 2)} for _ in range(10)]
    await products_collection.insert_many(products)
    print(f"✅ Seeded {len(products)} products.")

if __name__ == "__main__":
    asyncio.run(seed_products())
```

3. Run:

```bash
python scripts/seed_data.py
```

4. Verify REST:

```bash
curl -s http://localhost:8000/products | jq
```

5. Verify GraphQL:

```graphql
{
  products {
    name
    price
  }
}
```

6. Update `scripts/start.sh` to auto-seed before starting API:

```bash
#!/bin/bash
mkdir -p /data/db
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 &
sleep 3
python scripts/seed_data.py
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Outcome:** Database has test data ready every time you start.

```

---

Do you want me to go ahead and prepare **Day 11** so we start UI testing with Playwright? That would be the natural next step after Day 10.
```
