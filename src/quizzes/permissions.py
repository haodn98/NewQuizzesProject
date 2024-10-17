from fastapi import Depends, status, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from core.mongo_config import get_mongo_database
from quizzes.manager import QuizManager, QuizNotFound


async def is_company_quiz(company_id, quiz_id, db: AsyncIOMotorCollection = Depends(get_mongo_database)):
    try:
        quiz = await QuizManager.get_quiz(db, quiz_id)
        if not str(quiz["company_id"]) == company_id:
            raise HTTPException(detail="Company does not related to quiz", status_code=status.HTTP_403_FORBIDDEN )
        return True
    except QuizNotFound:
        raise HTTPException(detail="Quiz not found", status_code=status.HTTP_404_NOT_FOUND)
    except ValueError:
        raise HTTPException(detail="Invalid Quiz id", status_code=status.HTTP_400_BAD_REQUEST)