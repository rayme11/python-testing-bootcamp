# src/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List

app = FastAPI()

# --- Mongo connection ---
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.testing_db
products_collection = db.products

# --- REST root ---
@app.get("/")
def root():
    return {"message": "API is running"}

# --- REST: /products ---
class Product(BaseModel):
    name: str
    price: float

@app.post("/products")
async def create_product(product: Product):
    new_product = product.model_dump()
    result = await products_collection.insert_one(new_product)
    return {"message": "Product added", "id": str(result.inserted_id)}

@app.get("/products")
async def list_products():
    items = []
    async for doc in products_collection.find():
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items

# --- GraphQL types/resolvers ---
@strawberry.type
class ProductType:
    name: str
    price: float

@strawberry.input
class ProductInput:
    name: str
    price: float

@strawberry.type
class Query:
    @strawberry.field
    async def all_products(self) -> List[ProductType]:
        results = []
        async for doc in products_collection.find():
            results.append(ProductType(name=doc["name"], price=doc["price"]))
        return results

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductInput) -> str:
        await products_collection.insert_one({"name": product.name, "price": product.price})
        return f"Product '{product.name}' added."

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
