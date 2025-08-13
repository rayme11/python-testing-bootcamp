# src/main.py
from typing import List, Optional

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI()

# ---------------------------
# Lazy Mongo initialization
# ---------------------------
def ensure_mongo(request: Request):
    """
    Create and cache the Motor client/db/collection on demand.
    This avoids relying on ASGI lifespan in tests and prevents
    'event loop is closed' from a client created on a different loop.
    """
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# ---------------------------
# REST models & routes
# ---------------------------
class Product(BaseModel):
    name: str
    price: float

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/products")
async def create_product(product: Product, request: Request):
    col = ensure_mongo(request)
    result = await col.insert_one(product.model_dump())
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.get("/products")
async def list_products(request: Request):
    col = ensure_mongo(request)
    items: list[dict] = []
    async for doc in col.find():
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items

@app.get("/products/first-id")
async def first_product_id(request: Request):
    col = ensure_mongo(request)
    doc = await col.find_one({})
    if not doc:
        raise HTTPException(status_code=404, detail="No products")
    return {"id": str(doc["_id"]), "name": doc["name"], "price": doc["price"]}

# ---------------------------
# GraphQL types & context
# ---------------------------
@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

async def get_context(request: Request):
    # Provide FastAPI request so resolvers can call ensure_mongo(...)
    return {"request": request}

# ---------------------------
# GraphQL schema (query + mutations)
# ---------------------------
@strawberry.type
class Query:
    @strawberry.field
    async def all_products(
        self,
        info,
        name_contains: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[ProductType]:
        """
        Strawberry exposes these as camelCase in GraphQL:
          nameContains, minPrice, maxPrice
        """
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        query: dict = {}
        if name_contains:
            query["name"] = {"$regex": name_contains, "$options": "i"}
        if min_price is not None or max_price is not None:
            price = {}
            if min_price is not None:
                price["$gte"] = float(min_price)
            if max_price is not None:
                price["$lte"] = float(max_price)
            query["price"] = price

        results: list[ProductType] = []
        async for doc in col.find(query):
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> str:
        request: Request = info.context["request"]
        col = ensure_mongo(request)
        await col.insert_one({"name": product.name, "price": float(product.price)})
        return f"Product '{product.name}' added."

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> str:
        request: Request = info.context["request"]
        col = ensure_mongo(request)
        try:
            oid = ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await col.update_one(
            {"_id": oid},
            {"$set": {"name": product.name, "price": float(product.price)}},
        )
        if result.matched_count == 0:
            return "Product not found."
        return "Product updated."

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> str:
        request: Request = info.context["request"]
        col = ensure_mongo(request)
        try:
            oid = ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return "Product not found."
        return "Product deleted."

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
