import streamlit as st
import logging

from document_parser import extract_text_from_file, allowed_file, SUPPORTED_EXTENSIONS
from quiz_generator import (
    generate_quiz,
    generate_ai_quiz,
    generate_ollama_quiz,
    ALLOWED_QUESTION_TYPES,
    DIFFICULTY_LEVELS,
    ANSWER_LENGTHS,
)
from i18n_utils import t as tr, set_language, SUPPORTED_LANGUAGES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- App State Initialization ---
def initialize_state():
    """Initializes session state variables."""
    if "quiz" not in st.session_state:
        st.session_state.quiz = None
        st.session_state.current_question_index = 0
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.show_answers = False


# --- UI Components ---
def render_sidebar():
    """Renders the sidebar for configuration."""
    with st.sidebar:
        st.title(tr("app.title"))

        # Language Selection
        st.markdown(tr("language.select"))
        cols = st.columns(len(SUPPORTED_LANGUAGES))
        for i, (lang_code, lang_name) in enumerate(SUPPORTED_LANGUAGES.items()):
            if cols[i].button(
                lang_name, key=f"lang_{lang_code}", use_container_width=True
            ):
                set_language(lang_code)
                st.rerun()

        st.markdown("---")  # Visual separator

        st.markdown(tr("app.subtitle"))

        st.header(tr("generator.mode"))
        mode = st.radio(
            "Mode",
            ["Local", "AI (Gemini)", "Ollama"],
            label_visibility="collapsed",
            key="mode",
            horizontal=True,
        )

        api_key = ""
        if mode == "AI (Gemini)":
            api_key = st.text_input(
                tr("generator.api_key_label", provider="Google"),
                type="password",
                placeholder=tr("generator.api_key_placeholder", provider="Google"),
            )
        elif mode == "Ollama":
            st.info(tr("generator.ollama_active"))
        else:
            st.success(tr("generator.local_active"))

        st.header(tr("generator.upload_label"))
        uploaded_file = st.file_uploader(
            tr("generator.upload_label"),
            type=list(SUPPORTED_EXTENSIONS),
            label_visibility="collapsed",
            help=tr("generator.upload_help"),
        )

        doc_lang_options = list(SUPPORTED_LANGUAGES.keys())
        doc_lang = st.selectbox(
            "Document Language",
            doc_lang_options,
            format_func=lambda x: SUPPORTED_LANGUAGES[x],
        )

        text_content = st.text_area(
            "Text Content",
            placeholder=tr("generator.text_placeholder"),
            height=200,
            label_visibility="collapsed",
        )

        st.header("Quiz Configuration")
        num_questions = st.slider(tr("generator.num_questions"), 1, 50, 10)
        question_type = st.selectbox(
            tr("generator.question_type"), list(ALLOWED_QUESTION_TYPES)
        )
        difficulty = st.selectbox(tr("generator.difficulty"), list(DIFFICULTY_LEVELS))
        answer_length = st.selectbox(
            tr("generator.answer_length"), list(ANSWER_LENGTHS)
        )

        if st.button(
            tr("generator.generate_button"), use_container_width=True, type="primary"
        ):
            handle_quiz_generation(
                mode,
                api_key,
                uploaded_file,
                text_content,
                num_questions,
                question_type,
                difficulty,
                answer_length,
                doc_lang,
            )


def render_quiz():
    """Renders the interactive quiz questions and navigation."""
    quiz = st.session_state.quiz
    if not quiz:
        return

    st.header(tr("quiz.header"))

    # Display progress
    st.progress((st.session_state.current_question_index + 1) / len(quiz))

    q = quiz[st.session_state.current_question_index]
    index = st.session_state.current_question_index

    st.subheader(
        f"{tr('quiz.question_prefix', index=index + 1)} ({tr('quiz.points_badge', points=q.get('points', 1))})"
    )
    st.markdown(q["question"])

    # Answer input
    answer = None
    if q["type"] == "MCQ":
        options = q.get("options", [])
        answer = st.radio(
            "Options", options, key=f"q_{index}", label_visibility="collapsed"
        )
    else:
        answer = st.text_area(tr("quiz.type_answer_prompt"), key=f"q_{index}")

    if answer:
        st.session_state.user_answers[index] = answer

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    if st.session_state.current_question_index > 0:
        if col1.button(tr("quiz.previous_button")):
            st.session_state.current_question_index -= 1
            st.rerun()

    if st.session_state.current_question_index < len(quiz) - 1:
        if col3.button(tr("quiz.next_button")):
            st.session_state.current_question_index += 1
            st.rerun()
    else:
        if col3.button(tr("quiz.submit_quiz_button"), type="primary"):
            st.session_state.quiz_submitted = True
            st.rerun()


