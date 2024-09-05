from typing import List

from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: int
    username: str
    email: str


class UserCreate(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    email: str = Field(max_length=50)
    password: str = Field(min_length=8, max_length=100)


class UserUpdateRequestModel(BaseModel):
    email: str = Field(min_length=6, max_length=50)


class UserPasswordUpdateRequestModel(BaseModel):
    password: str = Field(min_length=8, max_length=100)
    new_password: str = Field(min_length=8, max_length=100)


class UserListResponseModel(BaseModel):
    users: List[UserRead]

class Token(BaseModel):
    access_token: str
    token_type: str