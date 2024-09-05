from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CompanyCreateUpdateSchema(BaseModel):
    name: str = Field(max_length=50)
    description: str = Field(max_length=100)
    is_private: bool = Field(default=False)


class CompanyRead(BaseModel):
    id: int
    name: str = Field(max_length=50)
    description: str = Field(max_length=100)
    registration_date: datetime


class CompanyMemberDeleteSchema(BaseModel):
    user_id: int

class LeaveCompanySchema(BaseModel):
    company_id: int


class InviteLetterSchema(BaseModel):
    receiver_user_id: int
    company_id: int


class ApplicationLetterSchema(BaseModel):
    company_id: int


class InviteApplicationAnswerSchema(BaseModel):
    answer: Literal['accepted', 'rejected']

class CreateDeleteCompanyAdminSchema(BaseModel):
    user_id: int