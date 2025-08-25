# Day 9

Perfect 👌 let’s move on with **Day 9** of the Python Testing Bootcamp.
We’ll continue building on top of **FastAPI + MongoDB + GraphQL**.

Here’s your **detailed README content for Day 9**:

---

````markdown
# Day 9 – Updating and Deleting Data with GraphQL

Welcome to **Day 9** of the Python Testing Bootcamp.

So far, we:
- Built a **REST + GraphQL API** using FastAPI.
- Added MongoDB persistence.
- Wrote tests for **queries** and **add mutations** in GraphQL.

Today, we’ll complete the CRUD cycle by adding:
- **Update mutations**  
- **Delete mutations**

This makes our GraphQL API production-ready.

---

## 🎯 Goals

- Learn how to implement **GraphQL mutations** for update and delete.
- Add **MongoDB integration** for modifying data.
- Expand our **tests** to cover update/delete functionality.
- Understand error handling in GraphQL.

---

## 📖 Theory – Mutations in GraphQL

In GraphQL:
- **Queries** = read-only operations (fetch data).  
- **Mutations** = write operations (create, update, delete).  

A mutation looks like a function call and returns the updated data.

Example:

```graphql
mutation {
  updateProduct(id: "123", name: "Laptop Pro", price: 1999.99) {
    id
    name
    price
  }
}
````

This updates a product and returns the new state.

---

## 🛠 Step-by-Step Instructions

### 1) Extend GraphQL Schema

Update `src/graphql_schema.py`:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, name: str, price: float) -> Product:
        doc = {"name": name, "price": price}
        result = await db.products.insert_one(doc)
        return Product(id=str(result.inserted_id), name=name, price=price)

    @strawberry.mutation
    async def update_product(self, id: strawberry.ID, name: Optional[str] = None, price: Optional[float] = None) -> Optional[Product]:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if price is not None:
            update_data["price"] = price

        if not update_data:
            return None

        result = await db.products.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": update_data},
            return_document=True,
        )

        if result:
            return Product(id=str(result["_id"]), name=result["name"], price=result["price"])
        return None

    @strawberry.mutation
    async def delete_product(self, id: strawberry.ID) -> bool:
        result = await db.products.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
```

---

### 2) Write Tests

Update `tests/test_graphql_api.py`:

```python
@pytest.mark.asyncio
async def test_graphql_update_and_delete_product(test_client):
    # Create product
    add_query = """
    mutation {
      addProduct(name: "Chair", price: 49.99) {
        id
        name
        price
      }
    }
    """
    r = await test_client.post("/graphql", json={"query": add_query})
    product = r.json()["data"]["addProduct"]
    product_id = product["id"]

    # Update product
    update_query = f"""
    mutation {{
      updateProduct(id: "{product_id}", name: "Office Chair", price: 89.99) {{
        id
        name
        price
      }}
    }}
    """
    r = await test_client.post("/graphql", json={"query": update_query})
    updated = r.json()["data"]["updateProduct"]
    assert updated["name"] == "Office Chair"
    assert updated["price"] == 89.99

    # Delete product
    delete_query = f"""
    mutation {{
      deleteProduct(id: "{product_id}")
    }}
    """
    r = await test_client.post("/graphql", json={"query": delete_query})
    deleted = r.json()["data"]["deleteProduct"]
    assert deleted is True
```

---

### 3) Run Tests

```bash
pytest -v
```

Expected output:

```
tests/test_graphql_api.py::test_graphql_update_and_delete_product PASSED
```

---

## ✅ Summary

Today you:

* Implemented **update** and **delete** mutations in GraphQL.
* Integrated them with **MongoDB** using `find_one_and_update` and `delete_one`.
* Wrote tests that:

  * Create → Update → Delete a product.
* Completed full **CRUD coverage in GraphQL**.

Next up (**Day 10**): We’ll dive into **filtering and advanced queries** with GraphQL.

```

---

```

Run:
```bash
./scripts/start.sh
```
