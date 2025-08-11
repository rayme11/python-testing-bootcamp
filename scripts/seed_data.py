from faker import Faker
import motor.motor_asyncio
import asyncio

fake = Faker()

async def seed_products():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    products_collection = db.products
    await products_collection.delete_many({})
    products = [{"name": fake.word().title(), "price": round(fake.random_number(digits=3), 2)} for _ in range(100)]
    await products_collection.insert_many(products)
    print(f"✅ Seeded {len(products)} products.")

if __name__ == "__main__":
    asyncio.run(seed_products())
