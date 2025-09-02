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
