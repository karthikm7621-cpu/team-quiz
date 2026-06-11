# Quiz Generator Specification

## Overview
The application generates AI-powered multiple-choice quizzes from uploaded documents or pasted text.

## User story
- As a user, I can upload a supported file or paste text.
- I can choose between 1 and 20 questions.
- I can generate a quiz with 4 options per question and a correct answer index.

## Supported file types
- PDF
- PNG
- JPG
- JPEG
- TXT
- CSV

## Acceptance criteria
- The app loads with `streamlit run app.py`.
- If no API key is present, the app displays a helpful error.
- If input is missing, the app asks the user to provide text or a file.
- The generated quiz displays each question, options, and the correct answer.
