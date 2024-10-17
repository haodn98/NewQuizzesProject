from fastapi import HTTPException, status
from redis.asyncio.client import Redis
from sqlalchemy import select

from src.companies.models import CompanyRole, CompanyMember


async def get_company_role(db, role_name: str, redis: Redis):
    """get type of invitation from Redis cache"""
    cached_role = await redis.get(role_name)
    if cached_role:
        return int(cached_role)

    result = await db.execute(select(CompanyRole).where(CompanyRole.name == role_name))
    company_role = result.scalar_one_or_none()

    if company_role is None:
        raise HTTPException(
            detail='Wrong company_role, should be "admin", "owner", or "admin"',
            status_code=status.HTTP_404_NOT_FOUND
        )

    await redis.set(role_name, company_role.id, ex=3600)

    return company_role.id


async def is_company_member(company_id: int, user_id, db, redis: Redis):
    cache_key = f"company_member_{company_id}_{user_id}"
    cached_result = await redis.get(cache_key)

    if cached_result:
        return cached_result == "true"

    query = (
        select(CompanyMember)
        .where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id
        )
    )
    result = await db.execute(query)
    company_member = result.scalar_one_or_none()

    if company_member is None:
        return False

    return True
