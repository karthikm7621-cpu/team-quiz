import io
import os
import streamlit as st
from dotenv import load_dotenv
from quiz_generator import (
    allowed_file,
    extract_text_from_file,
    generate_quiz,
    client,
)

load_dotenv()

st.set_page_config(page_title='Team Quiz', page_icon='🧠', layout='centered')
st.title('Team Quiz Generator')
st.markdown(
    'Upload a file or paste text to generate multiple-choice quiz questions using Google Gemini.'
)

if client is None:
    st.error(
        'No API key found. Create a `.env` file with `GEMINI_API_KEY` or `GOOGLE_API_KEY`, then restart Streamlit.'
    )

uploaded_file = st.file_uploader(
    'Upload PDF, PNG, JPG, JPEG, TXT, or CSV',
    type=['pdf', 'png', 'jpg', 'jpeg', 'txt', 'csv'],
)
text_input = st.text_area('Or paste text here', height=200)
num_questions = st.number_input('Number of questions', min_value=1, max_value=20, value=10, step=1)

if st.button('Generate quiz'):
    if uploaded_file is None and not text_input.strip():
        st.warning('Please upload a file or paste some text before generating a quiz.')
    else:
        try:
            if uploaded_file is not None:
                if not allowed_file(uploaded_file.name):
                    st.error('Unsupported file type. Please upload PDF, PNG, JPG, JPEG, TXT, or CSV.')
                else:
                    raw_content = uploaded_file.read()
                    text_content = extract_text_from_file(raw_content, uploaded_file.name)
            else:
                text_content = text_input

            questions = generate_quiz(text_content, num_questions)

            st.success(f'Quiz generated successfully! {len(questions)} questions created.')
            for index, question in enumerate(questions, start=1):
                with st.expander(f'Question {index}'):
                    st.markdown(f"**Q{index}. {question['question']}**")
                    for option_index, option in enumerate(question['options']):
                        prefix = '✅' if option_index == question['correct_index'] else '▫️'
                        st.write(f'{prefix} {option}')
                    st.markdown(f"**Explanation:** {question['explanation']}")

        except Exception as exc:
            st.error(f'Could not generate quiz: {exc}')
