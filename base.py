from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AIProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, api_key: str | None = None, model: str | None = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate_quiz(
        self,
        text_content: str,
        num_questions: int,
        question_type: str,
        difficulty: str,
        answer_length: str,
    ) -> List[Dict[str, Any]]:
        """Generates a quiz from the given text content."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the display name of the provider."""
        pass