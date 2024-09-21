import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.companies.models import CompanyRole,Base
from src.database.database import SQLALCHEMY_DATABASE_URL

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)



async def seed_roles(session: AsyncSession):
    roles = [
        CompanyRole(id=1, name="owner"),
        CompanyRole(id=2, name="admin"),
        CompanyRole(id=3, name="member")
    ]
    session.add_all(roles)
    await session.commit()


async def seed_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_roles(session)


if __name__ == '__main__':
    asyncio.run(seed_all())
