import streamlit as st
from dotenv import load_dotenv

from quiz_generator import (
    allowed_file,
    extract_text_from_file,
    generate_quiz,
    generate_ai_quiz,
    ALLOWED_EXTENSIONS,
)

load_dotenv()

st.set_page_config(
    page_title="Team Quiz",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
    st.session_state.question_type = "MCQ"
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Basic"
if "answer_length" not in st.session_state:
    st.session_state.answer_length = "1-line"
if "mode" not in st.session_state:
    st.session_state.mode = "Local"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

.main-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 32px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    margin-bottom: 24px;
}

.question-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    margin-bottom: 20px;
}

.header-section {
    text-align: center;
    padding: 30px 20px;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2));
    border-radius: 24px;
    margin-bottom: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.badge-mcq {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    display: inline-block;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.badge-very-short {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    display: inline-block;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.badge-short {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    display: inline-block;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.badge-long {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    color: white;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    display: inline-block;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.badge-essay {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    display: inline-block;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.points-badge {
    background: rgba(255, 255, 255, 0.15);
    color: #e2e8f0;
    padding: 8px 16px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 14px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.stButton>button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
    background: linear-gradient(135deg, #818cf8, #a78bfa);
}

.stButton>button:active {
    transform: translateY(0);
}

.submit-btn>button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
}

.submit-btn>button:hover {
    background: linear-gradient(135deg, #34d399, #10b981) !important;
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.5) !important;
}

.answer-box {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
}

.correct-answer {
    background: rgba(16, 185, 129, 0.15);
    border-left: 4px solid #10b981;
    padding: 12px 16px;
    border-radius: 8px;
    margin-top: 8px;
}

.score-card {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2));
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    margin-top: 20px;
}

.title-gradient {
    background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    font-size: 3rem;
    letter-spacing: -1px;
}

.subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 400;
    margin-top: 8px;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
    border-radius: 999px;
}

.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    color: white;
}

.stNumberInput > div > div > input {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    color: white;
}

.stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    color: white;
}

.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    color: white;
}

.upload-zone {
    background: rgba(255, 255, 255, 0.05);
    border: 2px dashed rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    transition: all 0.3s ease;
}

.upload-zone:hover {
    border-color: rgba(99, 102, 241, 0.5);
    background: rgba(99, 102, 241, 0.05);
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    margin: 24px 0;
}

