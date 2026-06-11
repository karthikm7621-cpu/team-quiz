# Sample Feature: PDF Export Specification

## Overview
The application generates quizzes successfully within the UI. This feature will allow users to export their generated quiz, including questions and answers, directly to a formatted PDF document for offline use.

## User Story
- As a user, I want to export my generated quiz to a PDF so that I can print it or share it offline with my team.

## Technical Requirements
- Use `reportlab` or an equivalent PDF generation library.
- Add a new "Export to PDF" `st.download_button` to the Streamlit UI in `app.py`.
- The PDF generation logic will be encapsulated in a new function, `generate_pdf_report`, within `quiz_generator.py`.
- The PDF will be generated in-memory as a `bytes` object.

## Acceptance Criteria
- [ ] The app displays an "Export to PDF" button when a quiz is actively shown.
- [ ] Clicking the button downloads a valid `.pdf` file.
- [ ] The PDF contains the questions, options, and correct answers clearly formatted.
- [ ] Unit tests in `tests/test_quiz_generator.py` cover the `generate_pdf_report` function.

## Security & Compliance
- Ensure downloaded file names are sanitized to prevent path traversal issues.