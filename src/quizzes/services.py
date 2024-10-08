import json

from fastapi import HTTPException, status
from sqlalchemy import select

from src.core.redis_config import get_redis, redis
from src.quizzes.manager import QuizManager, QuizNotFound
from src.quizzes.models import QuizResults
from src.utils.utils_quizzes import get_quiz_json, get_quiz_csv


async def get_all_quizzes_service(page, per_page, db):
    """
    Retrieves all available quizzes from the database.

    Args:
        db: The database object.

    Returns:
        A list of all quizzes retrieved from the database.
    """
    return await QuizManager.get_all_quizzes_paginated(collection=db, query={}, page=page, per_page=per_page)


async def get_company_quizzes_service(company_id, db):
    """
        Retrieves all quiz IDs for the specified company.

        Args:
            company_id (int): The ID of the company.
            db: The database object.

        Returns:
            A list of quiz IDs belonging to the specified company.
        """
    quizzes = await QuizManager.quiz_filter(db,
                                            {"company_id": company_id},
                                            {"projection": {"_id": 1, "name": 1}}
                                            )
    return quizzes


async def create_quizzes_service(user, company_id, quiz_data, db):
    """
    Creates a new quiz with the provided data.

    Args:
        user: The information of the user creating the quiz (includes the user ID).
        company_id: The ID of the company the quiz belongs to.
        quiz_data: The data of the quiz as a Pydantic model.
        db: The database object.

    Returns:
        The created quiz data after insertion into the database.
    """
    quiz_data = quiz_data.dict()
    quiz_data["company_id"] = company_id
    quiz_data["created_by_user_id"] = user.get("id")
    for index, question in enumerate(quiz_data["questions"]):
        question["number"] = index + 1
    return await QuizManager.create_quiz(db, quiz_data)


async def update_quizzes_service(quiz_id, quiz_data, db):
    """
    Update a quiz with the provided data.

    Args:
        quiz_id: The ID of the quiz
        quiz_data: The data of the quiz as a Pydantic model.
        db: The database object.

    Returns:
        The updated quiz data after insertion into the database.
    """
    quiz_data = quiz_data.dict()
    for index, question in enumerate(quiz_data["questions"]):
        if not question["number"]:
            question["number"] = index + 1
    document = await QuizManager.update_quiz(quiz_id=quiz_id, update_data=quiz_data, db=db)
    return document


async def delete_quizzes_service(quiz_id, db_mongo):
    deleted_quiz = await QuizManager.delete_quiz(db_mongo, quiz_id)
    if not deleted_quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    return {"detail": "Quiz deleted successfully"}


async def get_quiz_service(quiz_id, company_id, db):
    """
       Retrieves a specific quiz from the database, excluding answers.

       Args:
           quiz_id: The ID of the quiz to be retrieved.
           company_id: The ID of the company the quiz should be associated with.
           db: The database object.

       Returns:
           The quiz data without answers if found and valid for the company.

       Raises:
           HTTPException: If the quiz is not found (404) or the company doesn't match (403).
       """
    try:
        quiz = await QuizManager.get_quiz_no_answers(db, quiz_id)
        if quiz.get("company_id") != company_id:
            raise HTTPException(status_code=403, detail="Quiz not connected to company")
        return quiz
    except QuizNotFound:
        raise HTTPException(status_code=404, detail="Quiz not found")


