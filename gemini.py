from base import AIProvider
from quiz_generator import generate_ai_quiz
from typing import List, Dict, Any

class GeminiProvider(AIProvider):
    """Provider for Google Gemini."""

    @property
    def name(self) -> str:
        return "Gemini"

    def generate_quiz(
        self,
        text_content: str,
        num_questions: int,
        question_type: str,
        difficulty: str,
        answer_length: str,
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("Gemini API key is required.")
        
        return generate_ai_quiz(
            text_content, num_questions, question_type, difficulty, answer_length, self.api_key
        )