.footer {
    text-align: center;
    color: #64748b;
    font-size: 13px;
    margin-top: 40px;
    padding: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)


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
    st.markdown('<h2 class="title-gradient">🧠 Team Quiz</h2>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="question-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f'<div class="points-badge">🏆 {points} Mark{"s" if points > 1 else ""}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(type_badge(q_type), unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#e2e8f0; font-size:16px; font-weight:500;">Q{current_index + 1}. {q["question"]}</p>',
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
                f'<div style="background:rgba(255,255,255,0.08); padding:12px; border-radius:10px; margin:8px 0;"><strong>Your answer:</strong> {answer_display}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="answer-box"><strong>✅ Answer:</strong><br>'
            + str(q["answer"]).replace("\n", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"💡 {q['explanation']}")
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
                st.caption("👆 Select an answer to continue")
        elif q_type in ("Very Short Answer", "Short Answer"):
            user_input = st.text_input(
                "Type your answer",
                key=f"short_{current_index}",
                label_visibility="collapsed",
                placeholder="Type your answer here...",
            )
            if st.button(
                "Submit Answer",
                key=f"submit_short_{current_index}",
                use_container_width=True,
            ):
                st.session_state.user_answers[current_index] = user_input
                st.rerun()
            if user_answers[current_index] is None:
                st.caption("✍️ Type your answer and click Submit Answer")
        else:
            user_input = st.text_area(
                "Type your answer",
                key=f"long_{current_index}",
                label_visibility="collapsed",
                height=150,
                placeholder="Type your detailed answer here...",
            )
            if st.button(
                "Submit Answer",
                key=f"submit_long_{current_index}",
                use_container_width=True,
            ):
                st.session_state.user_answers[current_index] = user_input
                st.rerun()
            if user_answers[current_index] is None:
                st.caption("✍️ Type your answer and click Submit Answer")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div style="display:flex; gap:12px; margin-top:20px;">', unsafe_allow_html=True
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if current_index > 0 and st.button("⬅️ Previous", use_container_width=True):
            st.session_state.current_index -= 1
            st.rerun()
    with col2:
        if current_index < len(questions) - 1 and st.button(
            "Next ➡️", use_container_width=True
        ):
            st.session_state.current_index += 1
            st.rerun()
    with col3:
        if not submitted and st.button("📝 Submit Quiz", use_container_width=True):
            unanswered = [
                i + 1
                for i, a in enumerate(user_answers)
                if a is None or (isinstance(a, str) and a.strip() == "")
            ]
            if unanswered:
                st.warning(f"⚠️ Unanswered question(s): {unanswered}")
            else:
                st.session_state.quiz_submitted = True
                st.rerun()
    with col4:
        if st.button(
            "👁️ Show Answers" if not show_answers else "🙈 Hide Answers",
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
            f'<h2 style="color:#10b981; margin:0;">🏆 Score: {score} / {max_score}</h2>',
            unsafe_allow_html=True,
        )
        percentage = int((score / max_score) * 100) if max_score > 0 else 0
        st.markdown(
            f'<p style="color:#94a3b8; margin-top:8px;">{percentage}% correct</p>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🔄 Generate New Quiz", use_container_width=True):
            reset_quiz()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_generator() -> None:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    st.markdown(
        '<h1 class="title-gradient">🧠 Team Quiz Generator</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="subtitle">Upload any document or paste text to generate stunning quizzes</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            '<label style="color:#e2e8f0; font-weight:500; font-size:13px;">📋 Question Type</label>',
            unsafe_allow_html=True,
        )
        question_type = st.selectbox(
            "Question Type",
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
            '<label style="color:#e2e8f0; font-weight:500; font-size:13px;">⚡ Difficulty</label>',
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
            '<label style="color:#e2e8f0; font-weight:500; font-size:13px;">📏 Answer Length</label>',
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
            '<label style="color:#e2e8f0; font-weight:500; font-size:13px;">🔢 Questions</label>',
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
            '<label style="color:#e2e8f0; font-weight:500; font-size:13px;">🧠 Mode</label>',
            unsafe_allow_html=True,
        )
        mode = st.selectbox(
            "Mode",
            ["Local", "AI-Powered (Gemini)"],
            index=["Local", "AI-Powered (Gemini)"].index(st.session_state.mode),
            label_visibility="collapsed",
        )
        st.session_state.mode = mode
    with col2:
        if mode == "AI-Powered (Gemini)":
            st.markdown(
                '<label style="color:#e2e8f0; font-weight:500; font-size:13px;">🔑 Gemini API Key</label>',
                unsafe_allow_html=True,
            )
            api_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.api_key,
                type="password",
                label_visibility="collapsed",
                placeholder="Paste your Gemini API key here",
            )
            st.session_state.api_key = api_key
        else:
            st.markdown(
                '<label style="color:#94a3b8; font-weight:500; font-size:13px;">✅ Local mode active</label>',
                unsafe_allow_html=True,
            )
            st.session_state.api_key = ""

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    with st.form("quiz_form"):
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        st.markdown(
            '<p style="color:#94a3b8; font-size:14px; margin-bottom:12px;">📁 Upload your document</p>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload any supported file",
            type=list(ALLOWED_EXTENSIONS),
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px;">', unsafe_allow_html=True)
        st.markdown(
            '<p style="color:#94a3b8; font-size:14px; margin-bottom:8px;">✏️ Or paste text directly</p>',
            unsafe_allow_html=True,
        )
        text_input = st.text_area(
            "Paste your text here",
            height=150,
            label_visibility="collapsed",
            placeholder="Paste your study material here...",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Generate Quiz", use_container_width=True
            )

    if submitted:
        if uploaded_file is not None:
            if not allowed_file(uploaded_file.name):
                st.error("❌ Unsupported file type. Please upload a supported file.")
                return
            raw_content = uploaded_file.read()
            text_content = extract_text_from_file(raw_content, uploaded_file.name)
        else:
            text_content = ""

        if not text_content or not text_content.strip():
            text_content = text_input

        if not text_content or not text_content.strip():
            st.warning(
                "⚠️ Please upload a valid file or enter text so quiz questions can be generated."
            )
            return

        try:
            with st.spinner("✨ Generating your quiz..."):
                mode = st.session_state.mode
                if mode == "AI-Powered (Gemini)":
                    questions = generate_ai_quiz(
                        text_content,
                        num_questions,
                        question_type=st.session_state.question_type,
                        difficulty=st.session_state.difficulty,
                        answer_length=st.session_state.answer_length,
                        api_key=st.session_state.api_key,
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
            st.error(f"❌ Could not generate quiz: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="footer">Made with ❤️ using Streamlit</div>', unsafe_allow_html=True
    )


if st.session_state.show_quiz and st.session_state.questions:
    render_quiz()
else:
    render_generator()
