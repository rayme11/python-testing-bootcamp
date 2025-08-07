from fastapi import FastAPI
from pydantic import BaseModel
import motor.motor_asyncio


app = FastAPI()

# MongoDB client (localhost for Docker)
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.testing_db
products_collection = db.products

@app.get("/")
def root():
    return {"message": "API is running"}

class Product(BaseModel):
    name: str
    price: float

@app.post("/products")
async def create_product(product: Product):
    new_product = product.dict()
    result = await products_collection.insert_one(new_product)
    return {
        "message": "Product added",
        "id": str(result.inserted_id)
    }

@app.get("/products")
async def list_products():
    products = []
    async for product in products_collection.find():
        product["_id"] = str(product["_id"])  # Convert ObjectId to str
        products.append(product)
    return products

