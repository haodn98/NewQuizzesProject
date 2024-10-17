import asyncio
import logging
from datetime import timedelta, datetime

from celery import shared_task
from fastapi.params import Depends
from sqlalchemy import func, select
from motor.motor_asyncio import AsyncIOMotorCollection

from src.core.mongo_config import get_mongo_database
from src.database.database import async_session
from src.notifications.services import create_notifications_service
from src.quizzes.manager import QuizManager
from src.quizzes.models import QuizResults

logger = logging.getLogger(__name__)


@shared_task
async def quiz_remind_notification(db_mongo: AsyncIOMotorCollection = Depends(get_mongo_database)):
    with async_session() as session:
        query = select(
            QuizResults.user_id,
            QuizResults.quiz_id,
            QuizResults.company_id,
            func.max(QuizResults.quiz_date).label('last_attempt_date')
        ).group_by(
            QuizResults.user_id,
            QuizResults.quiz_id,
            QuizResults.company_id,
        ).order_by(
            QuizResults.user_id,
            QuizResults.quiz_id,
            QuizResults.company_id,
        )
        quiz_results = await session.execute(query)
        quiz_results = quiz_results.scalars().all()
        quizzes_ids = set(quiz.quiz_id for quiz in quiz_results)

        quizzes_data = await QuizManager.quiz_filter(db=db_mongo, query={"_id": {"$in": list(quizzes_ids)}},
                                                     projection={"_id": 1, "frequency": 1, "name": 1})
        quizzes_data = {quiz["_id"]: quiz for quiz in quizzes_data}

        for quiz in quiz_results:
            user_id = quiz.user_id
            quiz_id = quiz.quiz_id
            company_id = quiz.company_id
            last_attempt_date = quiz.last_attempt_date
            quiz_info = quizzes_data.get(quiz_id)
            if quiz_info:
                frequency = quiz_info.get('frequency')
                if frequency:

                    next_allowed_date = last_attempt_date + timedelta(days=frequency)
                    if next_allowed_date <= datetime.utcnow():
                        notification = {
                            "title": f"Time to repeat the quiz ",
                            "content": f'You took "{quiz["name"]}" so long time ago! Time to repeat',
                            "company_id": company_id,
                            "user_id": user_id,
                        }
                        await create_notifications_service(db=session, notification_data=notification)
