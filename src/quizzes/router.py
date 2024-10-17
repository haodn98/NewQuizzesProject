import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.params import Depends
from fastapi_cache.decorator import cache
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from companies.permissions import is_company_admin, is_company_member
from core.mongo_config import get_mongo_database
from core.redis_config import get_redis
from database.database import get_db_session
from quizzes.permissions import is_company_quiz
from quizzes.schemas import QuizModel, AnswerForm
from quizzes.services import (get_all_quizzes_service,
                              create_quizzes_service,
                              get_quiz_service,
                              get_quiz_answers_service,
                              get_company_quizzes_service,
                              send_quiz_solution_service,
                              update_quizzes_service,
                              delete_quizzes_service,
                              average_mark_service,
                              get_user_quizzes_json_services,
                              get_company_quizzes_results_json_services,
                              get_company_user_quizzes_results_json_services,
                              get_quizzes_results_json_services,
                              get_user_quizzes_csv_services,
                              get_company_quizzes_results_csv_services,
                              get_company_user_quizzes_results_csv_services,
                              get_quizzes_results_csv_services,
                              get_user_quiz_result_service,
                              get_quiz_results_service)
from utils.utils_auth import get_current_user

router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
)


# tested
@router.get("/average_mark")
@cache(expire=30)
async def average_mark(company_id: Optional[int] = None,
                       max_day: Optional[datetime] = datetime.now(),
                       user: dict = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db_session)):
    try:
        mark = await average_mark_service(user=user, db=db, company_id=company_id, max_day=max_day)
        return {
            "average_mark": mark
        }
    except ZeroDivisionError:
        raise HTTPException(status_code=404, detail="No quiz results for this period of time")


# tested
@router.get("/user_results/{user_id}")
@cache(expire=30)
async def get_user_results(
        user_id: int,
        user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)):
    return await get_user_quiz_result_service(user_id=user_id, db=db)


@router.get("/user_quizzes_results_json")
async def get_user_quizzes_json(user: dict = Depends(get_current_user),
                                db: AsyncSession = Depends(get_db_session),
                                redis: Redis = Depends(get_redis)):
    file_content = await get_user_quizzes_json_services(user=user, db=db, redis=redis)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/json",
                             headers={"Content-Disposition": "attachment; filename=user_quizzes.json"})


@router.get("/admin/{company_id}/results_json")
async def get_company_quizzes_json(company_id: int,
                                   company: bool = Depends(is_company_admin),
                                   user: dict = Depends(get_current_user),
                                   db: AsyncIOMotorDatabase = Depends(get_db_session),
                                   redis: Redis = Depends(get_redis)):
    file_content = await get_company_quizzes_results_json_services(company_id=company_id, db=db, redis=redis)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/json",
                             headers={"Content-Disposition": "attachment; filename=company_quizzes_results.json"})


@router.get("/admin/{company_id}/{user_id}/user_quizzes_json")
async def get_company_user_quizzes_json(company_id: int,
                                        user_id: int,
                                        company_user: bool = Depends(is_company_member),
                                        company: bool = Depends(is_company_admin),
                                        user: dict = Depends(get_current_user),
                                        db: AsyncIOMotorDatabase = Depends(get_db_session),
                                        redis: Redis = Depends(get_redis)):
    file_content = await get_company_user_quizzes_results_json_services(company_id=company_id,
                                                                        user_id=user_id,
                                                                        redis=redis,
                                                                        db=db)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/json",
                             headers={"Content-Disposition": "attachment; filename=company_user_quizzes_results.json"})


@router.get("/admin/{company_id}/{quiz_id}/quiz_results_json")
async def get_quiz_results_json(company_id: int,
                                quiz_id: str,
                                company: bool = Depends(is_company_admin),
                                quiz: bool = Depends(is_company_quiz),
                                user: dict = Depends(get_current_user),
                                db: AsyncIOMotorDatabase = Depends(get_db_session),
                                redis: Redis = Depends(get_redis)):
    file_content = await get_quizzes_results_json_services(quiz_id=quiz_id,
                                                           redis=redis,
                                                           db=db)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/json",
                             headers={"Content-Disposition": "attachment; filename=company_quiz_results.json"})


