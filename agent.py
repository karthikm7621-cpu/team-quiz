import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from quiz_generator import (
    ALLOWED_QUESTION_TYPES,
    ANSWER_LENGTHS,
    DIFFICULTY_LEVELS,
    generate_quiz,
)

APP_NAME = "team_quiz_adk"
DEFAULT_USER_ID = "anonymous"

load_dotenv()
DEFAULT_MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


def get_quiz_options() -> dict[str, list[str]]:
    """Returns the quiz configuration options supported by Team Quiz.

    Returns:
        A dictionary containing supported question types, difficulty levels, and
        answer length options.
    """
    return {
        "question_types": sorted(ALLOWED_QUESTION_TYPES),
        "difficulty_levels": sorted(DIFFICULTY_LEVELS),
        "answer_lengths": sorted(ANSWER_LENGTHS),
    }


def generate_practice_quiz(
    text_content: str,
    num_questions: int = 3,
    question_type: str = "MCQ",
    difficulty: str = "Basic",
    answer_length: str = "1-line",
) -> dict[str, Any]:
    """Generates a short practice quiz from user-provided study text.

    Args:
        text_content: The source notes, lesson text, or study material to quiz.
        num_questions: Number of questions to generate. Keep this between 1 and 5
            during chat unless the user explicitly asks for more.
        question_type: One of the supported Team Quiz question types.
        difficulty: One of Basic, Intermediate, or Pro.
        answer_length: One of 1-line, 2-line, Detailed, or Essay.

    Returns:
        A dictionary with status, normalized options, and generated questions.
    """
    if not text_content.strip():
        return {"status": "error", "error": "text_content is required"}

    safe_count = max(1, min(int(num_questions), 10))
    safe_type = question_type if question_type in ALLOWED_QUESTION_TYPES else "MCQ"
    safe_difficulty = difficulty if difficulty in DIFFICULTY_LEVELS else "Basic"
    safe_answer_length = answer_length if answer_length in ANSWER_LENGTHS else "1-line"

    questions = generate_quiz(
        text_content=text_content,
        num_questions=safe_count,
        question_type=safe_type,
        difficulty=safe_difficulty,
        answer_length=safe_answer_length,
    )

    return {
        "status": "success",
        "question_type": safe_type,
        "difficulty": safe_difficulty,
        "answer_length": safe_answer_length,
        "questions": questions,
    }


root_agent = Agent(
    model=DEFAULT_MODEL,
    name="team_quiz_study_agent",
    description="A study assistant for Team Quiz that creates quizzes and guides learners.",
    instruction="""
You are the Team Quiz autonomous study assistant.

Persona:
- Be concise, encouraging, and practical.
- Help learners turn notes, pasted text, or document excerpts into useful quizzes.
- When the user asks what the app can do, explain the available quiz options.

Rules and constraints:
- Use only the provided tools when you need project data or quiz generation.
- Do not claim that a quiz was saved to the app unless a tool explicitly reports that.
- Ask for source text when the user wants a generated quiz but has not provided material.
- Prefer small quizzes in chat, usually 3 to 5 questions, unless the user asks otherwise.
- Keep answers grounded in the tool output or the user's supplied text.
- If a requested question type, difficulty, or answer length is unsupported, choose the
  closest supported option and briefly mention the adjustment.
""".strip(),
    # ADK automatically wraps plain Python callables in FunctionTools. Their type
    # hints and Google-style docstrings become the function schema shown to Gemini.
    tools=[get_quiz_options, generate_practice_quiz],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
_created_sessions: set[tuple[str, str]] = set()
_session_lock = asyncio.Lock()


async def _ensure_session(user_id: str, session_id: str) -> None:
    key = (user_id, session_id)
    if key in _created_sessions:
        return

    async with _session_lock:
        if key not in _created_sessions:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            _created_sessions.add(key)


def _event_metadata(event: Any) -> list[dict[str, Any]]:
    metadata: list[dict[str, Any]] = []
    content = getattr(event, "content", None)
    for part in getattr(content, "parts", []) or []:
        function_call = getattr(part, "function_call", None)
        if function_call:
            metadata.append(
                {
                    "type": "function_call",
                    "name": getattr(function_call, "name", None),
                    "args": getattr(function_call, "args", None),
                    "id": getattr(function_call, "id", None),
                }
            )

        function_response = getattr(part, "function_response", None)
        if function_response:
            metadata.append(
                {
                    "type": "function_response",
                    "name": getattr(function_response, "name", None),
                    "response": getattr(function_response, "response", None),
                    "id": getattr(function_response, "id", None),
                }
            )
    return metadata


async def chat_with_agent(
    message: str,
    session_id: str,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """Runs one chat turn through the ADK Runner and returns text plus tool metadata."""
    await _ensure_session(user_id=user_id, session_id=session_id)

    content = types.Content(role="user", parts=[types.Part(text=message)])
    events = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    )

    response_text = ""
    tool_events: list[dict[str, Any]] = []

    async for event in events:
        tool_events.extend(_event_metadata(event))
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text or ""

    return {
        "response": response_text,
        "session_id": session_id,
        "user_id": user_id,
        "tools": tool_events,
    }
