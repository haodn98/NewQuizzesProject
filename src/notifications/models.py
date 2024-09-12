from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from src.database.base import Base

class Notification(Base):
    __tablename__ = 'notification'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    company_id = Column(Integer, ForeignKey('company.id'))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow())