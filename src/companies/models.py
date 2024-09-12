from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey

from src.database.base import Base

class InvitationStatusEnum(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INPROCESS = "inprocess"


class Company(Base):
    __tablename__ = 'company'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_private = Column(Boolean, nullable=False, default=False)
    registration_date = Column(DateTime(), default=datetime.utcnow)


class CompanyMember(Base):
    __tablename__ = 'company_member'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    company_id = Column(Integer, ForeignKey('company.id', ondelete='CASCADE'))
    role = Column(Integer, ForeignKey('company_role.id', ondelete="CASCADE"))
    registration_date = Column(DateTime(), default=datetime.utcnow)


class CompanyRole(Base):
    __tablename__ = 'company_role'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    def __str__(self):
        return self.name


class Invitation(Base):
    __tablename__ = 'invitation'

    id = Column(Integer, primary_key=True)
    sender_user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    receiver_user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    company_id = Column(Integer, ForeignKey('company.id', ondelete='CASCADE'))
    status = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    registration_date = Column(DateTime(), default=datetime.utcnow)

class Application(Base):
    __tablename__ = 'application'

    id = Column(Integer, primary_key=True)
    sender_user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    company_id = Column(Integer, ForeignKey('company.id', ondelete='CASCADE'))
    status = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    registration_date = Column(DateTime(), default=datetime.utcnow)

