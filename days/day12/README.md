# Day 12

````markdown
# Day 12 – Pagination, Sorting & Test Coverage (REST + GraphQL)

Today you’ll add **pagination & sorting** to both REST and GraphQL (compatible with the Day-11 lazy-Mongo + Strawberry context setup), and generate **coverage reports** (terminal + HTML). You’ll also see a reliable way to open the HTML coverage in **Codespaces** via the Ports tab.

---

## 🎯 Goals

- Expose `limit`, `skip`, `sort_by`, `order` on **REST** and `limit`, `skip`, `sortBy`, `order` on **GraphQL**.
- Keep filters working together with pagination/sorting (e.g., `name_contains`, `min_price`, `max_price`).
- Add tests for REST + GraphQL pagination/sorting that hit the **real running server**.
- Produce **coverage** reports in the terminal and as **HTML**; learn reliable ways to open the report in Codespaces.

---

## 🛠 Step-by-step instructions

> **Prerequisites**
> - You’ve completed **Day 11** and your app runs with `./scripts/start.sh`
> - MongoDB is running and seeded by your script
> - `requirements.txt` already includes: `pytest-cov`

### 1) Verify your API supports pagination, sorting & filters (Day-11 code already has these)

If you used the Day-11 `src/main.py`, you already expose:

- **REST**: `/products?limit=…&skip=…&sort_by=…&order=…&name_contains=…&min_price=…&max_price=…`
- **GraphQL**: 
  ```graphql
  {
    allProducts(
      limit: 10,
      skip: 0,
      sortBy: "price",
      order: "desc",
      nameContains: "desk",
      minPrice: 5.0,
      maxPrice: 50.0
    ) { name price }
  }
````

Quick local sanity checks while the server runs:

```bash
# REST: top 5 by price desc
curl "http://127.0.0.1:8000/products?limit=5&skip=0&sort_by=price&order=desc"

# GraphQL: top 5 by price desc
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ allProducts(limit:5, sortBy:\"price\", order:\"desc\") { name price } }"}'
```

You should receive valid JSON arrays (REST) or a GraphQL `data` payload.

---

### 2) Add REST pagination/sorting test

Create/append to `tests/test_products_api.py`:

```python
# --- REST pagination/sorting test (append to tests/test_products_api.py) ---

import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_rest_pagination_and_sorting():
    async with AsyncClient(base_url=BASE, timeout=10.0) as ac:
        r = await ac.get(
            "/products",
            params={"limit": 5, "skip": 0, "sort_by": "price", "order": "desc"}
        )
    assert r.status_code == 200, r.text
    arr = r.json()
    assert isinstance(arr, list)
    assert len(arr) <= 5
    if len(arr) >= 2:
        # prices should be non-increasing (desc)
        assert float(arr[0]["price"]) >= float(arr[-1]["price"])
```

**What this does**

* Calls your live server (`127.0.0.1:8000`) with `limit=5` sorted by `price desc`.
* Asserts the array size and basic ordering property.

---

### 3) Add GraphQL pagination/sorting test

Create/append to `tests/test_graphql_api.py`:

```python
# --- GraphQL pagination/sorting test (append to tests/test_graphql_api.py) ---

import pytest
from httpx import AsyncClient

BASE = "http://127.0.0.1:8000"

async def gql(query: str):
    async with AsyncClient(base_url=BASE, timeout=15.0) as ac:
        return await ac.post("/graphql", json={"query": query})

@pytest.mark.asyncio
async def test_graphql_pagination_and_sorting():
    q = '{ allProducts(limit: 5, skip: 0, sortBy: "price", order: "desc") { name price } }'
    r = await gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("data") is not None, r.text
    data = payload["data"]["allProducts"]
    assert isinstance(data, list)
    assert len(data) <= 5
    if len(data) >= 2:
        assert float(data[0]["price"]) >= float(data[-1]["price"])
```

**What this does**

* Issues a GraphQL query with `limit/skip/sortBy/order`.
* Confirms a list is returned and verifies the sort order if possible.

---

### 4) Run tests + coverage in terminal

From a separate terminal (keep the server running via `./scripts/start.sh`):

```bash
pytest --cov=. --cov-report=term-missing
```

**You’ll see**:

* Overall coverage %
* **Term-missing**: which files/lines aren’t hit (great hints on what to test next)

If you prefer to store coverage data in a file:

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

This will also generate **HTML** at `htmlcov/index.html`.

---

### 5) Open the HTML coverage in Codespaces (two reliable options)

#### Option A (Most Reliable): **Serve `htmlcov/` and open via the Ports tab**

```bash
# from the repo root
python -m http.server 8001 -d htmlcov
```

* In the **Ports** tab of Codespaces:

  * Forward **8001** (if it doesn’t auto-forward).
  * Click the forwarded URL → it opens `htmlcov` listing.
  * Click `index.html` to view the coverage report in-browser.

> This option works consistently because Codespaces proxies the port and serves static files correctly.

#### Option B: **Open the HTML directly in the editor**

* In the Explorer, expand `htmlcov/` and open `index.html`.
* VS Code’s simple HTML preview works, but external assets might be blocked. If it looks odd, use **Option A**.

---

### 6) (Optional) Bake coverage defaults into `pytest.ini`

If you want to run coverage by default (optional), you can edit `pytest.ini`:

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts = -v --tb=short --cov=. --cov-report=term-missing
```

Then you can simply run:

```bash
pytest
```

And still add HTML when you need it:

```bash
pytest --cov-report=html
```

---

## 🧠 Deep Dive – Why this matters

* **Pagination** (`limit`, `skip`) keeps responses small and testable, and it’s how clients build infinite-scroll UIs or admin tables.
* **Sorting** (`sort_by`/`order`) produces deterministic results — crucial for **assertions** in tests.
* **Filters + Pagination** together let you form real-world queries (e.g., “find the cheapest 10 keyboards”).
* **Coverage** isn’t just a number — the **term-missing** output points to untested branches (e.g., invalid ID paths, empty results, error handling). Use it to focus your next tests.

---

## ✅ Summary (what you accomplished & learned)

* Confirmed your Day-11 REST and GraphQL already support **pagination** and **sorting**, and added **tests** for both, against the **real Uvicorn server**.
* Produced **coverage** in the terminal and learned a **reliable Codespaces flow** to view the **HTML coverage** (serving `htmlcov/` on a forwarded port).
* You now have the building blocks to iterate toward higher coverage by writing focused tests for any missing lines/branches reported by `term-missing`.


```
```

Run:
```bash
./scripts/start.sh
```
