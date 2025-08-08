from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List
import motor.motor_asyncio

# MongoDB setup
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.testing_db
products_collection = db.products

# Product type for output
@strawberry.type
class ProductType:
    name: str
    price: float

# Product input for mutations
@strawberry.input
class ProductInput:
    name: str
    price: float

# Query resolver
@strawberry.type
class Query:
    @strawberry.field
    async def all_products(self) -> List[ProductType]:
        products = []
        async for p in products_collection.find():
            products.append(ProductType(name=p["name"], price=p["price"]))
        return products

# Mutation resolver
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_product(self, product: ProductInput) -> str:
        await products_collection.insert_one({"name": product.name, "price": product.price})
        return f"Product '{product.name}' added."

# Strawberry schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

# FastAPI app
app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def read_root():
    return {"message": "API is running"}
