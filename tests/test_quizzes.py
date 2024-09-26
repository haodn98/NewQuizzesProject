import pytest
from httpx import AsyncClient
from fastapi import status
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import select, text

from src.core.config import settings
from src.notifications.models import Notification
from src.quizzes.manager import QuizManager, QuizNotFound
from src.quizzes.models import QuizResults
from .conftest import ac, async_session_test, test_engine


@pytest.fixture(scope="function")
async def test_quiz():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    db = db["test_quizzes"]
    quiz_test = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            },
            {
                "text": "What is the square root of 64?",
                "answers": [
                    "6",
                    "7",
                    "8",
                    "9"
                ],
                "number": 5
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [
                2
            ],
            "2": [
                1
            ],
            "3": [
                3
            ],
            "4": [
                2
            ],
            "5": [
                2
            ]
        },
        "company_id": 1,
        "created_by_user_id": 1,
        "frequency": 1
    }
    test_quiz = await QuizManager.create_quiz(db=db, quiz_data=quiz_test)
    yield test_quiz
    await QuizManager.delete_quiz(db=db, quiz_id=test_quiz["_id"])


@pytest.fixture(scope="function")
async def test_result_to_test_quiz(test_quiz, test_user, test_company_with_member):
    quiz_results = QuizResults(
        quiz_id=test_quiz["_id"],
        user_id=test_user.id,
        company_id=test_company_with_member.id,
        result=4,
        questions_overall=5
    )
    async with async_session_test() as db:
        db.add(quiz_results)
        await db.commit()
    yield quiz_results
    async with test_engine.begin() as connection:
        await connection.execute(text('DELETE FROM "quiz_result";'))
        await connection.commit()


async def test_get_all_quizzes(ac: AsyncClient,
                               test_user,
                               test_quiz):
    response = await ac.get("/quizzes/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["documents"]) == 1


async def test_get_all_quizzes_paginated(ac: AsyncClient,
                                         test_user,
                                         test_quiz):
    response = await ac.get("/quizzes/?page=1&per_page=10")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["documents"]) == 1

    response = await ac.get("/quizzes/?page=2&per_page=10")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["documents"]) == 0


async def test_get_quiz(ac: AsyncClient,
                        test_user,
                        test_quiz,
                        test_company_with_member
                        ):
    response = await ac.get("/quizzes/{}/{}".format(test_company_with_member.id, test_quiz["_id"]))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["_id"] == test_quiz["_id"]
    assert len(response.json()) == 8


async def test_get_quiz_wrong_id_format(ac: AsyncClient,
                                        test_company_with_member,
                                        test_company_roles):
    response = await ac.get("/quizzes/{}/{}".format(test_company_with_member.id, "1000"))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid quiz id"}


async def test_get_quiz_wrong_quiz_id(ac: AsyncClient,
                                      test_company_with_member,
                                      test_company_roles):
    response = await ac.get("/quizzes/{}/{}".format(test_company_with_member.id, "222222222222222222222222"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Quiz not found"}


async def test_get_quiz_wrong_company_id(ac: AsyncClient,
                                         test_quiz):
    response = await ac.get("/quizzes/{}/{}".format(500, test_quiz["_id"]))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Quiz not connected to company"}


async def test_get_quiz_with_answers(ac: AsyncClient,
                                     test_user,
                                     test_quiz,
                                     test_company_with_member,
                                     ):
    response = await ac.get("/quizzes/{}/{}/answers".format(test_company_with_member.id, test_quiz["_id"]))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["_id"] == test_quiz["_id"]
    assert len(response.json()) == 9


async def test_get_quiz_with_answers_wrong_id_format(ac: AsyncClient,
                                                     test_company_with_member,
                                                     ):
    response = await ac.get("/quizzes/{}/{}".format(test_company_with_member.id, "1000"))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid quiz id"}


async def test_get_quiz_with_answers_wrong_quiz_id(ac: AsyncClient,
                                                   test_company_with_member,
                                                   ):
    response = await ac.get("/quizzes/{}/{}".format(test_company_with_member.id, "222222222222222222222222"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Quiz not found"}


async def test_get_quiz_with_answers_wrong_company_id(ac: AsyncClient, test_quiz):
    response = await ac.get("/quizzes/{}/{}".format(500, test_quiz["_id"]))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Quiz not connected to company"}


async def test_get_company_quizzes(ac: AsyncClient, test_company_with_member, test_quiz):
    response = await ac.get(f"/quizzes/{test_company_with_member.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["_id"] == test_quiz["_id"]


async def test_update_quiz_(ac: AsyncClient, test_company_with_member, test_quiz):
    quiz_data = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [2],
            "2": [1],
            "3": [3],
            "4": [2]
        },
        "frequency": 1
    }

    response = await ac.put("/quizzes/{}/{}".format(test_company_with_member.id, test_quiz["_id"]),
                            json=quiz_data)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["questions"]) == 4


async def test_update_quiz_wrong_id_format(ac: AsyncClient, test_company_with_member):
    quiz_data = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [2],
            "2": [1],
            "3": [3],
            "4": [2]
        },
        "frequency": 1
    }

    response = await ac.put("/quizzes/{}/{}".format(test_company_with_member.id, "1000"),
                            json=quiz_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid quiz id"}


async def test_update_quiz_wrong_quiz_id(ac: AsyncClient, test_company_with_member):
    quiz_data = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [2],
            "2": [1],
            "3": [3],
            "4": [2]
        },
        "frequency": 1
    }
    response = await ac.put("/quizzes/{}/{}".format(test_company_with_member.id, "222222222222222222222222"),
                            json=quiz_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Quiz not found"}


async def test_update_quiz_wrong_company_id(ac: AsyncClient, test_quiz):
    quiz_data = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [2],
            "2": [1],
            "3": [3],
            "4": [2]
        },
        "frequency": 1
    }
    response = await ac.put("/quizzes/{}/{}".format(500, test_quiz["_id"]),
                            json=quiz_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_quiz(ac: AsyncClient, test_company_with_member, test_quiz):
    quiz_data = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [2],
            "2": [1],
            "3": [3],
            "4": [2]
        },
        "frequency": 1
    }
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    db = db["test_quizzes"]

    response = await ac.post(f"/quizzes/{test_company_with_member.id}", json=quiz_data)
    quizzes = await QuizManager.get_all_quizzes(db=db)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(quizzes) == 2


async def test_create_quiz_wrong_company_id(ac: AsyncClient, test_company_with_member, test_quiz):
    quiz_data = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [2],
            "2": [1],
            "3": [3],
            "4": [2]
        },
        "frequency": 1
    }

    response = await ac.post(f"/quizzes/555555", json=quiz_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Company does not exist"}


async def test_get_quiz_results(ac: AsyncClient, test_user, test_quiz, test_result_to_test_quiz,
                                test_company_with_member):
    response = await ac.get("/quizzes/{}/{}/results".format(test_company_with_member.id, test_quiz["_id"]))

    assert response.status_code == status.HTTP_200_OK


async def test_get_quiz_results_wrong_id(ac: AsyncClient, test_quiz, test_result_to_test_quiz,
                                         test_company_with_member):
    response = await ac.get("/quizzes/{}/{}/results".format(test_company_with_member.id, 5000))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_send_quiz_answer(ac: AsyncClient,
                                test_user,
                                test_quiz,
                                test_result_to_test_quiz,
                                test_company_with_member):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2],
            "5": [1],
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)

    async with async_session_test() as db:
        results = await db.execute(select(QuizResults).where(QuizResults.quiz_id == test_quiz["_id"],
                                                             QuizResults.user_id == test_user.id))
        results = results.scalars().all()

        notification = await db.execute(
            select(Notification).where(Notification.company_id == test_company_with_member.id,
                                       Notification.user_id == test_user.id))
        notification = notification.scalars().all()

        assert response.status_code == status.HTTP_201_CREATED
        assert len(results) == 2
        assert len(notification) == 1

        for i in notification:
            await db.delete(i)
        await db.commit()


async def test_send_quiz_answer_wrong_answers_num(ac: AsyncClient,
                                                  test_user,
                                                  test_quiz,
                                                  test_result_to_test_quiz,
                                                  test_company_with_member):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2]
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Incorrect number of answers'}


async def test_send_quiz_answer_wrong_quiz_id(ac: AsyncClient,
                                              test_user,
                                              test_quiz,
                                              test_result_to_test_quiz,
                                              test_company_with_member):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2]
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, "222222222222222222222222"),
        json=answer_form)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Quiz not found'}


async def test_send_quiz_answer_invalid_quiz_id(ac: AsyncClient,
                                                test_user,
                                                test_quiz,
                                                test_result_to_test_quiz,
                                                test_company_with_member):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2]
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, "2222"),
        json=answer_form)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid quiz id"}


