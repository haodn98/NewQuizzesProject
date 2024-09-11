from datetime import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, Field


class Question(BaseModel):
    text: str
    answers: List[str] = Field(min_length=2)
    number: Optional[int] = None


class QuizModel(BaseModel):
    name: str
    description: str
    questions: List[Question] = Field(min_length=2)
    created_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    correct_answers: Dict[str, List[int]]


class AnswerForm(BaseModel):
    answers: Dict[int, int | List[int]] = Field(min_length=2)
