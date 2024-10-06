import logging
from fastapi import status, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from database.database import get_db_session
from utils.utils_auth import bcrypt_context, Validation

logger = logging.getLogger(__name__)


async def get_user_by_id_service(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return user


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
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for key, value in user_update_request.dict(exclude_unset=True).items():
        setattr(user, key, value)
        if key == "email":
            try:
                Validation.validate_email(value)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
    db.add(user)
    await db.commit()
    logger.info(
        f"User with ID {user_id} updated with data: "
        f"{ {key: value for key, value in user_update_request.dict(exclude_unset=True).items()} }"
    )
    return user


async def delete_user_service(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await db.delete(user)
    await db.commit()
    logger.info(f"User with ID {user.id} deleted")


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
