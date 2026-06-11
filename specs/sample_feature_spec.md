# Sample Feature: PDF Export Specification

## Overview
The application currently generates quizzes successfully. This feature will allow users to export their generated quizzes directly to a formatted PDF document.

## User Story
- As a user, I want to export my generated quiz to a PDF so that I can print it or share it offline with my team.

## Technical Requirements
- Use `reportlab` or an equivalent PDF generation library.
- Add a new "Export to PDF" button to the Streamlit UI in `app.py`.
- Generate the PDF in-memory and provide a Streamlit download button.

## Acceptance Criteria
- [ ] The app displays an "Export to PDF" button when a quiz is actively shown.
- [ ] Clicking the button downloads a valid `.pdf` file.
- [ ] The PDF contains the questions, options, and correct answers clearly formatted.
- [ ] Unit tests cover the PDF generation logic.

## Security & Compliance
- Ensure downloaded file names are sanitized to prevent path traversal issues.