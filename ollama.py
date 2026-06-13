import ollama
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OllamaProvider:
    """Provider for running local inference with Ollama."""

    def __init__(self, model: str = "llama3", **kwargs):
        self.model = model
        self.config = kwargs
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
            
            response_text = response.get("response", "")
            if not response_text.strip():
                raise ValueError("Received empty response from Ollama model.")

            data = json.loads(response_text)

            if not isinstance(data, dict) or "quiz" not in data or not isinstance(data["quiz"], list):
                raise ValueError("Ollama response must be a JSON object with a 'quiz' array.")

            questions = [
                item for item in data.get("quiz", []) 
                if isinstance(item, dict) and "question" in item and "answer" in item
            ]
            
            if not questions:
                raise ValueError("No valid questions found in Ollama response.")

            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Ollama generation failed - invalid JSON: {e}")
            raise RuntimeError("Failed to parse JSON from Ollama. The model may not be following instructions.") from e
        except ollama.ResponseError as e:
            logger.error(f"Ollama API error: {e.error}")
            if "model not found" in e.error:
                raise RuntimeError(f"Ollama model '{self.model}' not found. Please pull it with `ollama pull {self.model}`.") from e
            raise RuntimeError(f"An error occurred with the Ollama API: {e.error}") from e
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Failed to generate quiz with Ollama. Is the server running and reachable at {self.config.get('host')}?") from e