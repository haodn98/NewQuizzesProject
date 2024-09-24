from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.links import Page
from sqlalchemy import select, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.companies.models import Invitation, Company, Application
from src.companies.permissions import (is_company_admin,
                                       is_invitation_sender,
                                       is_invitation_receiver,
                                       is_application_receiver,
                                       is_company_owner)
from src.companies.schemas import (CompanyCreateUpdateSchema,
                                   CompanyRead,
                                   InviteLetterSchema,
                                   ApplicationLetterSchema,
                                   InviteApplicationAnswerSchema,
                                   CompanyMemberDeleteSchema,
                                   CreateDeleteCompanyAdminSchema)
from src.companies.services import (create_company_service,
                                    update_company_service,
                                    delete_company_service,
                                    get_company_by_id_service,
                                    change_company_access_service,
                                    get_company_members_service,
                                    create_invitational_letter,
                                    get_users_invitations_service,
                                    get_company_roles_service,
                                    invitational_answer_letter_service,
                                    create_application_letter,
                                    get_company_applications_service,
                                    delete_invitational_letter_service,
                                    application_answer_letter_service,
                                    delete_company_member_service,
                                    get_users_companies_service,
                                    get_users_applications_service,
                                    get_company_invitations_service,
                                    create_company_admin_user_service,
                                    delete_company_admin_user_service,
                                    get_company_admin_user_service)
from src.database.database import get_db_session
from src.utils.utils_auth import get_current_user

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
)


@router.get("", response_model=Page[CompanyRead])
@cache(expire=30)
async def get_all_companies(db: AsyncSession = Depends(get_db_session)):
    """
       Retrieve a paginated list of all companies.

       :param db: The asynchronous database session.
       :return: A paginated list of companies, ordered by their registration date.
       """
    return await paginate(db, select(Company).where(Company.is_private == False).order_by(Company.registration_date))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_company(company: CompanyCreateUpdateSchema,
                         user: Annotated[dict, Depends(get_current_user)],
                         db: AsyncSession = Depends(get_db_session)):
    """
    Create a new company.

    :param company: The company creation schema containing details of the new company.
    :param user: The currently authenticated user.
    :param db: The asynchronous database session.
    :return: The created company details.
    """
    return await create_company_service(user=user, company_data=company, db=db)