async def test_delete_quiz(ac: AsyncClient,
                           test_user,
                           test_result_to_test_quiz,
                           test_company_with_member):
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.MONGO_DB]
    db = db["test_quizzes"]
    quiz_test = {
        "name": "General Knowledge Quiz",
        "description": "A quiz to test your general knowledge skills",
        "questions": [
            {
                "text": "What is the capital of France?",
                "answers": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "number": 1
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "answers": [
                    "Earth",
                    "Mars",
                    "Jupiter",
                    "Venus"
                ],
                "number": 2
            },
            {
                "text": "What is the largest ocean on Earth?",
                "answers": [
                    "Atlantic",
                    "Indian",
                    "Arctic",
                    "Pacific"
                ],
                "number": 3
            },
            {
                "text": "Who wrote 'Romeo and Juliet'?",
                "answers": [
                    "Charles Dickens",
                    "Mark Twain",
                    "William Shakespeare",
                    "Leo Tolstoy"
                ],
                "number": 4
            },
            {
                "text": "What is the square root of 64?",
                "answers": [
                    "6",
                    "7",
                    "8",
                    "9"
                ],
                "number": 5
            }
        ],
        "created_at": "2024-09-24",
        "correct_answers": {
            "1": [
                2
            ],
            "2": [
                1
            ],
            "3": [
                3
            ],
            "4": [
                2
            ],
            "5": [
                2
            ]
        },
        "company_id": test_company_with_member.id,
        "created_by_user_id": test_user.id,
        "frequency": 1
    }
    quiz_to_delete = await QuizManager.create_quiz(db, quiz_test)
    response = await ac.delete("/quizzes/{}/{}".format(test_company_with_member.id, quiz_to_delete["_id"]))

    try:
        quiz = await QuizManager.get_quiz(db, quiz_to_delete["_id"])
    except QuizNotFound:
        quiz = None

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert quiz is None


