from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Health check root route
@app.get("/")
def root():
    return {"message": "API is running"}

# Data model
class Item(BaseModel):
    name: str
    price: float

# Create item endpoint
@app.post("/items")
async def create_item(item: Item):
    return {
        "message": f"Item '{item.name}' added successfully.",
        "price": item.price
    }
