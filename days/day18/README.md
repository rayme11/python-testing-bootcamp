# Day 18

Here’s **Day 18** in the same format—focused on **property-based testing (Hypothesis)** and **input validation** for our existing FastAPI + Mongo + Strawberry app. It includes exactly what to change, new files to add, and how to run + view coverage in Codespaces.

---

````markdown
# Day 18 – Property-Based Testing (Hypothesis) + Stronger Validation

## 🎯 Goals
- Add **robust input validation** to `Product` using Pydantic (min/max, > 0, etc.).
- Introduce **property-based testing** with **Hypothesis** to automatically explore many inputs.
- Keep using our **real Uvicorn server** + Mongo + GraphQL context from previous days.
- See test **coverage** in terminal and in **browser** (Codespaces).

---

## 🛠 Step-by-step instructions

### 1) Update dependencies (add Hypothesis)

**Append to `requirements.txt`:**
```txt
hypothesis
````

> If your Codespace is already running, re-install deps:

```bash
pip install -r requirements.txt
```

---

### 2) Strengthen input validation in `src/main.py`

We’ll **tighten** the `Product` schema so tests can exercise both valid and invalid payloads.

**Change this in `src/main.py`:**

```python
# BEFORE
# class Product(BaseModel):
#     name: str
#     price: float

# AFTER
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0, lt=100000)
```

> Why:
>
> * `name` must be non-empty and reasonably short.
> * `price` must be positive and below a large upper bound.
>   These constraints keep our API realistic and create meaningful negative cases for Hypothesis.

No other changes are needed—your existing REST and GraphQL code will keep working with these constraints.

---

### 3) Add property-based tests

We’ll add **two** test modules:

* REST property tests (`tests/test_property_based_rest.py`)
* GraphQL property tests (`tests/test_property_based_graphql.py`)

They **do not** use `asyncio`; we call the real server with `requests` so Hypothesis can manage many example runs easily.

> Make sure your server is running first:
>
> ```bash
> ./scripts/start.sh
> ```

#### A) `tests/test_property_based_rest.py`

```python
import requests
from hypothesis import given, settings, strategies as st

BASE = "http://127.0.0.1:8000"

# Strategy for valid product names (1..80 chars, letters/spaces/hyphens)
valid_names = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd",),
        whitelist_characters=" -_",
        min_codepoint=32, max_codepoint=126
    ),
    min_size=1, max_size=80
).map(lambda s: s.strip() or "X")  # ensure not empty after strip

# Valid positive prices (float-ish)
valid_prices = st.decimals(min_value="0.01", max_value="99999.99", allow_nan=False, allow_infinity=False)\
                 .map(lambda d: float(d))

# Some invalids
invalid_prices = st.one_of(
    st.just(0.0),
    st.decimals(max_value="-0.01", allow_nan=False, allow_infinity=False).map(lambda d: float(d))
)

@given(name=valid_names, price=valid_prices)
@settings(max_examples=30)
def test_create_product_accepts_valid_payloads(name, price):
    r = requests.post(f"{BASE}/products", json={"name": name, "price": price}, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("message") == "Product added"
    assert "id" in body

@given(name=st.just(""), price=valid_prices)
@settings(max_examples=10)
def test_create_product_rejects_empty_name(name, price):
    r = requests.post(f"{BASE}/products", json={"name": name, "price": price}, timeout=10)
    # FastAPI/Pydantic validation errors return HTTP 422
    assert r.status_code == 422, r.text

@given(name=valid_names, price=invalid_prices)
@settings(max_examples=10)
def test_create_product_rejects_non_positive_price(name, price):
    r = requests.post(f"{BASE}/products", json={"name": name, "price": price}, timeout=10)
    assert r.status_code == 422, r.text

# Pagination/sorting fuzz (kept small to stay fast)
@given(
    limit=st.integers(min_value=1, max_value=25),
    skip=st.integers(min_value=0, max_value=25),
    sort_by=st.sampled_from(["name", "price"]),
    order=st.sampled_from(["asc", "desc"])
)
@settings(max_examples=20)
def test_list_products_pagination_sorting(limit, skip, sort_by, order):
    r = requests.get(
        f"{BASE}/products",
        params={"limit": limit, "skip": skip, "sort_by": sort_by, "order": order},
        timeout=10
    )
    assert r.status_code == 200, r.text
    arr = r.json()
    assert isinstance(arr, list)
    assert len(arr) <= limit
    if len(arr) >= 2 and sort_by == "price":
        if order == "asc":
            assert arr[0]["price"] <= arr[-1]["price"]
        else:
            assert arr[0]["price"] >= arr[-1]["price"]
```

#### B) `tests/test_property_based_graphql.py`

```python
import requests
from hypothesis import given, settings, strategies as st

BASE = "http://127.0.0.1:8000"

valid_names = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd",),
        whitelist_characters=" -_",
        min_codepoint=32, max_codepoint=126
    ),
    min_size=1, max_size=80
).map(lambda s: s.strip() or "X")