async def test_delete_quiz_wrong_id(ac: AsyncClient,
                                    test_user,
                                    test_quiz,
                                    test_result_to_test_quiz,
                                    test_company_with_member):
    response = await ac.delete("/quizzes/{}/{}".format(test_company_with_member.id, "222222222222222222222222"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Quiz not found"}


async def test_delete_quiz_invalid_id(ac: AsyncClient,
                                      test_user,
                                      test_quiz,
                                      test_result_to_test_quiz,
                                      test_company_with_member):
    response = await ac.delete("/quizzes/{}/{}".format(test_company_with_member.id, "2222"))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_delete_quiz_wrong_company_id(ac: AsyncClient,
                                            test_user,
                                            test_quiz,
                                            test_result_to_test_quiz,
                                            test_company_with_member):
    response = await ac.delete("/quizzes/{}/{}".format(10000, test_quiz["_id"]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_user_average_mark(ac: AsyncClient,
                                     test_user,
                                     test_result_to_test_quiz,
                                     test_company_with_member):
    response = await ac.get("/quizzes/average_mark")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"average_mark": 0.8}


async def test_get_user_average_with_date_without_quizzes(ac: AsyncClient,
                                                          test_user,
                                                          test_result_to_test_quiz,
                                                          test_company_with_member):
    response = await ac.get("/quizzes/average_mark?max_day=2023-09-29")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No quiz results for this period of time or with this company"}


async def test_get_user_average_with_wrong_company(ac: AsyncClient,
                                                   test_user,
                                                   test_result_to_test_quiz,
                                                   test_company_with_member):
    response = await ac.get("/quizzes/average_mark?max_day=2023-09-29&company_id=10")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No quiz results for this period of time or with this company"}


async def test_users_results(ac: AsyncClient,
                             test_user,
                             test_result_to_test_quiz):
    response = await ac.get(f"/quizzes/user_results/{test_user.id}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


async def test_get_user_quizzes_json(ac: AsyncClient, test_user, test_company_with_member, test_result_to_test_quiz):
    response = await ac.get("/quizzes/user_quizzes_results_json")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=user_quizzes.json'
    assert response.headers["content-type"] == "application/json"


async def test_get_company_quizzes_json(ac: AsyncClient, test_user, test_company_with_member, test_result_to_test_quiz):
    response = await ac.get(f"/quizzes/admin/{test_company_with_member.id}/results_json")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=company_quizzes_results.json'
    assert response.headers["content-type"] == "application/json"


async def test_get_company_quizzes_json_wrong_company_id(ac: AsyncClient, test_user):
    response = await ac.get("/quizzes/admin/1000/results_json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company does not exist"


async def test_get_company_user_quizzes_json(ac: AsyncClient, test_quiz, test_user, test_company_with_member,
                                             test_result_to_test_quiz):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2],
            "5": [1],
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)

    response = await ac.get(f"/quizzes/admin/{test_company_with_member.id}/{test_user.id}/user_quizzes_json")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=company_user_quizzes_results.json'
    assert response.headers["content-type"] == "application/json"


async def test_get_company_user_quizzes_json_wrong_company_id(ac: AsyncClient, test_user):
    response = await ac.get(f"/quizzes/admin/1000/{test_user.id}/user_quizzes_json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company does not exist"


async def test_get_company_quiz_result_json(ac: AsyncClient,
                                            test_quiz,
                                            test_user,
                                            test_company_with_member,
                                            test_result_to_test_quiz):
    response = await ac.get(
        "/quizzes/admin/{}/{}/quiz_results_json".format(test_company_with_member.id, test_quiz["_id"]))

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=company_quiz_results.json'
    assert response.headers["content-type"] == "application/json"


async def test_get_company_quiz_result_json_wrong_company_id(ac: AsyncClient,
                                                             test_quiz,
                                                             test_user,
                                                             test_company_with_member):
    response = await ac.get("/quizzes/admin/{}/{}/quiz_results_json".format(1000, test_quiz["_id"]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company does not exist"


async def test_get_company_quiz_result_json_invalid_quiz_id(ac: AsyncClient,
                                                            test_quiz,
                                                            test_user,
                                                            test_company_with_member):
    response = await ac.get("/quizzes/admin/{}/{}/quiz_results_json".format(test_company_with_member.id, 55555))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid Quiz id"


async def test_get_company_quiz_result_json_wrong_quiz_id(ac: AsyncClient,
                                                          test_quiz,
                                                          test_user,
                                                          test_company_with_member):
    response = await ac.get(
        "/quizzes/admin/{}/{}/quiz_results_json".format(test_company_with_member.id, "222222222222222222222222"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Quiz not found"


async def test_get_user_quizzes_csv(ac: AsyncClient, test_quiz, test_user, test_company_with_member,
                                    test_result_to_test_quiz):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2],
            "5": [1],
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)
    response = await ac.get("/quizzes/user_quizzes_results_csv")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=user_quizzes.csv'
    assert response.headers["content-type"] == "application/csv"


async def test_get_company_quizzes_csv(ac: AsyncClient, test_quiz, test_user, test_company_with_member,
                                       test_result_to_test_quiz):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2],
            "5": [1],
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)
    response = await ac.get(f"/quizzes/admin/{test_company_with_member.id}/results_csv")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=company_quizzes_results.csv'
    assert response.headers["content-type"] == "application/csv"


async def test_get_company_quizzes_csv_wrong_company_id(ac: AsyncClient, test_quiz, test_user, test_company_with_member,
                                                        test_result_to_test_quiz):
    response = await ac.get("/quizzes/admin/1000/results_csv")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company does not exist"


async def test_get_company_user_quizzes_csv(ac: AsyncClient, test_quiz, test_user, test_company_with_member,
                                            test_result_to_test_quiz):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2],
            "5": [1],
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)
    response = await ac.get(f"/quizzes/admin/{test_company_with_member.id}/{test_user.id}/user_quizzes_csv")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=company_user_quizzes_results.csv'
    assert response.headers["content-type"] == "application/csv"


async def test_get_company_user_quizzes_csv_wrong_company_id(ac: AsyncClient, test_quiz, test_user,
                                                             test_company_with_member, test_result_to_test_quiz):
    response = await ac.get(f"/quizzes/admin/5000/{test_user.id}/user_quizzes_csv")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Company does not exist"


async def test_get_quiz_result_csv(ac: AsyncClient, test_user, test_company_with_member, test_quiz,
                                   test_result_to_test_quiz):
    answer_form = {
        "answers": {
            "1": [1],
            "2": [2],
            "3": [3],
            "4": [2],
            "5": [1],
        }
    }
    response = await ac.post(
        "/quizzes/{}/{}/solution".format(test_company_with_member.id, test_quiz["_id"]),
        json=answer_form)
    response = await ac.get(
        "/quizzes/admin/{}/{}/quiz_results_csv".format(test_company_with_member.id, test_quiz["_id"]))

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Disposition"] == 'attachment; filename=company_quiz_results.csv'
    assert response.headers["content-type"] == "application/csv"


async def test_get_company_quiz_result_csv_wrong_company_id(ac: AsyncClient,
                                                            test_quiz,
                                                            test_user,
                                                            test_company_with_member):
    response = await ac.get("/quizzes/admin/{}/{}/quiz_results_csv".format(5000, test_quiz["_id"]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == 'Company does not exist'


async def test_get_company_quiz_result_csv_invalid_quiz_id(ac: AsyncClient,
                                                           test_quiz,
                                                           test_user,
                                                           test_company_with_member):
    response = await ac.get("/quizzes/admin/{}/{}/quiz_results_csv".format(test_company_with_member.id, 55555))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid Quiz id"


async def test_get_company_quiz_result_csv_wrong_quiz_id(ac: AsyncClient,
                                                         test_quiz,
                                                         test_user,
                                                         test_company_with_member):
    response = await ac.get(
        "/quizzes/admin/{}/{}/quiz_results_csv".format(test_company_with_member.id, "222222222222222222222222"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == 'Quiz not found'
