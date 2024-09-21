from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_pagination import add_pagination

from src.auth.router import router as auth_router
from src.companies.router import router as companies_router
from src.core.config import settings
from src.core.redis_config import init_redis_pool, close_redis_pool
from src.quizzes.router import router as quizzes_router
from src.notifications.routers import router as notifications_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_redis_pool()
    redis = aioredis.from_url(settings.REDIS_URL)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield
    await close_redis_pool()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(quizzes_router)

app.include_router(notifications_router)

add_pagination(app)


@app.get("/healthy")
async def health_check():
    return {
        "status_code": 200,
        "detail": "ok",
        "result": "working"
    }
