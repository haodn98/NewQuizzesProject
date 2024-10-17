import re
from datetime import datetime, timedelta
from string import punctuation
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy import select

from src.auth.models import User
from src.core.config import settings
from src.database.database import AsyncSession

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/jwt/login")


async def authenticate_user(user_to_login, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == user_to_login.username))
    user = result.scalar_one_or_none()
    if not user:
        return False
    if not bcrypt_context.verify(user_to_login.password, user.hashed_password):
        return False
    return user


def create_access_token(user_id: int, username: str):
    encode = {
        "id": user_id,
        "username": username
    }
    encode.update(
        {"exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)}
    )

    return jwt.encode(encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("username")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate the user")
        return {"username": username,
                "id": user_id, }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate the user")


class Validation:

    @staticmethod
    def validate_password(password_to_validate: str) -> None:
        if len(password_to_validate) < 8:
            raise ValidationError("Password length should be at least 8 characters ")
        if (not any(symbol.isdigit() for symbol in password_to_validate)
                or not any(symbol.islower() for symbol in password_to_validate)
                or not any(symbol.isupper() for symbol in password_to_validate)
                or not any(symbol in punctuation for symbol in password_to_validate)):
            raise ValueError({"detail":
                                  "Password should include at least one uppercase latter, one lowercase letter, one digit and one symbol"})

    @staticmethod
    def validate_email(email_to_validate: str) -> None:
        pattern = r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
        if not re.match(pattern, email_to_validate):
            raise ValueError("Email is invalid")
