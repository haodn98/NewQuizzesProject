from pydantic import BaseModel, Field


class NotificationSchema(BaseModel):
    title: str = Field(max_length=100)
    content: str = Field(max_length=250)
    user_id: int
    company_id: int

