from fastapi import Depends, status, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from src.core.mongo_config import get_mongo_database
from src.quizzes.manager import QuizManager


async def is_company_quiz(company_id, quiz_id, db: AsyncIOMotorCollection = Depends(get_mongo_database)):
    quiz = await QuizManager.get_quiz(db, quiz_id)
    if not str(quiz["company_id"]) == company_id:
        raise HTTPException(detail="Company does not related to quiz", status_code=status.HTTP_403_FORBIDDEN )
    return True
