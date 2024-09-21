from typing import Annotated

from fastapi import (APIRouter,
                     Depends,
                     HTTPException,
                     status, )
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_cache.decorator import cache
from fastapi_pagination.links import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.auth.models import User
from src.auth.schemas import (UserCreate,
                              UserUpdateRequestModel,
                              UserPasswordUpdateRequestModel, Token, UserRead, )
from src.auth.services import (
    create_user_service,
    delete_user_service,
    get_user_by_id_service,
    update_user_service,
    user_update_password_service, )
from src.utils.utils_auth import authenticate_user, create_access_token, get_current_user
from src.database.database import get_db_session

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.get("/users", response_model=Page[UserRead])
async def get_users(db: AsyncSession = Depends(get_db_session)):
    return await paginate(db, select(User).order_by(User.registration_date))


@router.post("/users/register")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    return await create_user_service(user, db)


@router.post("/jwt/login", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: AsyncSession = Depends(get_db_session)):
    user = await authenticate_user(form_data, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate the user")
    token = create_access_token(user_id=user.id, username=user.username)
    response = JSONResponse(content={"access_token": token, 'token_type': "bearer"})
    response.set_cookie('access_token', token)
    return {"access_token": token, 'token_type': "bearer"}


@router.get("/users/{user_id}")
async def get_direct_user_by_id(user_id: int, db: AsyncSession = Depends(get_db_session)):
    return await get_user_by_id_service(user_id, db)


@router.put("/users/{user_id}")
async def user_update(user_id: int, user_update_request: UserUpdateRequestModel,
                      db: AsyncSession = Depends(get_db_session)):
    return await update_user_service(user_id, user_update_request, db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def user_delete(user_id: int,
                      user: Annotated[dict, Depends(get_current_user)],
                      db: AsyncSession = Depends(get_db_session)):
    return await delete_user_service(user_id, db)


@router.put("/users/password/{user_id}")
async def user_password_update(user_id: int,
                               user_password_update_request: UserPasswordUpdateRequestModel,
                               db: AsyncSession = Depends(get_db_session)):
    return await user_update_password_service(user_id, user_password_update_request, db)
