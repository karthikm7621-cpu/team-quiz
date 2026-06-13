"""
Main Streamlit application file for the Team Quiz Generator.
This file handles the UI, state management, and quiz generation logic.
"""
import streamlit as st
from dotenv import load_dotenv
import yaml
from pathlib import Path

from quiz_generator import (
    allowed_file,
    extract_text_from_file,
    generate_quiz,
    generate_ai_quiz,
    generate_ollama_quiz,
    ALLOWED_EXTENSIONS,
)

load_dotenv()

# --- HELPERS and SETUP ---
@st.cache_data
def load_css(file_name: Path):
    """Loads a CSS file into the Streamlit app."""
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_session_state():
    """Initializes all required session state variables with default values."""
    defaults = {
        "questions": [],
        "current_index": 0,
        "user_answers": [],
        "quiz_submitted": False,
        "show_quiz": False,
        "show_answers": False,
        "question_type": "MCQ",
        "difficulty": "Basic",
        "answer_length": "1-line",
        "mode": "Local",
        "api_key": "",
        "lang": "en",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- I18N and L10N SETUP ---
@st.cache_data
def load_translations(lang_code: str) -> dict:
    """Loads translation strings from a YAML file."""
    base_path = Path(__file__).parent
    filepath = base_path / f"{lang_code}.yml"
    if not filepath.exists():
        filepath = base_path / "en.yml"  # Fallback to English
    with open(filepath, "r", encoding="utf-8") as f:
        lang_data = yaml.safe_load(f)
        return lang_data.get(lang_code, {})

def get_translator(lang_code: str):
    """Returns a translator function for the given language."""
    translations = load_translations(lang_code)
    def t(key: str, **kwargs) -> str:
        keys = key.split('.')
        value = translations
        try:
            for k in keys:
                value = value[k]
            return str(value).format(**kwargs)
        except (KeyError, TypeError):
            return key  # Return the key if translation is not found
    return t

st.set_page_config(
    page_title="Team Quiz",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="auto",
)
initialize_session_state()
load_css(Path(__file__).parent / "style.css")

# --- LANGUAGE SELECTOR ---
languages = {"en": "English", "hi": "हिंदी (Hindi)", "ta": "தமிழ் (Tamil)"}
with st.sidebar:
    st.markdown("### Language / भाषा / மொழி")
    selected_lang_code = st.selectbox(
        "Language",
        options=list(languages.keys()),
        format_func=lambda code: languages[code],
        key="lang_selector",
        label_visibility="collapsed"
    )
    if selected_lang_code and selected_lang_code != st.session_state.lang:
        st.session_state.lang = selected_lang_code
        st.rerun()

t = get_translator(st.session_state.lang)

# --- LOGIC ---

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
    st.markdown(f'<h2 class="title-gradient">{t("quiz.header")}</h2>', unsafe_allow_html=True)
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
        st.caption(t("quiz.explanation_label", explanation=q['explanation']))
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
                "Type your answer here...",
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
                "Type your detailed answer here...",
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
        if current_index > 0 and st.button(t("quiz.previous_button"), use_container_width=True):
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        if current_index < len(questions) - 1 and st.button(
            t("quiz.next_button"), use_container_width=True
        ):
            st.session_state.current_index += 1
            st.rerun()
    with col3:
        if not submitted and st.button(t("quiz.submit_quiz_button"), use_container_width=True):
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
            t("quiz.show_answers_button") if not show_answers else t("quiz.hide_answers_button"),
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
        f'<h1 class="title-gradient">{t("app.title")}</h1>', unsafe_allow_html=True
    )
    st.markdown(
        f'<p class="subtitle">{t("app.subtitle")}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">{t("generator.question_type")}</label>',
            unsafe_allow_html=True,
        )
        question_type = st.selectbox(
            "Question Type",
            options=["MCQ", "Very Short Answer", "Short Answer", "Long Answer", "Essay"],
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
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">{t("generator.difficulty")}</label>',
            unsafe_allow_html=True,
        )
        difficulty = st.selectbox(
            "Difficulty",
            ["Basic", "Intermediate", "Pro"],
            index=["Basic", "Intermediate", "Pro"].index(st.session_state.difficulty),
            label_visibility="collapsed",
        )
        st.session_state.difficulty = difficulty
    with col3:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">{t("generator.answer_length")}</label>',
            unsafe_allow_html=True,
        )
        answer_length = st.selectbox(
            "Answer Length",
            ["1-line", "2-line", "Detailed", "Essay"],
            index=["1-line", "2-line", "Detailed", "Essay"].index(
                st.session_state.answer_length
            ),
            label_visibility="collapsed",
        )
        st.session_state.answer_length = answer_length
    with col4:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">{t("generator.num_questions")}</label>',
            unsafe_allow_html=True,
        )
        num_questions = st.number_input(
            "Number of questions",
            min_value=1,
            max_value=20,
            value=10,
            step=1,
            label_visibility="collapsed",
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">{t("generator.mode")}</label>',
            unsafe_allow_html=True,
        )
        mode = st.selectbox(
            "Mode",
            ["Local", "Ollama (Local)", "AI-Powered (Gemini)"],
            index=["Local", "Ollama (Local)", "AI-Powered (Gemini)"].index(st.session_state.mode),
            label_visibility="collapsed",
        )
        st.session_state.mode = mode
    with col2:
        if mode == "AI-Powered (Gemini)":
            st.markdown(
                f'<label style="color:#e2e8f0; font-weight:500; font-size:13px;">{t("generator.api_key_label", provider="Gemini")}</label>',
                unsafe_allow_html=True,
            )
            api_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.api_key,
                type="password",
                label_visibility="collapsed",
                placeholder=t("generator.api_key_placeholder", provider="Gemini"),
            )
            st.session_state.api_key = api_key
        elif mode == "Ollama (Local)":
            st.markdown(
                f'<div style="height: 62px; display: flex; align-items: center; justify-content: start;"><label style="color:#94a3b8; font-weight:500; font-size:13px;">✅ {t("generator.ollama_active")}</label></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="height: 62px; display: flex; align-items: center; justify-content: start;"><label style="color:#94a3b8; font-weight:500; font-size:13px;">{t("generator.local_active")}</label></div>',
                unsafe_allow_html=True,
            )
            st.session_state.api_key = ""

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    with st.form("quiz_form"):
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:#94a3b8; font-size:14px; margin-bottom:12px;">{t("generator.upload_label")}</p>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload any supported file",
            type=list(ALLOWED_EXTENSIONS),
            label_visibility="collapsed",
            help=t("generator.upload_help")
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px;">', unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:#94a3b8; font-size:14px; margin-bottom:8px;">{t("generator.upload_help")}</p>',
            unsafe_allow_html=True,
        )
        text_input = st.text_area(
            "Paste text",
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
        if uploaded_file is not None:
            if not allowed_file(uploaded_file.name):
                st.error(t("generator.errors.unsupported_file"))
                return
            raw_content = uploaded_file.read()
            text_content = extract_text_from_file(raw_content, uploaded_file.name)
        else:
            text_content = ""

        if not text_content or not text_content.strip():
            text_content = text_input

        if not text_content or not text_content.strip():
            st.warning(t("generator.errors.no_input"))
            return

        try:
            with st.spinner(t("generator.spinner")):
                mode = st.session_state.mode
                api_key = st.session_state.api_key
                if mode == "AI-Powered (Gemini)":
                    questions = generate_ai_quiz(
                        text_content,
                        num_questions,
                        question_type=st.session_state.question_type,
                        difficulty=st.session_state.difficulty,
                        answer_length=st.session_state.answer_length,
                        api_key=api_key,
                    )
                elif mode == "Ollama (Local)":
                    questions = generate_ollama_quiz(
                        text_content,
                        num_questions,
                        question_type=st.session_state.question_type,
                        difficulty=st.session_state.difficulty,
                        answer_length=st.session_state.answer_length,
                    )
                else:
                    questions = generate_quiz(
                        text_content,
                        num_questions,
                        question_type=st.session_state.question_type,
                        difficulty=st.session_state.difficulty,
                        answer_length=st.session_state.answer_length,
                    )

            if not questions:
                st.error(t("generator.errors.generation_failed", error="No questions were generated."))
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


if st.session_state.show_quiz and st.session_state.questions:
    render_quiz()
else:
    render_generator()
