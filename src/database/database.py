from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from core.config import settings

# postgres setup
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

async_session = sessionmaker(bind=engine,
                             class_=AsyncSession,
                             expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    async with async_session() as session:
        yield session


