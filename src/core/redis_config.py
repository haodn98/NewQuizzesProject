import aioredis

from src.core.config import Settings

REDIS_URL = Settings.REDIS_URL
# redis setup
redis: aioredis.Redis = None


async def get_redis() -> aioredis.Redis:
    return redis


async def init_redis_pool():
    global redis
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)


async def close_redis_pool():
    await redis.close()