@router.get("/user_quizzes_results_csv")
async def get_user_quizzes_csv(user: dict = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db_session),
                               redis: Redis = Depends(get_redis)):
    file_content = await get_user_quizzes_csv_services(user=user,
                                                       db=db,
                                                       redis=redis)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/csv",
                             headers={"Content-Disposition": "attachment; filename=user_quizzes.csv"})


@router.get("/admin/{company_id}/results_csv")
async def get_company_quizzes_csv(company_id: int,
                                  company: bool = Depends(is_company_admin),
                                  user: dict = Depends(get_current_user),
                                  db: AsyncIOMotorDatabase = Depends(get_db_session),
                                  redis: Redis = Depends(get_redis)):
    file_content = await get_company_quizzes_results_csv_services(company_id=company_id,
                                                                  db=db,
                                                                  redis=redis)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/csv",
                             headers={"Content-Disposition": "attachment; filename=company_quizzes_results.csv"})


@router.get("/admin/{company_id}/{user_id}/user_quizzes_csv")
async def get_company_user_quizzes_csv(company_id: int,
                                       user_id: int,
                                       company_user: bool = Depends(is_company_member),
                                       company: bool = Depends(is_company_admin),
                                       user: dict = Depends(get_current_user),
                                       db: AsyncIOMotorDatabase = Depends(get_db_session),
                                       redis: Redis = Depends(get_redis)):
    file_content = await get_company_user_quizzes_results_csv_services(company_id=company_id,
                                                                       user_id=user_id,
                                                                       redis=redis,
                                                                       db=db)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/csv",
                             headers={"Content-Disposition": "attachment; filename=company_user_quizzes_results.csv"})


@router.get("/admin/{company_id}/{quiz_id}/quiz_results_csv")
async def get_quiz_results_csv(company_id: int,
                               quiz_id: str,
                               company: bool = Depends(is_company_admin),
                               quiz: bool = Depends(is_company_quiz),
                               user: dict = Depends(get_current_user),
                               db: AsyncIOMotorDatabase = Depends(get_db_session),
                               redis: Redis = Depends(get_redis)):
    file_content = await get_quizzes_results_csv_services(quiz_id=quiz_id,
                                                          redis=redis,
                                                          db=db)
    return StreamingResponse(io.BytesIO(file_content.encode('utf-8')), media_type="application/csv",
                             headers={"Content-Disposition": "attachment; filename=company_quiz_results.csv"})


# tested
@router.get("/")
@cache(expire=30)
async def get_all_quizzes(page: Optional[int] = 1, per_page: Optional[int] = 10,
                          user: dict = Depends(get_current_user),
                          db: AsyncIOMotorDatabase = Depends(get_mongo_database)):
    """
    Endpoint to retrieve all quizzes.

    Args:
        user (dict): The current authenticated user, retrieved from the token.
        db (AsyncIOMotorDatabase): MongoDB database instance.

    Returns:
        A list of all available quizzes.
        """
    return await get_all_quizzes_service(page=page,
                                         per_page=per_page,
                                         db=db)


# tested
@router.get("/{company_id}")
@cache(expire=30)
async def get_company_quizzes(company_id: int,
                              user: dict = Depends(get_current_user),
                              db: AsyncIOMotorDatabase = Depends(get_mongo_database)):
    return await get_company_quizzes_service(company_id=company_id, db=db)


# tested
@router.post("/{company_id}", status_code=status.HTTP_201_CREATED)
async def create_quiz(
        company_id: int,
        quiz_data: QuizModel,
        user: dict = Depends(get_current_user),
        company: bool = Depends(is_company_admin),
        db_mongo: AsyncIOMotorDatabase = Depends(get_mongo_database),
        db_postgres: AsyncSession = Depends(get_db_session)):
    """
    Endpoint to create a new quiz.

    Args:
        company_id (int): The ID of the company that owns the quiz.
        quiz_data (QuizModel): The quiz data in Pydantic model form.
        user (dict): The current authenticated user.
        company: Check if the user is an admin of the company.
        db_mongo (AsyncIOMotorDatabase): MongoDB database instance.

    Returns:
        The created quiz data.
    """
    return await create_quizzes_service(user=user, company_id=company_id, quiz_data=quiz_data, db_mongo=db_mongo,
                                        db_postgres=db_postgres)


