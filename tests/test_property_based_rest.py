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
