import csv
import io
import json


from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

async def get_quiz_json(query,
                        db: AsyncSession,
                        redis: Redis):
    result = await db.execute(query)
    result = result.scalars().all()
    file_content = io.StringIO()
    for quiz in result:
        quiz_json = await redis.get(f'Company {quiz.company_id} {quiz.user_id} {quiz.quiz_id} {quiz.id}')
        if quiz_json:
            quiz_result = json.loads(quiz_json)
            file_content.write(json.dumps(quiz_result, indent=4))
    file_content.seek(0)
    return file_content.getvalue()


async def get_quiz_csv(query,
                       db: AsyncSession,
                       redis: Redis):
    result = await db.execute(query)
    result = result.scalars().all()
    rows = []

    for quiz in result:
        quiz_json = await redis.get(f'Company {quiz.company_id} {quiz.user_id} {quiz.quiz_id} {quiz.id}')
        if quiz_json:
            quiz_result = json.loads(quiz_json)
            for i in range(1, quiz.questions_overall + 1):
                question_key = f"Question {i}"

                if question_key in quiz_result:
                    row = {
                        "user": quiz_result["user"],
                        "company": quiz_result["company"],
                        "quiz": quiz_result["quiz"],
                        "question": quiz_result[question_key]["question"],
                        "user_answer": quiz_result[question_key]["answer"],
                        "result": quiz_result[question_key]["result"]
                    }
                    rows.append(row)
    if rows:
        file_content = io.StringIO()
        fieldnames = ["user", "company", "quiz", "question", "user_answer", "result"]
        writer = csv.DictWriter(file_content, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        file_content.seek(0)
        return file_content.getvalue()
