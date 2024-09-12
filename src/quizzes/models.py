from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, String

from src.database.base import Base


class QuizResults(Base):
    __tablename__ = 'quiz_result'

    id = Column(Integer, primary_key=True)
    quiz_id = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    company_id = Column(Integer, ForeignKey('company.id'))
    result = Column(Float, nullable=False)
    questions_overall = Column(Integer)
    quiz_date = Column(DateTime, nullable=False, default=datetime.utcnow)
