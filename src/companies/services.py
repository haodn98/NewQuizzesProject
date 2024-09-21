from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette import status

from src.auth.models import User
from src.companies.models import (Company,
                                  CompanyMember,
                                  Invitation,
                                  CompanyRole,
                                  InvitationStatusEnum,
                                  Application)
from src.utils.utils_companies import get_company_role, is_company_member


async def get_company_by_id_service(company_id, db):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return company


async def create_company_service(user, company_data, db):
    result = await db.execute(select(Company).where(Company.name == company_data.name))
    repeatable_company = result.scalar_one_or_none()
    if repeatable_company:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    company = Company(
        name=company_data.name,
        description=company_data.description,
        is_private=False
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    await create_company_member_service(user.get("id"), company.id, "owner", db)
    return company


async def create_company_member_service(user_id, company_id, role, db):
    if not await is_company_member(user_id, company_id, db):
        company_member = CompanyMember(
            user_id=user_id,
            company_id=company_id,
            role=await get_company_role(db, role)
        )
        db.add(company_member)
        await db.commit()
    else:
        raise HTTPException(detail="User is already member of a company",
                            status_code=status.HTTP_400_BAD_REQUEST)


async def delete_company_member_service(user_id, company_id, db):
    try:
        result = await db.execute(select(CompanyMember).where(CompanyMember.user_id == user_id,
                                                              CompanyMember.company_id == company_id))
        company_member_to_delete = result.scalar_one_or_none()
        if not company_member_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        await db.delete(company_member_to_delete)
        await db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def update_company_service(company_id, company_data, db):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(detail="company not found",
                            status_code=status.HTTP_404_NOT_FOUND)

    for key, value in company_data.dict(exclude_unset=True).items():
        if key == "name":
            if value == company_data.name:
                continue
        setattr(company, key, value)
    db.add(company)
    await db.commit()
    return company


async def change_company_access_service(company_id, db):
    try:
        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        company.is_private = not company.is_private
        db.add(company)
        await db.commit()
        return company
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def delete_company_service(company_id, db):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await db.delete(company)
    await db.commit()


async def get_company_members_service(company_id, db):
    result = await db.execute(select(CompanyMember).where(CompanyMember.company_id == company_id))
    members = result.scalars().all()
    if not members:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return members


async def create_invitational_letter(user, invitational_letter, db):
    if user.get("id") == invitational_letter.receiver_user_id:
        raise HTTPException(
            detail="Cannot send invitation to yourself",
            status_code=status.HTTP_400_BAD_REQUEST)
    invitation = Invitation(
        sender_user_id=user.get("id"),
        receiver_user_id=invitational_letter.receiver_user_id,
        company_id=invitational_letter.company_id,
        status=InvitationStatusEnum.INPROCESS.value
    )
    db.add(invitation)
    await db.commit()
    return invitation


async def get_users_invitations_service(user_id, db):
    result = await db.execute(select(Invitation).where(Invitation.receiver_user_id == user_id))
    invitations = result.scalars().all()
    if not invitations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return invitations


async def get_users_applications_service(user, db):
    result = await db.execute(select(Application).where(Application.sender_user_id == user.get("id")))
    applications = result.scalars().all()
    if not applications:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return applications


async def get_users_companies_service(user_id, db):
    result = await db.execute(
        select(Company.name, Company.id).join(CompanyMember, Company.id == CompanyMember.company_id).where(
            CompanyMember.user_id == user_id))
    companies = result.all()
    return [{"id": company.id, "name": company.name} for company in companies]


async def get_company_applications_service(company_id, db):
    result = await db.execute(select(Application).where(Application.company_id == company_id))
    applications = result.scalars().all()
    if not applications:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return applications


async def get_company_invitations_service(company_id, db):
    result = await db.execute(select(Invitation).where(Invitation.company_id == company_id))
    invitations = result.scalars().all()
    if not invitations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return invitations


async def delete_invitational_letter_service(invitational_id, db):
    invitation = await db.execute(select(Invitation).where(Invitation.id == invitational_id))
    invitation = invitation.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(invitation)
    await db.commit()


async def invitational_answer_letter_service(invitational_id, invitation_answer, db):
    invitation = await db.execute(select(Invitation).where(Invitation.id == invitational_id,
                                                           Invitation.is_active == True))
    invitation = invitation.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if invitation_answer.answer == "rejected":
        invitation.status = InvitationStatusEnum.REJECTED.value
        invitation.is_private = False
        db.add(invitation)
        await db.commit()
        return JSONResponse(content={"detail": "Invitation was rejected."},
                            status_code=status.HTTP_200_OK,
                            )
    invitation.status = InvitationStatusEnum.ACCEPTED.value
    invitation.is_active = False
    db.add(invitation)
    await db.commit()
    await create_company_member_service(invitation.receiver_user_id, invitation.company_id, "member", db)
    return invitation


async def application_answer_letter_service(application_id, application_letter, db):
    application = await db.execute(
        select(Application).where(Application.id == application_id,
                                  Application.is_active == True))
    application = application.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if application_letter.answer == "rejected":
        application.status = InvitationStatusEnum.REJECTED.value
        application.is_active = False
        db.add(application)
        await db.commit()
        return JSONResponse(content={"detail": "Invitation was rejected."},
                            status_code=status.HTTP_200_OK,
                            )
    application.status = InvitationStatusEnum.ACCEPTED.value
    application.is_active = False
    db.add(application)
    await db.commit()
    await create_company_member_service(application.sender_user_id, application.company_id, "member", db)
    return application


async def create_application_letter(user, application_letter, db):
    application = Application(
        sender_user_id=user.get("id"),
        company_id=application_letter.company_id,
        status=InvitationStatusEnum.INPROCESS.value
    )
    db.add(application)
    await db.commit()
    return application


async def create_company_admin_user_service(company_id, admin_user_request, db):
    admin_user = await db.execute(select(CompanyMember).where(CompanyMember.company_id == company_id,
                                                              CompanyMember.user_id == admin_user_request.user_id))
    admin_user = admin_user.scalar_one_or_none()
    if not admin_user:
        raise HTTPException(detail="User is not a company member",
                            status_code=status.HTTP_404_NOT_FOUND)

    admin_user.role = await get_company_role(db, "admin")
    db.add(admin_user)
    await db.commit()
    return admin_user


async def get_company_admin_user_service(company_id, db):
    result = await db.execute(
        select(User.id, User.username)
        .join(CompanyMember, User.id == CompanyMember.user_id)
        .join(CompanyRole, CompanyMember.role == CompanyRole.id)
        .where(CompanyMember.company_id == company_id,
               CompanyRole.name.in_(["owner", "admin"])
               ))
    admin_users = result.all()
    if not admin_users:
        raise HTTPException(detail="There is no admins",
                            status_code=status.HTTP_404_NOT_FOUND)
    return [{"user_id": user.id, "username": user.username} for user in admin_users]


async def delete_company_admin_user_service(company_id, admin_user_request, db):
    not_admin_user = await db.execute(select(CompanyMember).where(CompanyMember.company_id == company_id,
                                                                  CompanyMember.user_id == admin_user_request.user_id))
    not_admin_user = not_admin_user.scalar_one_or_none()
    if not not_admin_user:
        raise HTTPException(detail="User is not a company member",
                            status_code=status.HTTP_404_NOT_FOUND)

    not_admin_user.role = await get_company_role(db, "member")
    db.add(not_admin_user)
    await db.commit()
    return not_admin_user


async def get_company_roles_service(db):
    company_roles = await db.execute(select(CompanyRole))
    return company_roles.scalars().all()