async def send_quiz_solution_service(user, company_id, quiz_id, answers_form, db_mongo, db_postgres, redis):
    quiz = await QuizManager.get_quiz(db=db_mongo, quiz_id=quiz_id)
    if quiz.get("company_id") != company_id:
        raise HTTPException(status_code=400, detail="Quiz not connected to company")

    quiz_questions = quiz["questions"]
    quiz_answers = quiz["correct_answers"]
    answers_form = answers_form.dict()
    users_answers = answers_form.get("answers")
    results = {"user": user.get("id"),
               "company": company_id,
               "quiz": quiz_id, }
    result = 0

    if len(quiz["correct_answers"]) != len(answers_form.get("answers")):
        raise HTTPException(status_code=400, detail="Incorrect number of answers")

    for number, answer in users_answers.items():
        if set(quiz_answers[str(number)]) == set(answer):
            results[f"Question {str(number)}"] = {
                "question": str([question for question in quiz_questions if question["number"] == number]),
                "answer": answer,
                "result": "right"

            }
            results["result " + str(number)] = "right"
            result += 1
        else:
            results[f"Question {str(number)}"] = {
                "question": str([question for question in quiz_questions if question["number"] == number]),
                "answer": answer,
                "result": "wrong",
            }
    user_result = QuizResults(
        user_id=user.get("id"),
        quiz_id=quiz_id,
        company_id=company_id,
        result=result,
        questions_overall=len(quiz_questions)
    )
    db_postgres.add(user_result)
    await db_postgres.commit()
    await db_postgres.refresh(user_result)
    redis = await get_redis()
    await redis.set(
        f'Company {company_id} {user.get("id")} {quiz_id} {user_result.id}', json.dumps(results), ex=172800)
    return user_result


async def get_quiz_answers_service(quiz_id, company_id, db):
    """
        Retrieves a specific quiz from the database, including answers.

        Args:
            quiz_id: The ID of the quiz to be retrieved.
            company_id: The ID of the company the quiz should be associated with.
            db: The database object.

        Returns:
            The quiz data with answers if found and valid for the company.

        Raises:
            HTTPException: If the quiz is not found (404) or the company doesn't match (403).
        """
    try:
        quiz = await QuizManager.get_quiz(db, quiz_id)
        if quiz.get("company_id") != company_id:
            raise HTTPException(status_code=403, detail="Quiz not connected to company")
        return quiz
    except QuizNotFound:
        raise HTTPException(status_code=404, detail="Quiz not found")


async def average_mark_service(user, db, company_id=None):
    total_marks = 0
    total_questions = 0
    if company_id is None:
        quizzes_results = await db.execute(select(QuizResults).where(QuizResults.user_id == user.get("id")))
        quizzes_results = quizzes_results.scalars().all()
    else:
        quizzes_results = await db.execute(select(QuizResults).where(QuizResults.user_id == user.get("id"),
                                                                     QuizResults.company_id == company_id))
        quizzes_results = quizzes_results.scalars().all()
    for quiz_result in quizzes_results:
        total_marks += quiz_result.result
        total_questions += quiz_result.questions_overall
    return total_marks / total_questions


async def get_user_quizzes_json_services(user, db, redis):
    query = select(QuizResults).where(QuizResults.user_id == user.get("id"))
    return await get_quiz_json(query=query, db=db, redis=redis)


async def get_company_quizzes_results_json_services(company_id, db, redis):
    query = select(QuizResults).where(QuizResults.company_id == company_id)
    return await get_quiz_json(query=query, db=db, redis=redis)


async def get_company_user_quizzes_results_json_services(company_id, user_id, redis, db):
    query = select(QuizResults).where(QuizResults.company_id == company_id,
                                      QuizResults.user_id == user_id)
    return await get_quiz_json(query=query, db=db, redis=redis)


async def get_quizzes_results_json_services(quiz_id, db, redis):
    query = select(QuizResults).where(QuizResults.quiz_id == quiz_id)
    return await get_quiz_json(query=query, db=db, redis=redis)

async def get_user_quizzes_csv_services(user, db, redis):
    query = select(QuizResults).where(QuizResults.user_id == user.get("id"))
    return await get_quiz_csv(query=query, db=db, redis=redis)

async def get_company_quizzes_results_csv_services(company_id, db, redis):
    query = select(QuizResults).where(QuizResults.company_id == company_id)
    return await get_quiz_csv(query=query, db=db, redis=redis)

async def get_company_user_quizzes_results_csv_services(company_id, user_id, redis, db):
    query = select(QuizResults).where(QuizResults.company_id == company_id,
                                      QuizResults.user_id == user_id)
    return await get_quiz_json(query=query, db=db, redis=redis)

async def get_quizzes_results_csv_services(quiz_id, db, redis):
    query = select(QuizResults).where(QuizResults.quiz_id == quiz_id)
    return await get_quiz_json(query=query, db=db, redis=redis)