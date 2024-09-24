import pytest
from fastapi import status
from fastapi_pagination import response
from httpx import AsyncClient
from sqlalchemy import text, select

from src.auth.models import User
from src.companies.models import Application, InvitationStatusEnum, Invitation, Company, CompanyMember
from src.utils.utils_auth import bcrypt_context
from tests.conftest import ac, async_session_test, test_engine, test_company_roles


@pytest.fixture(scope='module')
async def test_user_for_company_test():
    user = User(
        email="Test2@testt.com",
        username="TestUser2",
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


@pytest.fixture()
async def test_company_member_for_company_test(test_user, test_company_roles, test_user_for_company_test,
                                               test_company_with_member):
    company_member = CompanyMember(
        user_id=test_user_for_company_test.id,
        company_id=test_company_with_member.id,
        role=next(role.id for role in test_company_roles if role.name == "member")
    )
    async with async_session_test() as db:
        db.add(company_member)
        await db.commit()
    yield company_member
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "company_member";'))
        await connection.commit()


@pytest.fixture(scope='module')
async def test_company_for_company_test():
    company = Company(
        name="test company for company test",
        description="test company descriptions",
    )
    async with async_session_test() as db:
        db.add(company)
        await db.commit()
    yield company
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "company";'))
        await connection.commit()


@pytest.fixture()
async def test_application(test_user_for_company_test, test_company_with_member):
    application = Application(
        sender_user_id=test_user_for_company_test.id,
        company_id=test_company_with_member.id,
        status=InvitationStatusEnum.INPROCESS.value,
    )
    async with async_session_test() as db:
        db.add(application)
        await db.commit()
    yield application
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "application";'))
        await connection.commit()


@pytest.fixture()
async def test_invitation(test_user, test_user_for_company_test,test_company_without_member):
    invitation = Invitation(
        sender_user_id=test_user_for_company_test.id,
        receiver_user_id=test_user.id,
        company_id=test_company_without_member.id,
        status=InvitationStatusEnum.INPROCESS.value,
    )
    async with async_session_test() as db:
        db.add(invitation)
        await db.commit()
    yield invitation
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "invitation";'))
        await connection.commit()


async def test_get_all_companies(ac: AsyncClient, test_company_with_member):
    response = await ac.get('/companies')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"][0]["name"] == "test company with members"


async def test_get_company_by_id(ac: AsyncClient, test_company_with_member):
    response = await ac.get(f'/companies/details/{test_company_with_member.id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "test company with members"


async def test_get_company_by_id_wrong_id(ac: AsyncClient):
    response = await ac.get(f'/companies/details/1000')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_company(ac: AsyncClient, test_user, test_company_roles):
    company_data = {
        "name": "test new company",
        "description": "test new company description",
    }
    response = await ac.post('/companies', json=company_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "test new company"


async def test_update_company(ac: AsyncClient, test_company_with_member):
    company_data = {
        "name": "test new company",
        "description": "new test new company description",
    }
    response = await ac.put(f'/companies/details/{test_company_with_member.id}', json=company_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["description"] == "new test new company description"


async def test_update_company_wrong_id(ac: AsyncClient):
    company_data = {
        "name": "test new company",
        "description": "new test new company description",
    }
    response = await ac.put('/companies/details/1000', json=company_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_company(ac: AsyncClient, test_user, test_company_roles):
    test_company_for_delete = Company(
        name="we will delete you",
        description="we will delete you",
    )
    async with async_session_test() as db:
        db.add(test_company_for_delete)
        await db.commit()
        await db.refresh(test_company_for_delete)
        company_member = CompanyMember(
            user_id=test_user.id,
            company_id=test_company_for_delete.id,
            role=next(role.id for role in test_company_roles if role.name == "owner")
        )
        db.add(company_member)
        await db.commit()
    response = await ac.delete(f'/companies/details/{test_company_for_delete.id}')

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_delete_company_wrong_id(ac: AsyncClient):
    response = await ac.delete('/companies/details/1000')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_company_repeatable_name(ac: AsyncClient, test_company_with_member):
    company_data = {
        "name": "test company with members",
        "description": "test company description",
    }
    response = await ac.post('/companies', json=company_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_update_change_company_access(ac: AsyncClient, test_company_with_member):
    response = await ac.put(f'/companies/access/{test_company_with_member.id}')

    assert response.json()["is_private"] == True
    assert response.status_code == status.HTTP_200_OK


async def test_update_change_company_access_wrong_id(ac: AsyncClient):
    response = await ac.put('/companies/access/1000')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_company_members(ac: AsyncClient, test_user, test_company_with_member):
    response = await ac.get(f'/companies/details/{test_company_with_member.id}/members')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


async def test_get_company_members_wrong_id(ac: AsyncClient):
    response = await ac.get('/companies/details/1000/members')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_company_roles(ac: AsyncClient, test_company_roles):
    response = await ac.get(f'/companies/company_roles')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": 1, "name": "owner"},
                               {"id": 2, "name": "admin"},
                               {"id": 3, "name": "member"}]


async def test_get_user_invitations(ac: AsyncClient, test_user, test_invitation):
    response = await ac.get(f'/companies/user_inbox/invitations/{test_user.id}')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


async def test_get_user_invitations_wrong_user_id(ac: AsyncClient, ):
    response = await ac.get('/companies/user_inbox/invitations/1000')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_company_applications(ac: AsyncClient, test_company_with_member, test_application):
    response = await ac.get(f'/companies/company_inbox/applications/{test_company_with_member.id}')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


async def test_get_company_applications_wrong_id(ac: AsyncClient):
    response = await ac.get('/companies/company_inbox/applications/1000')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_users_applications(ac: AsyncClient, test_user_for_company_test, test_application):
    response = await ac.get(f"/companies/users_applications/{test_user_for_company_test.id}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


async def test_get_users_applications_wrong_id(ac: AsyncClient, test_user_for_company_test, test_application):
    response = await ac.get("/companies/users_applications/1000")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_company_invite(ac: AsyncClient, test_user_for_company_test, test_company_with_member):
    invitation_data = {
        "receiver_user_id": test_user_for_company_test.id,
        "company_id": test_company_with_member.id,
    }
    response = await ac.post('/companies/company_invite', json=invitation_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["receiver_user_id"] == test_user_for_company_test.id
    assert response.json()["status"] == InvitationStatusEnum.INPROCESS.value


async def test_create_company_invite_to_yourself(ac: AsyncClient, test_user, test_company_with_member):
    invitation_data = {
        "receiver_user_id": test_user.id,
        "company_id": test_company_with_member.id,
    }
    response = await ac.post('/companies/company_invite', json=invitation_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == 'Cannot send invitation to yourself'


async def test_create_company_invite_wrong_company_id(ac: AsyncClient, test_user_for_company_test,
                                                      test_company_with_member):
    invitation_data = {
        "receiver_user_id": test_user_for_company_test.id,
        "company_id": 4000,
    }
    response = await ac.post('/companies/company_invite', json=invitation_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_company_application(ac: AsyncClient, test_company_for_company_test):
    application_data = {
        "company_id": test_company_for_company_test.id,
    }

    response = await ac.post('/companies/company_application', json=application_data)

    assert response.status_code == status.HTTP_201_CREATED


async def test_create_company_application_does_not_exist(ac: AsyncClient,
                                                         test_user_for_company_test,
                                                         test_company_for_company_test):
    application_data = {
        "company_id": 400,
    }
    response = await ac.post('/companies/company_application', json=application_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company not found"


async def test_delete_invitation_letter(ac: AsyncClient,
                                        test_user,
                                        test_company_with_member,
                                        ):
    invitation = Invitation(
        sender_user_id=test_user.id,
        receiver_user_id=test_company_with_member.id,
        company_id=test_company_with_member.id,
        status=InvitationStatusEnum.INPROCESS.value,
    )
    async with async_session_test() as db:
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
    response = await ac.delete(f"/companies/company_invitation/{invitation.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

async def test_delete_invitation_letter_wrong_id(ac: AsyncClient,
                                                 test_user,
                                                 test_company_with_member):

    response = await ac.delete(f"/companies/company_invitation/1000")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Invitation does not exist"

async def test_invitation_answer_accepted(ac: AsyncClient,
                                        test_user,
                                        test_company_without_member,
                                        test_invitation
                                        ):
    invitation_form = {
        "answer":"accepted"
    }
    response = await ac.post(f"/companies/company_invite/answer/{test_invitation.id}",
                             json=invitation_form)
    async with async_session_test() as db:
        invitation = await db.execute( select(Invitation).where(Invitation.id == test_invitation.id))
        invitation = invitation.scalar_one_or_none()
        company_member = await db.execute(select(CompanyMember).where(CompanyMember.user_id == invitation.receiver_user_id,
                                                                      CompanyMember.company_id == invitation.company_id))
        company_member = company_member.scalar_one_or_none()
        await db.delete(company_member)
        await db.commit()
    assert response.status_code == status.HTTP_200_OK
    assert invitation.status == InvitationStatusEnum.ACCEPTED.value

async def test_invitation_answer_rejected(ac: AsyncClient,
                                        test_user,
                                        test_company_without_member,
                                        test_invitation
                                        ):
    invitation_form = {
        "answer":"rejected"
    }
    response = await ac.post(f"/companies/company_invite/answer/{test_invitation.id}",
                             json=invitation_form)
    async with async_session_test() as db:
        invitation = await db.execute( select(Invitation).where(Invitation.id == test_invitation.id))
        invitation = invitation.scalar_one_or_none()
    assert response.status_code == status.HTTP_200_OK
    assert invitation.status == InvitationStatusEnum.REJECTED.value

async def test_invitation_answer_rejected_403(ac: AsyncClient,
                                        test_invitation
                                        ):
    invitation_form = {
        "answer":"rejected"
    }
    response = await ac.post(f"/companies/company_invite/answer/{test_invitation.id}",
                             json=invitation_form)
    async with async_session_test() as db:
        invitation = await db.execute( select(Invitation).where(Invitation.id == test_invitation.id))
        invitation = invitation.scalar_one_or_none()
    assert response.status_code == status.HTTP_200_OK
    assert invitation.status == InvitationStatusEnum.REJECTED.value
    assert response.json()["detail"] == 'Invitation was rejected.'

async def test_invitation_answer_wrong_id(ac: AsyncClient,
                                        test_user,
                                        test_company_without_member,
                                        test_invitation
                                        ):
    invitation_form = {
        "answer":"accepted"
    }
    response = await ac.post(f"/companies/company_invite/answer/1000",
                             json=invitation_form)

    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_application_answer_accepted(ac: AsyncClient,
                                        test_user,
                                        test_company_with_member,
                                        test_application
                                        ):
    application_form = {
        "answer":"accepted"
    }
    response = await ac.post(f"/companies/company_application/answer/{test_application.id}",
                             json=application_form)
    async with async_session_test() as db:
        application = await db.execute( select(Application).where(Application.id == test_application.id))
        application = application.scalar_one_or_none()
        company_member = await db.execute(select(CompanyMember).where(CompanyMember.user_id == application.sender_user_id,
                                                                      CompanyMember.company_id == application.company_id))
        company_member = company_member.scalar_one_or_none()
        await db.delete(company_member)
        await db.commit()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == InvitationStatusEnum.ACCEPTED.value

async def test_application_answer_rejected(ac: AsyncClient,
                                        test_user,
                                        test_company_without_member,
                                        test_application
                                        ):
    application_form = {
        "answer":"rejected"
    }
    response = await ac.post(f"/companies/company_application/answer/{test_application.id}",
                             json=application_form)
    async with async_session_test() as db:
        application = await db.execute(select(Application).where(Application.id == test_application.id))
        application = application.scalar_one_or_none()
    assert response.status_code == status.HTTP_200_OK
    assert application.status == InvitationStatusEnum.REJECTED.value

async def test_application_answer_wrong_id(ac: AsyncClient,
                                        test_user
                                        ):
    application_form = {
        "answer":"rejected"
    }
    response = await ac.post(f"/companies/company_application/answer/1000",
                             json=application_form)

    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_user_stop_membership(ac: AsyncClient,
                                    test_user_for_company_test,
                                    test_company_with_member,
                                    test_company_roles):
    company_member = CompanyMember(
        user_id = test_user_for_company_test.id,
        company_id = test_company_with_member.id,
        role = next(role.id for role in test_company_roles if role.name == "member")
    )
    async with async_session_test() as db:
        db.add(company_member)
        await db.commit()
    response = await ac.delete(
        f"/companies/{test_company_with_member.id}/membership_stop/{test_user_for_company_test.id}"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

async def test_user_stop_membership_wrong_company_id(ac: AsyncClient,
                                    test_user_for_company_test):
    response = await ac.delete(
        f"/companies/1000/membership_stop/{test_user_for_company_test.id}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Company does not exist"

async def test_user_stop_membership_wrong_user_id(ac: AsyncClient,
                                                     test_company_with_member,
                                                     test_company_roles):
    response = await ac.delete(
        f"/companies/{test_company_with_member.id}/membership_stop/1000"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User does not exist"

async def test_get_company_admin_list(ac: AsyncClient,test_user,test_company_with_member):
    response = await ac.get(f"/companies/admin_user/{test_company_with_member.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["user_id"] == test_user.id


async def test_get_company_admin_list_wrong_id(ac: AsyncClient):
    response = await ac.get(f"/companies/admin_user/1000")
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_create_admin_user(ac: AsyncClient,
                                     test_user,
                                     test_company_with_member,
                                     test_user_for_company_test,
                                     test_company_roles,
                                     test_company_member_for_company_test):
    admin_user_form={
        "user_id":test_user_for_company_test.id,
    }
    response = await ac.post(f"/companies/admin_user/{test_company_with_member.id}",
                             json=admin_user_form)

    assert response.status_code == status.HTTP_200_OK

# async def test_delete_admin_user(ac: AsyncClient,
#                                      test_user,
#                                      test_company_with_member,
#                                      test_user_for_company_test,
#                                      test_company_roles,
#                                      test_company_member_for_company_test):
#     admin_user_form={
#         "user_id":test_user_for_company_test.id,
#     }
#     response = await ac.delete(f"/companies/admin_user/{test_company_with_member.id}",params=admin_user_form)
#
#     assert response.status_code == status.HTTP_204_NO_CONTENT



async def test_create_admin_user_wrong_id(ac: AsyncClient,test_user):
    admin_user_form={
        "user_id":test_user.id,
    }
    response = await ac.post(f"/companies/admin_user/1000",
                             json=admin_user_form)
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_create_admin_user_wrong_user_id(ac: AsyncClient,test_company_with_member):
    admin_user_form={
        "user_id":1000,
    }
    response = await ac.post(f"/companies/admin_user/{test_company_with_member.id}",
                             json=admin_user_form)
    assert response.status_code == status.HTTP_403_FORBIDDEN


