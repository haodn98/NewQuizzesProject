import logging
from fastapi import status, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserRead
from src.database import get_db_session
from src.utils.utils_auth import bcrypt_context, Validation

logger = logging.getLogger(__name__)

async def get_all_users_service(db: AsyncSession):
    try:
        result = await db.execute(select(User.id, User.username, User.email))
        all_users = [UserRead(id=user[0], username=user[1], email=user[2]) for user in result.all()]
        return all_users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def get_user_by_id_service(user_id: int, db: AsyncSession):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def create_user_service(user_to_create, db: AsyncSession = Depends(get_db_session)):
    try:
        Validation.validate_password(user_to_create.password)
        Validation.validate_email(user_to_create.email)
        new_user = User(
            username=user_to_create.username,
            email=user_to_create.email,
            hashed_password=bcrypt_context.hash(user_to_create.password),
            is_active=True,
            is_superuser=False,
            is_staff=False,
            is_deleted=False
        )
        db.add(new_user)
        await db.commit()
        logger.info(f"User created with email: {new_user.email}")
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def update_user_service(user_id: int, user_update_request, db: AsyncSession = Depends(get_db_session), ):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        for key, value in user_update_request.dict(exclude_unset=True).items():
            setattr(user, key, value)
            if key == "email":
                Validation.validate_email(value)

        db.add(user)
        await db.commit()
        logger.info(
            f"User with ID {user_id} updated with data: "
            f"{ {key: value for key, value in user_update_request.dict(exclude_unset=True).items()} }"
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def delete_user_service(user: dict, db: AsyncSession):
    try:
        result = await db.execute(select(User).where(User.id == user.get("id")))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await db.delete(user)
        await db.commit()
        logger.info(f"User with ID {user.id} deleted")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def user_update_password_service(user_id: int, user_new_password_request, db: AsyncSession):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if not bcrypt_context.verify(user_new_password_request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    Validation.validate_password(user_new_password_request.new_password)
    user.hashed_password = bcrypt_context.hash(user_new_password_request.new_password)
    await db.commit()

    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
