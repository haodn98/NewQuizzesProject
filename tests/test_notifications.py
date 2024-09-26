import pytest
from httpx import AsyncClient
from sqlalchemy import text
from starlette import status

from src.notifications.models import Notification
from tests.conftest import async_session_test, test_engine


@pytest.fixture(scope="function")
async def test_notification(test_user, test_company_with_member):
    notification = Notification(
        title="Test Notification",
        content="Test Notification content",
        user_id=test_user.id,
        company_id=test_company_with_member.id
    )

    async with async_session_test() as db:
        db.add(notification)
        await db.commit()
    yield notification
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "notification";'))
        await connection.commit()


async def test_get_all_notifications(ac: AsyncClient, test_user, test_company_with_member, test_notification):
    response = await ac.get(f'/notifications/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

async def test_user_make_notification_read(ac: AsyncClient, test_notification):
    response = await ac.post(f'/notifications/{test_notification.id}/read')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_read"] is True

async def test_user_make_notification_read_wrong_id(ac: AsyncClient,):
    response = await ac.post(f'/notifications/1000/read')

    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_create_notification(ac: AsyncClient,test_user,test_company_with_member):
    notification = {
        "title":"Test Notification New",
        "content":"Test Notification content",
        "user_id":test_user.id,
        "company_id":test_company_with_member.id
    }
    response = await ac.post(f'/notifications/',json=notification)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == notification["title"]

async def test_create_notification_wrong_form(ac: AsyncClient,test_user,test_company_with_member):
    notification = {

        "content":"Test Notification content",
        "user_id":test_user.id,
        "company_id":test_company_with_member.id
    }
    response = await ac.post(f'/notifications/',json=notification)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY