import streamlit as st
from pathlib import Path

# --- Core Imports ---
from i18n_utils import t, set_language, SUPPORTED_LANGUAGES
from config import settings

# --- Feature Imports ---
from document_parser import extract_text_from_file, SUPPORTED_EXTENSIONS
from rag_workflow import (
    create_vector_store,
    extract_text_chunks,
    generate_answer,
    get_embedding_model,
    get_llm,
    retrieve_context,
)

# --- AI Provider Imports ---
from base import AIProvider
from local import LocalProvider
from gemini import GeminiProvider
from ollama_provider import OllamaProvider


# --- Page Config ---
st.set_page_config(page_title="Team Quiz", page_icon="🧠", layout="centered")


def load_css():
    css_file = Path(__file__).parent / "style.css"
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "show_quiz" not in st.session_state:
    st.session_state.show_quiz = False
if "show_answers" not in st.session_state:
    st.session_state.show_answers = False
if "question_type" not in st.session_state:
    st.session_state.question_type = "MCQ"  # Default value
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Basic"  # Default value
if "answer_length" not in st.session_state:
    st.session_state.answer_length = "1-line"  # Default value
if "provider_name" not in st.session_state:
    st.session_state.provider_name = "Local"  # Default provider
if "api_key" not in st.session_state:
    st.session_state.api_key = ""  # For BYOK
if "qna_chunks" not in st.session_state:
    st.session_state.qna_chunks = None
if "qna_vector_store" not in st.session_state:
    st.session_state.qna_vector_store = None
if "qna_doc_filename" not in st.session_state:
    st.session_state.qna_doc_filename = None


def reset_quiz() -> None:
    st.session_state.questions = []
    st.session_state.current_index = 0
    st.session_state.user_answers = []
    st.session_state.quiz_submitted = False
    st.session_state.show_quiz = False
    st.session_state.show_answers = False


def type_badge(q_type: str) -> str:
    badge_class = {
        "MCQ": "badge-mcq",
        "Very Short Answer": "badge-very-short",
        "Short Answer": "badge-short",
        "Long Answer": "badge-long",
        "Essay": "badge-essay",
    }.get(q_type, "badge-mcq")
    return f'<span class="{badge_class}">{q_type}</span>'


def render_quiz() -> None:
    questions = st.session_state.questions
    current_index = st.session_state.current_index
    user_answers = st.session_state.user_answers
    submitted = st.session_state.quiz_submitted
    show_answers = st.session_state.show_answers

    q = questions[current_index]
    q_type = q.get("type", "")
    points = q.get("points", 1)

    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    st.markdown(
        f'<h2 class="title-gradient">🧠 {t("quiz.header")}</h2>', unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="question-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f'<div class="points-badge">{t("quiz.points_badge", points=points)}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(type_badge(q_type), unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#e2e8f0; font-size:16px; font-weight:500;">{t("quiz.question_prefix", index=current_index + 1)}. {q["question"]}</p>',
        unsafe_allow_html=True,
    )

    if submitted or show_answers:
        if q_type == "MCQ":
            for i, option in enumerate(q["options"]):
                correct = i == q["correct_index"]
                chosen = user_answers[current_index] == i
                if correct:
                    st.markdown(
                        f'<div class="correct-answer">✅ <strong>{option}</strong></div>',
                        unsafe_allow_html=True,
                    )
                elif chosen:
                    st.markdown(
                        f'<div style="opacity:0.6; padding:8px;">❌ {option}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="opacity:0.4; padding:8px;">▫️ {option}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            answer_display = (
                user_answers[current_index]
                if user_answers[current_index]
                else "Not answered"
            )
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.08); padding:12px; border-radius:10px; margin:8px 0;"><strong>{t("quiz.your_answer")}:</strong> {answer_display}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="answer-box"><strong>{t("quiz.correct_answer_label")}</strong><br>'
            + str(q["answer"]).replace("\n", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )
        st.caption(t("quiz.explanation_label", explanation=q.get("explanation", "")))
    else:
        if q_type == "MCQ":
            options = q.get("options", [])
            cols = st.columns(2)
            for i, option in enumerate(options):
                with cols[i % 2]:
                    if st.button(
                        option, key=f"opt_{i}_{current_index}", use_container_width=True
                    ):
                        st.session_state.user_answers[current_index] = i
                        st.rerun()

            if user_answers[current_index] is None:
                st.caption(t("quiz.select_answer_prompt"))
        elif q_type in ("Very Short Answer", "Short Answer"):
            user_input = st.text_input(
                "short_answer_input",
                key=f"short_{current_index}",
                label_visibility="collapsed",
                placeholder=t("quiz.type_answer_prompt"),
            )
            if st.button(
                t("quiz.submit_answer_button"),
                key=f"submit_short_{current_index}",
                use_container_width=True,
            ):
                st.session_state.user_answers[current_index] = user_input
                st.rerun()
            if user_answers[current_index] is None:
                st.caption(t("quiz.type_answer_prompt"))
        else:
            user_input = st.text_area(
                "long_answer_input",
                key=f"long_{current_index}",
                label_visibility="collapsed",
                height=150,
                placeholder=t("quiz.type_answer_prompt"),
            )
            if st.button(
                t("quiz.submit_answer_button"),
                key=f"submit_long_{current_index}",
                use_container_width=True,
            ):
                st.session_state.user_answers[current_index] = user_input
                st.rerun()
            if user_answers[current_index] is None:
                st.caption(t("quiz.type_answer_prompt"))

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div style="display:flex; gap:12px; margin-top:20px;">', unsafe_allow_html=True
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if current_index > 0 and st.button(
            t("quiz.previous_button"), use_container_width=True
        ):
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        if current_index < len(questions) - 1 and st.button(
            t("quiz.next_button"), use_container_width=True
        ):
            st.session_state.current_index += 1
            st.rerun()
    with col3:
        if not submitted and st.button(
            t("quiz.submit_quiz_button"), use_container_width=True
        ):
            unanswered = [
                i + 1
                for i, a in enumerate(user_answers)
                if a is None or (isinstance(a, str) and a.strip() == "")
            ]
            if unanswered:
                st.warning(t("quiz.unanswered_warning", questions=unanswered))
            else:
                st.session_state.quiz_submitted = True
                st.rerun()
    with col4:
        if st.button(
            t("quiz.show_answers_button")
            if not show_answers
            else t("quiz.hide_answers_button"),
            use_container_width=True,
        ):
            st.session_state.show_answers = not show_answers
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        score = 0
        max_score = 0
        for i, q in enumerate(questions):
            ans = user_answers[i]
            points = q.get("points", 1)
            max_score += points
            if q.get("type") == "MCQ":
                if ans == q.get("correct_index"):
                    score += points
            elif (
                isinstance(ans, str)
                and ans.strip().lower() == q.get("answer", "").strip().lower()
            ):
                score += points

        st.markdown('<div class="score-card">', unsafe_allow_html=True)
        st.markdown(
            f'<h2 style="color:#10b981; margin:0;">{t("quiz.score_card_header", score=score, max_score=max_score)}</h2>',
            unsafe_allow_html=True,
        )
        percentage = int((score / max_score) * 100) if max_score > 0 else 0
        st.markdown(
            f'<p style="color:#94a3b8; margin-top:8px;">{t("quiz.score_percentage", percentage=percentage)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button(t("quiz.new_quiz_button"), use_container_width=True):
            reset_quiz()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_generator() -> None:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="title-gradient">🧠 {t("app.title")}</h1>', unsafe_allow_html=True
    )
    st.markdown(
        f'<p class="subtitle">{t("app.subtitle")}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">📋 {t("generator.question_type")}</label>',
            unsafe_allow_html=True,
        )
        question_type = st.selectbox(
            "question_type_select",
            ["MCQ", "Very Short Answer", "Short Answer", "Long Answer", "Essay"],
            index=[
                "MCQ",
                "Very Short Answer",
                "Short Answer",
                "Long Answer",
                "Essay",
            ].index(st.session_state.question_type),
            label_visibility="collapsed",
        )
        st.session_state.question_type = question_type
    with col2:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">⚡ {t("generator.difficulty")}</label>',
            unsafe_allow_html=True,
        )
        difficulty = st.selectbox(
            "difficulty_select",
            ["Basic", "Intermediate", "Pro"],
            index=["Basic", "Intermediate", "Pro"].index(st.session_state.difficulty),
            label_visibility="collapsed",
        )
        st.session_state.difficulty = difficulty
    with col3:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">📏 {t("generator.answer_length")}</label>',
            unsafe_allow_html=True,
        )
        answer_length = st.selectbox(
            "answer_length_select",
            ["1-line", "2-line", "Detailed", "Essay"],
            index=["1-line", "2-line", "Detailed", "Essay"].index(
                st.session_state.answer_length
            ),
            label_visibility="collapsed",
        )
        st.session_state.answer_length = answer_length
    with col4:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">🔢 {t("generator.num_questions")}</label>',
            unsafe_allow_html=True,
        )
        num_questions = st.number_input(
            "num_questions_input",
            min_value=1,
            max_value=20,
            value=10,
            step=1,
            label_visibility="collapsed",
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # --- Provider Selection (BYOK and Ollama) ---
    provider_options = ["Local"]
    if settings.GEMINI_API_KEY:
        provider_options.append("Gemini")
    if settings.OLLAMA_HOST:
        provider_options.append("Ollama (Local)")
    # ... add other providers like OpenAI, Anthropic here

    selected_provider = st.selectbox(t("generator.mode"), provider_options)
    st.session_state.provider_name = selected_provider

    provider: AIProvider
    if selected_provider == "Local":
        provider = LocalProvider()
    elif selected_provider == "Gemini":
        provider = GeminiProvider(api_key=settings.GEMINI_API_KEY)
    elif selected_provider == "Ollama (Local)":
        # In a real app, you'd have a model selector UI here
        provider = OllamaProvider(model="llama3", host=settings.OLLAMA_HOST)
    else:
        st.error("Selected provider is not configured.")
        return

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    with st.form("quiz_form"):
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:#94a3b8; font-size:14px; margin-bottom:12px;">📁 {t("generator.upload_label")}</p>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "file_uploader",
            type=list(SUPPORTED_EXTENSIONS),
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px;">', unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:#94a3b8; font-size:14px; margin-bottom:8px;">✏️ {t("generator.upload_help")}</p>',
            unsafe_allow_html=True,
        )
        text_input = st.text_area(
            "text_input_area",
            height=150,
            label_visibility="collapsed",
            placeholder=t("generator.text_placeholder"),
        )
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                t("generator.generate_button"), use_container_width=True
            )

    if submitted:
        text_content = ""
        source_name = ""

        if uploaded_file is not None:
            source_name = uploaded_file.name
            try:
                raw_content = uploaded_file.read()
                text_content = extract_text_from_file(raw_content, source_name)
            except ValueError:
                st.error(t("generator.errors.unsupported_file"))
                return

        if not text_content.strip():
            text_content = text_input.strip()

        if not text_content.strip():
            if uploaded_file is not None:
                st.warning(
                    t("generator.errors.no_text_extracted", filename=uploaded_file.name)
                )
            else:
                st.warning(t("generator.errors.no_input"))
            return

        try:
            with st.spinner(t("generator.spinner")):
                questions = provider.generate_quiz(
                    text_content=text_content,
                    num_questions=num_questions,
                    question_type=st.session_state.question_type,
                    difficulty=st.session_state.difficulty,
                    answer_length=st.session_state.answer_length,
                )

            if not questions:
                st.error("❌ Failed to generate questions. Please try different input.")
                return

            st.session_state.questions = questions
            st.session_state.current_index = 0
            st.session_state.user_answers = [None] * len(questions)
            st.session_state.quiz_submitted = False
            st.session_state.show_quiz = True
            st.session_state.show_answers = False
            st.rerun()

        except Exception as exc:
            st.error(t("generator.errors.generation_failed", error=exc))

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="footer">{t("app.made_with")}</div>', unsafe_allow_html=True
    )


def render_qna() -> None:
    """Renders the Document Q&A interface."""
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="title-gradient">📄 {t("qna.mode_name")}</h1>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # The document upload is handled in the sidebar within main()

    if st.session_state.qna_vector_store is None:
        st.warning(t("qna.error_no_document"))
    else:
        embedding_model = get_embedding_model()
        llm = get_llm()

        question = st.text_input(
            "qna_question",
            placeholder=t("qna.question_placeholder"),
            label_visibility="collapsed",
        )

        if st.button(t("qna.ask_button"), use_container_width=True, type="primary"):
            if not question:
                st.error(t("qna.error_no_question"))
            elif llm is None:
                st.error(
                    "The local LLM is not loaded. Please check the model path and configuration."
                )
            else:
                with st.spinner(t("qna.spinner")):
                    context = retrieve_context(
                        question,
                        st.session_state.qna_vector_store,
                        st.session_state.qna_chunks,
                        embedding_model,
                    )
                    answer = generate_answer(question, context, llm)

                st.subheader(t("qna.answer_header"))
                st.markdown(answer)

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    load_css()

    with st.sidebar:
        st.markdown("## Settings")

        app_mode = st.radio(
            "Mode", options=["Quiz Generator", "Document Q&A"], key="app_mode"
        )
        st.markdown("---")

        # Language Switcher
        lang_name = st.selectbox(
            "Language",
            options=list(SUPPORTED_LANGUAGES.values()),
            index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.language),
        )
        lang_code = [
            code for code, name in SUPPORTED_LANGUAGES.items() if name == lang_name
        ][0]
        if lang_code != st.session_state.language:
            set_language(lang_code)
            st.rerun()

        # Conditional sidebar for Q&A
        if app_mode == "Document Q&A":
            st.markdown("---")
            st.header(t("qna.upload_label"))
            uploaded_file = st.file_uploader(
                "qna_uploader",
                type="pdf",
                accept_multiple_files=False,
                label_visibility="collapsed",
            )

            if uploaded_file:
                if uploaded_file.name != st.session_state.qna_doc_filename:
                    st.session_state.qna_doc_filename = uploaded_file.name

                    temp_dir = Path("temp_docs")
                    temp_dir.mkdir(exist_ok=True)
                    file_path = temp_dir / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        st.session_state.qna_chunks = extract_text_chunks(file_path)

                        if not st.session_state.qna_chunks:
                            st.error("Could not extract text from the PDF.")
                        else:
                            embedding_model = get_embedding_model()
                            st.session_state.qna_vector_store = create_vector_store(
                                st.session_state.qna_chunks, embedding_model
                            )
                            st.success(
                                f"✅ Ready to answer questions about **{uploaded_file.name}**"
                            )
                else:
                    st.info(f"✅ **{uploaded_file.name}** is already loaded.")

    if app_mode == "Quiz Generator":
        if st.session_state.show_quiz and st.session_state.questions:
            render_quiz()
        else:
            render_generator()
    elif app_mode == "Document Q&A":
        render_qna()


if __name__ == "__main__":
    main()
