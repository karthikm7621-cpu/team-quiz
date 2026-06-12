from .base import AIProvider
from features.quiz_generator import generate_local_questions
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
        **kwargs # Other parameters are ignored by local provider
    ) -> List[Dict[str, Any]]:
        return generate_local_questions(text_content, num_questions, **kwargs)