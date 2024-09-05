from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.traversals import compare

from src.auth.models import User
from src.companies.models import Company, CompanyMember, Invitation, Application, CompanyRole
from src.database import get_db_session
from src.utils.utils import get_current_user


async def is_company_admin(company_id: int, user: dict = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db_session)):
    query = (
        select(CompanyMember)
        .join(CompanyRole, CompanyMember.role == CompanyRole.id)
        .where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.get("id"),
            CompanyRole.name.in_(["owner", "admin"])
        )
    )
    result = await db.execute(query)
    company_member = result.scalar_one_or_none()

    if company_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )

async def is_company_owner(company_id: int, user: dict = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db_session)):
    query = (
        select(CompanyMember)
        .join(CompanyRole, CompanyMember.role == CompanyRole.id)
        .where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.get("id"),
            CompanyRole.name.in_(["owner"])
        )
    )
    result = await db.execute(query)
    company_member = result.scalar_one_or_none()

    if company_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )

async def is_invitation_sender(invitation_id: int, user: dict = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id,
                                                       Invitation.sender_user_id == user.get("id"),
                                                       ))
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return invitation


async def is_invitation_receiver(invitation_id: int, user: dict = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id,
                                                       Invitation.receiver_user_id == user.get("id"),
                                                       ))
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return invitation


async def is_application_receiver(application_id: int, user: dict = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    await is_company_admin(application.company_id, user, db)

    return application