@router.get("/details/{company_id}")
@cache(expire=30)
async def get_company_by_id(company_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    Retrieve details of a company by its ID.

    :param company_id: The ID of the company to retrieve.
    :param db: The asynchronous database session.
    :return: The details of the requested company.
    """
    return await get_company_by_id_service(company_id, db)


@router.get("/details/{company_id}/members")
@cache(expire=30)
async def get_company_members(company_id: int,
                              user: Annotated[dict, Depends(get_current_user)],
                              db: AsyncSession = Depends(get_db_session)):
    """
    Retrieve the list of members of a specific company by its ID.

    :param company_id: The ID of the company whose members are to be retrieved.
    :param db: The asynchronous database session.
    :return: A list of members in the specified company.
    """
    return await get_company_members_service(company_id, db)


@router.delete("/details/{company_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_members(company_id: int,
                                 company_member_user_id: CompanyMemberDeleteSchema,
                                 user: Annotated[dict, Depends(get_current_user)],
                                 company: bool = Depends(is_company_admin),
                                 db: AsyncSession = Depends(get_db_session)):
    return await delete_company_member_service(company_id=company_id, user_id=company_member_user_id.user_id, db=db)


@router.put("/details/{company_id}")
async def update_company(company_id: int,
                         company_data: CompanyCreateUpdateSchema,
                         user: Annotated[dict, Depends(get_current_user)],
                         company: bool = Depends(is_company_admin),
                         db: AsyncSession = Depends(get_db_session)):
    """
    Update the details of a company by its ID.

    :param company_id: The ID of the company to update.
    :param company_data: The new data for updating the company.
    :param user: The currently authenticated user.
    :param company: Check if the current user is the owner of the company.
    :param db: The asynchronous database session.
    :return: The updated company details.
    """
    return await update_company_service(company_id=company_id, company_data=company_data, db=db)


@router.delete("/details/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int,
                         user: Annotated[dict, Depends(get_current_user)],
                         company: bool = Depends(is_company_admin),
                         db: AsyncSession = Depends(get_db_session)):
    """
        Delete a company by its ID.

        :param company_id: The ID of the company to delete.
        :param user: The currently authenticated user.
        :param company: Check if the current user is the owner of the company.
        :param db: The asynchronous database session.
        :return: A response indicating the result of the deletion.
        """
    return await delete_company_service(company_id=company_id, db=db)


@router.put("/access/{company_id}")
async def change_company_access(company_id: int,
                                user: Annotated[dict, Depends(get_current_user)],
                                company: bool = Depends(is_company_admin),
                                db: AsyncSession = Depends(get_db_session)):
    """
       Change the access type (public/private) of a company.

       :param company_id: The ID of the company whose access type is to be changed.
       :param user: The currently authenticated user.
       :param company: Check if the current user is the owner of the company.
       :param db: The asynchronous database session.
       :return: The updated access type of the company.
       """
    return await change_company_access_service(company_id=company_id, db=db)


@router.get("/user_inbox/invitations/{user_id}")
@cache(expire=30)
async def get_user_invitations(user_id: int,
                               user: Annotated[dict, Depends(get_current_user)],
                               db: AsyncSession = Depends(get_db_session)):
    """
       Retrieve the inbox of invitations for the current user.

       :param user: The currently authenticated user.
       :param db: The asynchronous database session.
       :return: A list of invitations received by the current user.
       """
    return await get_users_invitations_service(user_id, db)


@router.get("/company_inbox/applications/{company_id}")
@cache(expire=30)
async def get_company_applications(company_id: int,
                                   user: Annotated[dict, Depends(get_current_user)],
                                   company: bool = Depends(is_company_admin),
                                   db: AsyncSession = Depends(get_db_session)):
    return await get_company_applications_service(company_id, db)


@router.get("/company_inbox/invites/{company_id}")
@cache(expire=30)
async def get_company_invites(company_id: int,
                              user: Annotated[dict, Depends(get_current_user)],
                              company: bool = Depends(is_company_admin),
                              db: AsyncSession = Depends(get_db_session)):
    return await get_company_invitations_service(company_id, db)


@router.get("/users_companies")
@cache(expire=30)
async def get_users_companies(user: Annotated[dict, Depends(get_current_user)],
                              db: AsyncSession = Depends(get_db_session)):
    return await get_users_companies_service(user.get("id"), db)


@router.get("/users_applications/{user_id}")
@cache(expire=30)
async def get_users_applications(user_id: int,
                                 user: Annotated[dict, Depends(get_current_user)],
                                 db: AsyncSession = Depends(get_db_session)):
    return await get_users_applications_service(user_id, db)


@router.post("/company_invite",status_code=status.HTTP_201_CREATED)
async def create_company_invite(invitation_letter: InviteLetterSchema,
                                user: Annotated[dict, Depends(get_current_user)],
                                db: AsyncSession = Depends(get_db_session)):
    """
        Create an invitation to invite a user to a company.

        :param invitation_letter: The schema containing details of the invitation.
        "Field invitational_letter.type specifies the type of action. Use 'invite' for invitations and 'application' for requests."
        :param user: The currently authenticated user (must be the company owner).
        :param db: The asynchronous database session.
        :return: The created invitation letter.
        """
    await is_company_admin(invitation_letter.company_id, user, db)
    return await create_invitational_letter(user, invitation_letter, db)


@router.post("/company_application",status_code=status.HTTP_201_CREATED)
async def create_company_application(application_letter: ApplicationLetterSchema,
                                     user: Annotated[dict, Depends(get_current_user)],
                                     db: AsyncSession = Depends(get_db_session)):
    """
        Create an application from user to a company.

        :param application_letter: The schema containing details of the application
        :param user: The currently authenticated user (must be the company owner).
        :param db: The asynchronous database session.
        :return: The created invitation letter.
        """
    return await create_application_letter(user, application_letter, db)


@router.delete("/{company_id}/membership_stop/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def user_stop_membership(company_id: int,
                               user_id:int,
                               user: Annotated[dict, Depends(get_current_user)],
                               db: AsyncSession = Depends(get_db_session)):
    return await delete_company_member_service(user_id=user_id, company_id=company_id, db=db)


@router.delete("/company_invitation/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitational_letter(invitation_id: int,
                                     user: Annotated[dict, Depends(get_current_user)],
                                     invitation: bool = Depends(is_invitation_sender),
                                     db: AsyncSession = Depends(get_db_session)):
    """
        Revoke a previously sent invitation.

        :param invitation_id: The ID of the invitation to revoke.
        :param user: The currently authenticated user (must be the sender of the invitation).
        :param invitation: Ensure the user is the sender of the invitation.
        :param db: The asynchronous database session.
        :return: The result of the invitation revocation.
        """
    return await delete_invitational_letter_service(invitation_id, db)


@router.post("/company_invite/answer/{invitation_id}")
async def invitational_answer(invitation_id: int,
                              invitation_answer: InviteApplicationAnswerSchema,
                              user: Annotated[dict, Depends(get_current_user)],
                              invitation: bool = Depends(is_invitation_receiver),
                              db: AsyncSession = Depends(get_db_session)):
    return await invitational_answer_letter_service(invitation_id, invitation_answer, db)


@router.post("/company_application/answer/{application_id}")
async def application_answer(application_id: int,
                             application_answer: InviteApplicationAnswerSchema,
                             user: Annotated[dict, Depends(get_current_user)],
                             application: bool = Depends(is_application_receiver),
                             db: AsyncSession = Depends(get_db_session)):
    return await application_answer_letter_service(application_id, application_answer, db)


@router.get("/admin_user/{company_id}")
@cache(expire=30)
async def get_company_admin_user_list(company_id: int,
                                      user: Annotated[dict, Depends(get_current_user)],
                                      company: bool = Depends(is_company_admin),
                                      db: AsyncSession = Depends(get_db_session)):
    return await get_company_admin_user_service(company_id, db)


@router.post("/admin_user/{company_id}")
async def create_company_admin_user(company_id: int,
                                    admin_user_request: CreateDeleteCompanyAdminSchema,
                                    user: Annotated[dict, Depends(get_current_user)],
                                    company: bool = Depends(is_company_owner),
                                    db: AsyncSession = Depends(get_db_session)):
    return await create_company_admin_user_service(company_id=company_id, admin_user_request=admin_user_request, db=db)


@router.delete("/admin_user/{company_id}")
async def delete_company_admin_user(company_id: int,
                                    admin_user_request: CreateDeleteCompanyAdminSchema,
                                    user: Annotated[dict, Depends(get_current_user)],
                                    company: bool = Depends(is_company_owner),
                                    db: AsyncSession = Depends(get_db_session)):
    return await delete_company_admin_user_service(company_id=company_id, admin_user_request=admin_user_request, db=db)


@router.get("/company_roles")
async def get_company_roles(db: AsyncSession = Depends(get_db_session)):
    """
         Retrieve a list of all roles in a company.

         :param db: The asynchronous database session.
         :return: the list of all roles in a company.
         """
    return await get_company_roles_service(db)
