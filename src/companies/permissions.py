from dns.e164 import query
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.companies.models import (CompanyMember, Invitation, Application, CompanyRole, Company)
from src.database.database import get_db_session
from src.utils.utils_auth import get_current_user


async def check_company_membership(company_id: int, user: dict, role_names: list, db: AsyncSession):
    company = await db.execute(select(Company).where(Company.id == company_id))
    company = company.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company does not exist"
        )

    query = (
        select(CompanyMember)
        .join(CompanyRole, CompanyMember.role == CompanyRole.id)
        .where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.get("id"),
            CompanyRole.name.in_(role_names)
        )
    )

    result = await db.execute(query)
    company_member = result.scalar_one_or_none()

    if company_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )

    return True


async def is_company_member(company_id: int, user: dict = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db_session)):
    return await check_company_membership(company_id, user, ["owner", "admin", "member"], db)

async def is_company_owner(company_id: int, user: dict = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db_session)):
    return await check_company_membership(company_id, user, ["owner"], db)


async def is_company_admin(company_id: int, user: dict = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db_session)):
    return await check_company_membership(company_id, user, ["owner", "admin"], db)

async def is_invitation_sender(invitation_id: int, user: dict = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()

    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation does not exist"
        )
    if invitation.sender_user_id != user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )
    return True


async def is_invitation_receiver(invitation_id: int, user: dict = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation does not exist"
        )
    if invitation.receiver_user_id != user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )
    return True


async def is_application_receiver(application_id: int, user: dict = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    await is_company_admin(application.company_id, user, db)

    return True