def render_scorecard():
    """Renders the final score and allows reviewing answers."""
    quiz = st.session_state.quiz
    user_answers = st.session_state.user_answers
    score = 0
    max_score = 0

    for i, q in enumerate(quiz):
        max_score += q.get("points", 1)
        user_ans = user_answers.get(i)
        correct_ans = q.get("answer")
        if q["type"] == "MCQ":
            correct_ans = q["options"][q["correct_index"]]

        if (
            user_ans
            and str(user_ans).strip().lower() == str(correct_ans).strip().lower()
        ):
            score += q.get("points", 1)

    percentage = (score / max_score * 100) if max_score > 0 else 0
    st.header(tr("quiz.score_card_header", score=score, max_score=max_score))
    st.subheader(tr("quiz.score_percentage", percentage=f"{percentage:.2f}"))

    st.session_state.show_answers = st.toggle(tr("quiz.show_answers_button"))

    if st.session_state.show_answers:
        for i, q in enumerate(quiz):
            with st.expander(
                f"{tr('quiz.question_prefix', index=i + 1)}: {q['question'][:50]}..."
            ):
                st.markdown(
                    f"**{tr('quiz.your_answer')}:** {user_answers.get(i, 'Not Answered')}"
                )

                correct_ans_display = q.get("answer")
                if q["type"] == "MCQ":
                    correct_ans_display = q["options"][q["correct_index"]]

                st.markdown(
                    f"**{tr('quiz.correct_answer_label')}** {correct_ans_display}"
                )
                if "explanation" in q:
                    st.info(tr("quiz.explanation_label", explanation=q["explanation"]))

    if st.button(tr("quiz.new_quiz_button")):
        # Reset state for a new quiz
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# --- Logic ---
def handle_quiz_generation(
    mode,
    api_key,
    uploaded_file,
    text_content,
    num_questions,
    question_type,
    difficulty,
    answer_length,
    doc_lang,
):
    """Processes inputs and calls the correct quiz generation function."""
    content = ""
    filename = ""
    if uploaded_file:
        if not allowed_file(uploaded_file.name):
            st.error(tr("generator.errors.unsupported_file"))
            return
        filename = uploaded_file.name
        with st.spinner(f"Extracting text from {filename}..."):
            try:
                file_bytes = uploaded_file.getvalue()
                content = extract_text_from_file(file_bytes, filename, lang=doc_lang)
            except Exception as e:
                st.error(f"Error reading file: {e}")
                logger.error(f"File read error for {filename}: {e}")
                return
    elif text_content:
        content = text_content
    else:
        st.warning(tr("generator.errors.no_input"))
        return

    if not content.strip():
        st.error(tr("generator.errors.no_text_extracted", filename=filename))
        return

    with st.spinner(tr("generator.spinner")):
        try:
            quiz_data = None
            if mode == "Local":
                quiz_data = generate_quiz(
                    content, num_questions, question_type, difficulty, answer_length
                )
            elif mode == "AI (Gemini)":
                if not api_key:
                    st.error("Google API key is required for AI mode.")
                    return
                quiz_data = generate_ai_quiz(
                    content,
                    num_questions,
                    question_type,
                    difficulty,
                    answer_length,
                    api_key,
                )
            elif mode == "Ollama":
                # Assuming default model, can be made configurable
                quiz_data = generate_ollama_quiz(
                    content, num_questions, question_type, difficulty, answer_length
                )

            if not quiz_data:
                st.error(
                    tr(
                        "generator.errors.generation_failed",
                        error="No questions were generated.",
                    )
                )
                return

            # Reset state and store new quiz
            st.session_state.quiz = quiz_data
            st.session_state.current_question_index = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.rerun()

        except Exception as e:
            st.error(tr("generator.errors.generation_failed", error=str(e)))
            logger.error(f"Quiz generation failed: {e}", exc_info=True)


# --- Main App ---
def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title=tr("app.title"), layout="wide")

    initialize_state()
    render_sidebar()

    if st.session_state.quiz:
        if st.session_state.quiz_submitted:
            render_scorecard()
        else:
            render_quiz()
    else:
        st.info(
            "👋 Welcome! Configure your quiz in the sidebar and click 'Generate Quiz' to start."
        )
        st.markdown(
            f"<div style='text-align: center; margin-top: 20px;'>{tr('app.made_with')}</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
