from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import settings


async def get_mongo_database():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    db_collection = db[settings.MONGO_COLLECTION]
    return db_collection