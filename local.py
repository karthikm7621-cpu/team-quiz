from base import AIProvider
from quiz_generator import generate_quiz as generate_local_questions
from typing import List, Dict, Any


class LocalProvider(AIProvider):
    """Provider for generating quizzes offline using local heuristics."""

    @property
    def name(self) -> str:
        return "Local"

    def generate_quiz(
        self,
        text_content: str,
        num_questions: int,
        question_type: str = "MCQ",
        difficulty: str = "Basic",
        answer_length: str = "1-line",
    ) -> List[Dict[str, Any]]:
        return generate_local_questions(
            text_content,
            num_questions,
            question_type=question_type,
            difficulty=difficulty,
            answer_length=answer_length,
        )