# tested
@router.put("/{company_id}/{quiz_id}")
async def update_quizz(
        company_id: int,
        quiz_id: str,
        quiz_data: QuizModel,
        user: dict = Depends(get_current_user),
        company: bool = Depends(is_company_admin),
        db: AsyncIOMotorDatabase = Depends(get_mongo_database)):
    """
    Endpoint to update a quiz.

    Args:
        company_id (int): The ID of the company that owns the quiz.
        quiz_id (int): The ID of the quiz.
        quiz_data (QuizModel): The quiz data in Pydantic model form.
        user (dict): The current authenticated user.
        company: Check if the user is an admin of the company.
        db (AsyncIOMotorDatabase): MongoDB database instance.

    Returns:
        The updated quiz data.
    """
    return await update_quizzes_service(quiz_id=quiz_id, quiz_data=quiz_data, db=db)


# tested
@router.get("/{company_id}/{quiz_id}")
@cache(expire=30)
async def get_quiz(quiz_id: str,
                   company_id: int,
                   user: dict = Depends(get_current_user),
                   db: AsyncIOMotorDatabase = Depends(get_mongo_database)):
    """
        Endpoint to retrieve a specific quiz without answers.

        Args:
            quiz_id (str): The ID of the quiz to retrieve.
            company_id (int): The ID of the company the quiz belongs to.
            user (dict): The current authenticated user.
            db (AsyncIOMotorDatabase): MongoDB database instance.

        Returns:
            The quiz data without answers.
        """
    return await get_quiz_service(quiz_id=quiz_id, company_id=company_id, db=db)


# tested
@router.delete("/{company_id}/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
        company_id: int,
        quiz_id: str,
        user: dict = Depends(get_current_user),
        company: bool = Depends(is_company_admin),
        quiz: bool = Depends(is_company_quiz),
        db_mongo: AsyncIOMotorDatabase = Depends(get_mongo_database),
        db_postgres: AsyncSession = Depends(get_db_session)):
    return await delete_quizzes_service(quiz_id=quiz_id, db_mongo=db_mongo)


# tested
@router.get("/{company_id}/{quiz_id}/results")
@cache(expire=30)
async def get_quiz_results(company_id: int,
                           quiz_id: str,
                           company: bool = Depends(is_company_admin),
                           quiz: bool = Depends(is_company_quiz),
                           db: AsyncSession = Depends(get_db_session)):
    return await get_quiz_results_service(quiz_id=quiz_id, db=db)


# tested
@router.get("/{company_id}/{quiz_id}/answers")
@cache(expire=30)
async def get_quiz_with_answers(quiz_id: str,
                                company_id: int,
                                user: dict = Depends(get_current_user),
                                company: bool = Depends(is_company_admin),
                                db: AsyncIOMotorDatabase = Depends(get_mongo_database)):
    """
        Endpoint to retrieve a specific quiz with answers.

        Args:
            quiz_id (str): The ID of the quiz to retrieve.
            company_id (int): The ID of the company the quiz belongs to.
            user (dict): The current authenticated user.
            company: Check if the user is an admin of the company.
            db (AsyncIOMotorDatabase): MongoDB database instance.

        Returns:
            The quiz data with answers.
        """
    return await get_quiz_answers_service(quiz_id=quiz_id, company_id=company_id, db=db)


# tested
@router.post("/{company_id}/{quiz_id}/solution", status_code=status.HTTP_201_CREATED)
async def send_quiz_solution(quiz_id: str,
                             company_id: int,
                             answers_form: AnswerForm,
                             user: dict = Depends(get_current_user),
                             company: bool = Depends(is_company_member),
                             db_mongo: AsyncIOMotorDatabase = Depends(get_mongo_database),
                             db_postgres: AsyncSession = Depends(get_db_session),
                             redis: Redis = Depends(get_redis)):
    return await send_quiz_solution_service(
        user=user,
        company_id=company_id,
        quiz_id=quiz_id,
        answers_form=answers_form,
        db_mongo=db_mongo,
        db_postgres=db_postgres,
        redis=redis
    )
