# tests/conftest.py
import pytest
import motor.motor_asyncio

@pytest.fixture
def sample_user():
    return {"id": 1, "username": "tester", "role": "admin"}

# Optional: Day 9 autouse seeding/cleanup
@pytest.fixture(autouse=True)
async def seed_and_cleanup():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.testing_db
    await db.products.delete_many({})
    await db.products.insert_many([
        {"name": "Preloaded Item 1", "price": 10.99},
        {"name": "Preloaded Item 2", "price": 20.50}
    ])
    yield
    await db.products.delete_many({})
