import ollama
import json
from .base import AIProvider
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OllamaProvider(AIProvider):
    """Provider for running local inference with Ollama."""

    @property
    def name(self) -> str:
        return "Ollama (Local)"

    def __init__(self, model: str = "llama3", **kwargs):
        # Default to llama3 if no model is specified
        super().__init__(model=model, **kwargs)
        self.client = ollama.Client(host=self.config.get("host"))

    def generate_quiz(
        self,
        text_content: str,
        num_questions: int,
        question_type: str,
        difficulty: str,
        answer_length: str,
    ) -> List[Dict[str, Any]]:
        
        # This prompt is a simplified version. For better results, it should be
        # tailored to the specific model (e.g., using its chat template).
        prompt = f"""
        Based on the following text, generate a quiz with {num_questions} questions.
        The quiz should be in JSON format, as an object with a single key "quiz" which is a list of questions.
        Each question object must have: "question", "type", "answer".
        For "MCQ" type, also include "options" (a list of 4 strings) and "correct_index" (an integer).
        
        Difficulty: {difficulty}
        Question Type Focus: {question_type}
        Answer Length: {answer_length}
        
        Text:
        {text_content[:4000]}
        """

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                format="json" # Use Ollama's JSON mode
            )
            
            response_text = response.get("response", "{}")
            data = json.loads(response_text)
            return data.get("quiz", [])

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            # You could check if the model exists or if the server is running
            raise RuntimeError(f"Failed to generate quiz with Ollama. Is the server running and model '{self.model}' pulled?") from e