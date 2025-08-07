import asyncio
import motor.motor_asyncio

async def seed():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    products = db.products

    await products.insert_many([
        {"name": "Laptop", "price": 999.99},
        {"name": "Mouse", "price": 29.99},
        {"name": "Monitor", "price": 199.99}
    ])
    print("✅ Seeded test data!")

if __name__ == "__main__":
    asyncio.run(seed())
