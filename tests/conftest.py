import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, defer
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from watchfiles import awatch

from src.auth.models import User
from src.companies.models import CompanyRole, Company, CompanyMember
from src.core.config import settings
from src.core.mongo_config import get_mongo_database
from src.database.base import Base
from src.database.database import get_db_session
from src.main import app, lifespan
from src.quizzes.manager import QuizManager
from src.utils.utils_auth import bcrypt_context, get_current_user

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.TEST_DB_USER}:{settings.TEST_DB_PASS}@{settings.TEST_DB_HOST}:{settings.TEST_DB_PORT}/{settings.TEST_DB_NAME}"
test_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)

async_session_test = sessionmaker(bind=test_engine,
                                  class_=AsyncSession,
                                  expire_on_commit=False)

Base.metadata.bind = test_engine


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        yield session


async def override_get_current_user():
    return {"username": "TestUser1", "id": 1}


async def override_get_mongo_database():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    db_collection = db["test_quizzes"]
    yield db_collection
    client.close()


app.dependency_overrides[get_db_session] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_mongo_database] = override_get_mongo_database


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await db.drop_collection("test_quizzes")
    client.close()


@pytest.fixture
async def ac() -> AsyncGenerator[AsyncSession, None]:
    async with lifespan(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


@pytest.fixture(scope="session")
async def test_user():
    user = User(
        email="Test@testt.com",
        username="TestUser1",
        hashed_password=bcrypt_context.hash("testpassword"),
        is_verified=True,

    )
    async with async_session_test() as db:
        db.add(user)
        await db.commit()
    yield user
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "user";'))
        await connection.commit()


@pytest.fixture(scope="session")
async def test_company_roles():
    roles = [
        CompanyRole(id=1, name="owner"),
        CompanyRole(id=2, name="admin"),
        CompanyRole(id=3, name="member")
    ]
    async with async_session_test() as db:
        db.add_all(roles)
        await db.commit()
    yield roles
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "company_role";'))
        await connection.commit()


@pytest.fixture(scope="session")
async def test_company_without_member():
    company = Company(
        name="test company no members",
        description="test company descriptions",
    )
    async with async_session_test() as db:
        db.add(company)
        await db.commit()
    yield company
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "company";'))
        await connection.commit()


@pytest.fixture(scope="session")
async def test_company_with_member(test_user, test_company_roles):
    company = Company(
        name="test company with members",
        description="test company descriptions",
    )
    async with async_session_test() as db:
        db.add(company)
        await db.commit()
        await db.refresh(company)
        company_member = CompanyMember(
            user_id=test_user.id,
            company_id=company.id,
            role=next(role.id for role in test_company_roles if role.name == "owner")
        )
        db.add(company_member)
        await db.commit()
    yield company
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "company_member";'))
        await connection.execute(text('DELETE FROM "company";'))
        await connection.commit()


