import jwt
import pytest
from dns.dnssecalgs import algorithms
from httpx import AsyncClient
from starlette import status

from src.auth import factories
from src.auth.models import User
from src.utils.utils_auth import authenticate_user
from src.core.config import settings
from tests.conftest import ac, async_session_test


@pytest.mark.asyncio
async def test_get_all_users(ac: AsyncClient, test_user):
    await factories.UserFactory.create_batch(10)

    response = await ac.get("/auth/users")
    assert len(response.json()["items"]) == 11
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_all_users_paginated(ac: AsyncClient, test_user):
    await factories.UserFactory.create_batch(10)

    response = await ac.get("/auth/users?page=1&size=5")
    assert len(response.json()["items"]) == 5
    assert response.status_code == 200

async def test_get_user_by_id(ac: AsyncClient, test_user):

    response = await ac.get(f"/auth/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id

async def test_get_user_by_id_wrong_id(ac: AsyncClient):

    response = await ac.get(f"/auth/users/1000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"



async def test_login(ac: AsyncClient, test_user):
    data = {"username": test_user.username, "password": "testpassword"}
    response = await ac.post("/auth/jwt/login", data=data)

    assert response.json()["access_token"]
    decode_token = jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decode_token["username"] == test_user.username
    assert decode_token["id"] == test_user.id

async def test_login_no_user(ac: AsyncClient):
    data = {"username": "user_name", "password": "testpassword"}
    response = await ac.post("/auth/jwt/login", data=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




async def test_login_wrong_credentials(ac: AsyncClient, test_user):
    data = {"username": test_user.username, "password": "some_password"}
    response = await ac.post("/auth/jwt/login", data=data)
    assert response.status_code == 401

    data = {"username": "some_username", "password": "some_password"}
    response = await ac.post("/auth/jwt/login", data=data)
    assert response.status_code == 401


async def test_create_user(ac: AsyncClient):
    new_test_user = {"username": "Test_user",
                     "password": "PasswordTest123!",
                     "email": "tesssst@email.com"}
    response = await ac.post("/auth/users/register", json=new_test_user)
    assert response.json()["username"] == new_test_user["username"]
    assert response.json()["email"] == new_test_user["email"]
    assert response.status_code == 200


async def test_create_user_short_password(ac: AsyncClient):
    new_test_user = {"username": "Test_user",
                     "password": "123!",
                     "email": "tesssst@email.com"}
    response = await ac.post("/auth/users/register", json=new_test_user)
    assert response.status_code == 422


async def test_create_user_weak_password(ac: AsyncClient):
    new_test_user = {"username": "Test_user",
                     "password": "11111111111",
                     "email": "tesssst@email.com"}
    response = await ac.post("/auth/users/register", json=new_test_user)
    assert response.json()[
               "detail"] == "{'detail': 'Password should include at least one uppercase latter, one lowercase letter, one digit and one symbol'}"
    assert response.status_code == 500


async def test_user_update(ac: AsyncClient, test_user):
    used_data = {"email": "new_test_email@test.com"}
    response = await ac.put(f"/auth/users/{test_user.id}", json=used_data)

    assert response.status_code == 200
    assert response.json()["email"] == used_data["email"]


async def test_user_update_wrong_email(ac: AsyncClient, test_user):
    used_data = {"email": "new_test_email@test"}
    response = await ac.put(f"/auth/users/{test_user.id}", json=used_data)

    assert response.json()["detail"] == 'Email is invalid'
    assert response.status_code == 500


async def test_user_update_wrong_id(ac: AsyncClient, test_user):
    used_data = {"email": "new_test_email@test.com"}
    response = await ac.put("/auth/users/1000", json=used_data)
    assert response.status_code == 404


async def test_password_update(ac: AsyncClient, test_user):
    used_data = {"password": "testpassword",
                 "new_password": "Itsnewpassword123!", }
    response = await ac.put(f"/auth/users/password/{test_user.id}", json=used_data)

    assert response.status_code == 200


async def test_user_delete(ac: AsyncClient, ):
    async with async_session_test() as session:
        test_user = User(
            username="TestUserDelete",
            email="TestUserDelete@gmail.com",
            hashed_password="testpassword",

        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
    response = await ac.delete(f"/auth/users/{test_user.id}")

    assert response.status_code == 204


async def test_user_delete_wrong_id(ac: AsyncClient):
    response = await ac.delete("/auth/users/10000")

    assert response.status_code == 404
