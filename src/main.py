# src/main.py
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Request, Query
from pydantic import BaseModel
import motor.motor_asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter

app = FastAPI()

# ---------- Lazy Mongo initialization ----------
def ensure_mongo(request: Request):
    state = request.app.state
    if not hasattr(state, "client"):
        state.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    if not hasattr(state, "db"):
        state.db = state.client.testing_db
    if not hasattr(state, "products"):
        state.products = state.db.products
    return state.products

# ---------- REST: models & routes ----------
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
async def list_products(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("name", pattern="^(name|price)$"),
    order: str = Query("asc", pattern="^(?i)(asc|desc)$"),
):
    col = ensure_mongo(request)
    sort_dir = 1 if order.lower() == "asc" else -1
    items: list[dict] = []
    cursor = col.find().skip(skip).limit(limit).sort(sort_by, sort_dir)
    async for doc in cursor:
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

# ---------- GraphQL: types, schema & router ----------
@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

async def get_context(request: Request):
    return {"request": request}

@strawberry.type
class QueryGQL:
    @strawberry.field
    async def all_products(
        self,
        info,
        name_contains: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: Optional[int] = 100,
        skip: Optional[int] = 0,
        sort_by: Optional[str] = "name",
        order: Optional[str] = "asc",
    ) -> List[ProductType]:
        request: Request = info.context["request"]
        col = ensure_mongo(request)

        # Build query
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

        # Validate & normalize paging/sorting
        limit = max(1, min(int(limit or 100), 500))
        skip = max(0, int(skip or 0))
        sort_by = sort_by if sort_by in {"name", "price"} else "name"
        sort_dir = 1 if (order or "asc").lower() == "asc" else -1

        results: list[ProductType] = []
        cursor = col.find(query).skip(skip).limit(limit).sort(sort_by, sort_dir)
        async for doc in cursor:
            results.append(ProductType(name=doc["name"], price=float(doc["price"])))
        return results

@strawberry.type
class MutationGQL:
    @strawberry.mutation
    async def add_product(self, info, product: ProductInput) -> str:
        col = ensure_mongo(info.context["request"])
        await col.insert_one({"name": product.name, "price": float(product.price)})
        return f"Product '{product.name}' added."

    @strawberry.mutation
    async def update_product(self, info, id: str, product: ProductInput) -> str:
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await col.update_one({"_id": oid}, {"$set": {"name": product.name, "price": float(product.price)}})
        if result.matched_count == 0:
            return "Product not found."
        return "Product updated."

    @strawberry.mutation
    async def delete_product(self, info, id: str) -> str:
        col = ensure_mongo(info.context["request"])
        try:
            oid = ObjectId(id)
        except Exception:
            return "Invalid product ID."
        result = await col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return "Product not found."
        return "Product deleted."

schema = strawberry.Schema(query=QueryGQL, mutation=MutationGQL)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
