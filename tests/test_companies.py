import pytest
from fastapi import status
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

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
async def test_invitation(test_user,test_user_for_company_test, test_company_with_member):
    invitation = Invitation(
        sender_user_id=test_user.id,
        receiver_user_id=test_user_for_company_test.id,
        company_id=test_company_with_member.id,
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
    assert response.json()["items"][0]["name"] == "test company"


async def test_get_company_by_id(ac: AsyncClient, test_company_with_member):
    response = await ac.get(f'/companies/details/{test_company_with_member.id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "test company"


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
        "name": "test company",
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

async def test_get_user_invitations(ac: AsyncClient, test_user_for_company_test,test_invitation):
    response = await ac.get(f'/companies/user_inbox/invitations/{test_user_for_company_test.id}')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

async def test_get_user_invitations_wrong_id(ac: AsyncClient,):
    response = await ac.get('/companies/user_inbox/invitations/1000')

    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_get_company_applications(ac: AsyncClient, test_company_with_member,test_application):
    response = await ac.get(f'/companies/company_inbox/applications/{test_company_with_member.id}')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
