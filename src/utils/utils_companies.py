from fastapi import HTTPException, status
from sqlalchemy import select

from src.companies.models import CompanyRole, CompanyMember

COMPANY_ROLE_CACHE = {}


async def get_company_role(db, role_name: str):
    """get type of invitation from cache"""
    if role_name in COMPANY_ROLE_CACHE:
        return COMPANY_ROLE_CACHE[role_name]

    result = await db.execute(select(CompanyRole).where(CompanyRole.name == role_name))
    company_role = result.scalar_one_or_none()

    if company_role is None:
        raise HTTPException(
            detail='Wrong company_role, should be "admin","owner" or "admin"',
            status_code=status.HTTP_404_NOT_FOUND)

    COMPANY_ROLE_CACHE[role_name] = company_role.id
    return company_role.id


async def is_company_member(company_id: int, user_id, db):
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