valid_prices = st.decimals(min_value="0.01", max_value="99999.99", allow_nan=False, allow_infinity=False)\
                 .map(lambda d: float(d))

def gql(query: str, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(f"{BASE}/graphql", json={"query": query}, headers=headers, timeout=15)

def login(username: str, password: str) -> str:
    r = requests.post(f"{BASE}/token", data={"username": username, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

# We only fuzz queries (no mutations) here to avoid admin token mgmt in Hypothesis loops.
@given(
    name_contains=st.one_of(st.none(), st.text(min_size=0, max_size=5)),
    min_price=st.one_of(st.none(), st.floats(min_value=0.01, max_value=5000, allow_infinity=False, allow_nan=False)),
    max_price=st.one_of(st.none(), st.floats(min_value=0.01, max_value=5000, allow_infinity=False, allow_nan=False)),
    limit=st.integers(min_value=1, max_value=10),
    skip=st.integers(min_value=0, max_value=10),
    sort_by=st.sampled_from(["name", "price"]),
    order=st.sampled_from(["asc", "desc"]),
)
@settings(max_examples=20)
def test_graphql_all_products_fuzz(name_contains, min_price, max_price, limit, skip, sort_by, order):
    # ensure min<=max when both provided
    if min_price is not None and max_price is not None and min_price > max_price:
        min_price, max_price = max_price, min_price

    parts = []
    if name_contains is not None:
        parts.append(f'nameContains: "{name_contains}"')
    if min_price is not None:
        parts.append(f"minPrice: {float(min_price):.2f}")
    if max_price is not None:
        parts.append(f"maxPrice: {float(max_price):.2f}")
    parts.append(f"limit: {limit}")
    parts.append(f"skip: {skip}")
    parts.append(f'sortBy: "{sort_by}"')
    parts.append(f'order: "{order}"')
    args = ", ".join(parts)

    q = f'{{ allProducts({args}) {{ name price }} }}'
    r = gql(q)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert "errors" not in payload, payload
    data = payload.get("data", {}).get("allProducts", [])
    assert isinstance(data, list)
    assert len(data) <= limit
    # Optional order check when price sort requested
    if len(data) >= 2 and sort_by == "price":
        if order == "asc":
            assert data[0]["price"] <= data[-1]["price"]
        else:
            assert data[0]["price"] >= data[-1]["price"]
```

---

### 4) Run the server and the tests

**Terminal A – start services (Mongo + API + seed)**

```bash
./scripts/start.sh
```

**Terminal B – run tests (including Hypothesis)**

```bash
pytest -q
```

> Hypothesis will generate many examples per test—if you want **more** exploration:

```bash
pytest -q -k property_based --hypothesis-show-statistics
```

---

### 5) Coverage (terminal + browser in Codespaces)

**Terminal coverage (concise + missing lines)**

```bash
pytest --cov=. --cov-report=term-missing
```

**HTML coverage (serve via Codespaces)**

```bash
pytest --cov=. --cov-report=html
python3 -m http.server 9000 --directory htmlcov
```

* In Codespaces, open the **Ports** tab, make sure **9000** is forwarded & public, then open:

  ```
  https://<your-forwarded-url>-9000.github.dev/index.html
  ```

---

## ✅ Summary (what you accomplished & learned)

* You **hardened** your API with Pydantic constraints (min length, positive price).
* You used **Hypothesis** to automatically test **dozens of inputs** per test:

  * Valid random payloads are accepted (status **200**).
  * Invalid payloads (empty name, non-positive price) are rejected (status **422**).
  * Pagination/sorting combos hold under fuzzing for both REST and GraphQL.
* You kept the stack **unchanged** (FastAPI + Mongo + Strawberry + RBAC), so the tests still hit a **real running server**, making the results closer to production behavior.
* You reviewed coverage both in the **terminal** and with a **browser** via Codespaces.

> Tip: Property-based tests are fantastic for **finding edge cases you didn’t think about**. If Hypothesis finds a failure, it will **shrink** the input to a minimal counterexample—use that to tighten validation or improve logic.

```
---
::contentReference[oaicite:0]{index=0}
```

Run:
```bash
./scripts/start.sh
```
