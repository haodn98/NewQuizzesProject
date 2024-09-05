from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from src.base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(), nullable=False)
    is_verified = Column(Boolean(), default=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    is_deleted = Column(Boolean(), default=False)
    is_staff = Column(Boolean(), default=False)
    registration_date = Column(DateTime(), default=datetime.utcnow)
