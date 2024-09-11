from fastapi import HTTPException
from sqlalchemy import select

from src.quizzes.manager import QuizManager
from src.quizzes.models import QuizResults


async def get_all_quizzes_service(page,per_page,db):
    """
    Retrieves all available quizzes from the database.

    Args:
        db: The database object.

    Returns:
        A list of all quizzes retrieved from the database.
    """
    return await QuizManager.get_all_quizzes_paginated(collection = db,query={},page=page,per_page=per_page)


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
    quiz_to_delete_mongo = await QuizManager.delete_quiz(db_mongo,quiz_id)

    return quiz_to_delete_mongo

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
    quiz = await QuizManager.get_quiz_no_answers(db, quiz_id)
    if quiz is None:
        return HTTPException(status_code=404, detail="Quiz not found")
    if quiz.get("company_id") != company_id:
        return HTTPException(status_code=403, detail="Quiz not connected to company")
    return quiz


async def send_quiz_solution_service(user, company_id, quiz_id, answers_form, db_mongo, db_postgres):
    quiz = await QuizManager.get_quiz(db=db_mongo, quiz_id=quiz_id)
    if quiz.get("company_id") != company_id:
        return HTTPException(status_code=400, detail="Quiz not connected to company")

    quiz_answers = quiz["correct_answers"]
    answers_form = answers_form.dict()
    users_answers = answers_form.get("answers")
    results = {}
    max_mark = sum([len(value) for value in answers_form.get("answers").values()])
    result = 0

    if len(quiz["correct_answers"]) != len(answers_form.get("answers")):
        raise HTTPException(status_code=400, detail="Incorrect number of answers")

    for number, answer in users_answers.items():
        if set(quiz_answers[str(number)]) == set(answer):
            results["result " + str(number)] = "right"
            result += 1
        else:
            results["result " + str(number)] = "wrong"
    user_result = QuizResults(
        user_id=user.get("id"),
        quiz_id=quiz_id,
        company_id=company_id,
        result=result / max_mark * 100,
    )
    db_postgres.add(user_result)
    await db_postgres.commit()
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
    quiz = await QuizManager.get_quiz(db, quiz_id)
    if quiz is None:
        return HTTPException(status_code=404, detail="Quiz not found")
    if quiz.get("company_id") != company_id:
        return HTTPException(status_code=403, detail="Quiz not connected to company")
    return quiz
