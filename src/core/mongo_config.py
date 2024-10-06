from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings


async def get_mongo_database():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    try:
        db = client[settings.MONGO_DB]
        db_collection = db[settings.MONGO_COLLECTION]
        yield db_collection
    finally:
        client.close()