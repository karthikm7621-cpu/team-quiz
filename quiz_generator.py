import json
import logging
import random
import re
import time
import typing
from ollama_provider import OllamaProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_QUESTION_TYPES = {
    "MCQ",
    "Very Short Answer",
    "Short Answer",
    "Long Answer",
    "Essay",
}
DIFFICULTY_LEVELS = {"Basic", "Intermediate", "Pro"}
ANSWER_LENGTHS = {"1-line", "2-line", "Detailed", "Essay"}


def _pick_keyword(sentence: str) -> str:
    words = sentence.split()
    candidates = [w for w in words if len(w) > 2 and w.isalpha()]
    return random.choice(candidates) if candidates else words[len(words) // 2]  # nosec B311


def _pick_wrong_options(sentences: list[str], correct_word: str) -> list[str]:
    pool: list[str] = []
    for s in sentences:
        for w in s.split():
            if len(w) > 2 and w.isalpha() and w != correct_word and w not in pool:
                pool.append(w)
    random.shuffle(pool)  # nosec B311
    return pool[:3]


def _pick_sentences(sentences: list[str], count: int = 1) -> list[str]:
    return random.sample(sentences, min(count, len(sentences)))  # nosec B311


def _make_mcq(
    sentence: str, difficulty: str, answer_length: str, points: int
) -> tuple[str, list[str], int]:
    word = _pick_keyword(sentence)
    wrong = _pick_wrong_options([sentence], word)
    if len(wrong) < 3:
        wrong = ["Option A", "Option B", "Option C", "Option D"]
    options = [word] + wrong[:3]
    random.shuffle(options)  # nosec B311
    correct_index = options.index(word)

    if difficulty == "Basic":
        question_text = f'[{points} mark] What is "{word}"?'
    elif difficulty == "Intermediate":
        question_text = (
            f'[{points} mark] Which word best fits this context: "{sentence[:80]}..."?'
        )
    else:
        question_text = f'[{points} mark] Analyze: Which term completes this idea "{sentence[:70]}..."? Choose the most accurate option.'
    return question_text, options, correct_index


def _generate_local_mcq(
    sentence: str, difficulty: str, answer_length: str, points: int
) -> dict:
    qtxt, options, ci = _make_mcq(sentence, difficulty, answer_length, points)
    word = options[ci]

    answer_map = {
        "1-line": word,
        "2-line": f"{word} – it is the key term identified in the given context.",
        "Detailed": f'{word} is the correct answer. It matches the context of: "{sentence[:60]}..." It carries significant meaning here.',
        "Essay": (
            f"{word} is the correct answer. "
            f'In the context of "{sentence[:70]}...", this term holds the most weight. '
            f"Option analysis shows it aligns with the passage better than distractors. "
            f"Therefore, {word} is selected based on contextual relevance."
        ),
    }

    return {
        "type": "MCQ",
        "question": qtxt,
        "points": points,
        "options": options,
        "correct_index": ci,
        "answer": answer_map.get(answer_length, word),
        "explanation": f'Reference: "{sentence[:60]}..."',
    }


def _generate_local_vsa(
    sentence: str, difficulty: str, answer_length: str, points: int
) -> dict:
    word = _pick_keyword(sentence)

    q_map = {
        "Basic": (f'[{points} mark] What is "{word}"?', word),
        "Intermediate": (
            f'[{points} mark] State the meaning of "{word}" from the text.',
            f"{word} refers to the key concept in the passage.",
        ),
        "Pro": (
            f'[{points} mark] Why is "{word}" significant in the passage?',
            f"{word} is significant because it connects multiple ideas in the passage.",
        ),
    }
    question, answer = q_map.get(difficulty, q_map["Basic"])

    if answer_length != "1-line":
        answer += f" {sentence[:60]}..."

    return {
        "type": "Very Short Answer",
        "question": question,
        "points": points,
        "answer": answer,
        "explanation": f'Reference: "{sentence[:60]}..."',
    }


def _generate_local_short_answer(
    sentence: str, difficulty: str, answer_length: str, points: int
) -> dict:
    word = _pick_keyword(sentence)

    q_map = {
        "Basic": (
            f"[{points} mark] Explain briefly: {sentence[:80]}...",
            f"{word} is a key term that supports the main idea.",
        ),
        "Intermediate": (
            f'[{points} mark] Describe briefly how "{word}" affects the passage.',
            f"{word} has a direct impact on the passage meaning. It helps readers understand the central theme better.",
        ),
        "Pro": (
            f'[{points} mark] Pro-level: Explain the role of "{word}" in this context with one example.',
            f'{word} plays a key role by reinforcing the theme. For example, in the sentence "{sentence[:60]}...", it elevates the overall message.',
        ),
    }
    question, answer = q_map.get(difficulty, q_map["Basic"])

    if answer_length == "Detailed":
        answer += f" {sentence[:60]}..."

    return {
        "type": "Short Answer",
        "question": question,
        "points": points,
        "answer": answer,
        "explanation": f'Reference: "{sentence[:60]}..."',
    }


def _generate_local_long_answer(
    sentence: str, difficulty: str, answer_length: str, points: int
) -> dict:
    word = _pick_keyword(sentence)

    q_map = {
        "Basic": (
            f"[{points} mark] Write a short note on: {sentence[:80]}...",
            f"{word} is important. It helps explain the main point and gives context to the passage.",
        ),
        "Intermediate": (
            f'[{points} mark] Describe the importance of "{word}" in: {sentence[:80]}...',
            f"{word} contributes greatly. It supports the argument and adds depth to the understanding of the topic. Without it, the passage would be incomplete.",
        ),
        "Pro": (
            f'[{points} mark] Analyze the importance of "{word}" in: {sentence[:80]}...',
            f'{word} is a central concept. It influences multiple aspects of the passage by connecting ideas and strengthening arguments. Contextually, it appears in: "{sentence[:70]}...", which highlights its relevance.',
        ),
    }
    question, answer = q_map.get(difficulty, q_map["Basic"])

    if answer_length in ("1-line", "2-line"):
        answer = ". ".join(answer.split(". ")[:2]) + "."
    if answer_length == "Essay":
        answer += f" In summary, {word} is indispensable. Further study can reveal deeper insights about its role in the given context."

    return {
        "type": "Long Answer",
        "question": question,
        "points": points,
        "answer": answer,
        "explanation": f'Reference: "{sentence[:60]}..."',
    }


def _generate_local_essay(
    sentence: str, difficulty: str, answer_length: str, points: int
) -> dict:
    word = _pick_keyword(sentence)

    answer_map = {
        "1-line": f"{word} is significant for the topic.",
        "2-line": f"{word} is important in context. It contributes to the central theme.",
        "default": (
            f"{word} is a key concept that shapes the narrative. "
            f"It contributes to the overall structure and supports the central theme. "
            f'In the passage "{sentence[:70]}...", {word} appears as a significant element. '
            f"An in-depth essay should cover its background, impact, and broader implications."
        ),
    }
    answer = answer_map.get(answer_length, answer_map["default"])

    return {
        "type": "Essay",
        "question": f'[{points} mark] Essay: Discuss in detail the importance of "{word}" with reference to: {sentence[:80]}...',
        "points": points,
        "answer": answer,
        "explanation": f'Reference: "{sentence[:60]}..."',
    }


def generate_quiz(
    text_content: str,
    num_questions: int = 10,
    question_type: str = "MCQ",
    difficulty: str = "Basic",
    answer_length: str = "1-line",
) -> list[dict[str, typing.Any]]:
    sentences = re.split(r"[.!?]+", text_content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15][
        : max(num_questions * 4, 40)
    ]
    if not sentences:
        sentences = [text_content[:200]]

    # Map question types to their generator functions
    question_generators = {
        "MCQ": _generate_local_mcq,
        "Very Short Answer": _generate_local_vsa,
        "Short Answer": _generate_local_short_answer,
        "Long Answer": _generate_local_long_answer,
        "Essay": _generate_local_essay,
    }

    generator_func = question_generators.get(question_type)
    if not generator_func:
        logger.warning(
            f"Unsupported local question type: {question_type}. Defaulting to MCQ."
        )
        generator_func = _generate_local_mcq

    questions = []
    for idx in range(num_questions):
        sentence = _pick_sentences(sentences)[0]
        points = idx + 1
        q = generator_func(sentence, difficulty, answer_length, points)
        questions.append(q)

    return questions[:num_questions]


def generate_ai_quiz(
    text_content: str,
    num_questions: int = 10,
    question_type: str = "MCQ",
    difficulty: str = "Basic",
    answer_length: str = "1-line",
    api_key: str = "",
) -> list[dict[str, typing.Any]]:
    if not api_key.strip():
        raise ValueError("AI mode requires a valid API key.")

    try:
        from google import genai
        from google.genai import types as genai_types
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        raise RuntimeError("AI mode requires google-genai. Install it and try again.")

    client = genai.Client(api_key=api_key.strip())

    type_map = {
        "MCQ": "multiple-choice",
        "Very Short Answer": "very-short-answer",
        "Short Answer": "short-answer",
        "Long Answer": "long-answer",
        "Essay": "essay",
    }
    ai_type = type_map.get(question_type, "multiple-choice")

    answer_instruction = {
        "1-line": "Keep answers as short as possible, ideally one line.",
        "2-line": "Keep answers concise, about two lines.",
        "Detailed": "Provide detailed, well-explained answers.",
        "Essay": "Provide long, comprehensive essay-style model answers.",
    }.get(answer_length, "Keep answers concise.")

    MAX_OUTPUT_TOKENS = 8192
    for attempt in range(3):
        try:
            prompt = (
                "You are an advanced educational assessment engine. "
                "Analyze the following decoded data and generate quiz questions strictly from that data only. "
                "Do not use outside information and do not include conversational filler.\n\n"
                "Strict output contract:\n"
                "- Format: one JSON object with exactly one key named quiz.\n"
                "- quiz must be an array of question objects.\n"
                "- Each question object must have exactly: question (string), type (string), answer (string).\n"
                "- Allowed type values: mcq, fill_in_blank, short_answer, long_answer, essay.\n"
                "- If type is mcq, also include options (array of 4 strings) and correct_index (integer 0-3).\n"
                "- Do not include any extra keys or conversational text.\n\n"
                f"Generate {num_questions} {difficulty} questions.\n"
                f"- Question-type mix: include multiple-choice, fill-in-the-blank, short answer, long answer, and essay where useful.\n"
                f"- Preferred focus: {ai_type} when it fits the content.\n"
                f"- {answer_instruction}\n"
                "- Number the questions with a short prefix like [1 mark], [2 marks], etc., increasing by 1 each question in order.\n\n"
                "Data:\n"
                f"{text_content}"
            )

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                ),
            )

            raw = getattr(response, "text", "") or ""
            if not raw.strip():
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise ValueError("Empty response from AI model.")

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise ValueError(f"Invalid JSON from AI model: {e}")

            if (
                not isinstance(data, dict)
                or "quiz" not in data
                or not isinstance(data["quiz"], list)
            ):
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise ValueError("AI response must be a JSON object with a quiz array.")

            questions = []
            for idx, item in enumerate(data["quiz"][:num_questions]):
                if not isinstance(item, dict):
                    continue

                q_type_raw = (
                    (item.get("type") or "")
                    .strip()
                    .lower()
                    .replace(" ", "_")
                    .replace("-", "_")
                )
                # Normalize AI output types to the application's standard types.
                q_type_map = {
                    "mcq": "MCQ",
                    "multiple-choice": "MCQ",
                    "fill_in_blank": "Very Short Answer",
                    "very_short_answer": "Very Short Answer",
                    "veryshortanswer": "Very Short Answer",
                    "short_answer": "Short Answer",
                    "long_answer": "Long Answer",
                    "essay": "Essay",
                }
                # Default to "Short Answer" if the type is unknown.
                q_type = q_type_map.get(q_type_raw, "Short Answer")

                question_text = (item.get("question") or "").strip()
                answer_text = (item.get("answer") or "").strip()
                if not question_text or not answer_text:
                    continue

                points = max(1, min(idx + 1, 20))

                q = {
                    "type": q_type,
                    "question": question_text,
                    "points": points,
                    "answer": answer_text,
                    "explanation": "Source-based answer generated from provided data.",
                }

                if q_type == "MCQ":
                    options = item.get("options") or []
                    if not isinstance(options, list):
                        options = []
                    if len(options) < 2:
                        options = [answer_text, "Option B", "Option C", "Option D"]
                    options = [str(o) for o in options[:4]]
                    correct_index = item.get("correct_index", 0)
                    try:
                        correct_index = int(correct_index)
                    except Exception:
                        correct_index = 0
                    correct_index = max(0, min(correct_index, len(options) - 1))
                    q["options"] = options
                    q["correct_index"] = correct_index

                questions.append(q)

            if not questions:
                raise ValueError("No valid questions were generated by AI.")

            return questions

        except google_exceptions.ResourceExhausted as exc:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"AI rate limit exceeded after retries: {exc}") from exc
        except Exception as exc:
            if attempt < 2:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"AI generation failed: {exc}") from exc

    raise RuntimeError("AI generation failed after retries.")


def generate_ollama_quiz(
    text_content: str,
    num_questions: int,
    question_type: str,
    difficulty: str,
    answer_length: str,
    model: str = "llama3",
) -> list[dict[str, typing.Any]]:
    """Generates quiz questions using a local Ollama model."""
    provider = OllamaProvider(model=model)
    return provider.generate_quiz(
        text_content=text_content,
        num_questions=num_questions,
        question_type=question_type,
        difficulty=difficulty,
        answer_length=answer_length,
    )
