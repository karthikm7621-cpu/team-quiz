# User Manual

## Overview
This application generates quizzes from uploaded documents or pasted text.

## Getting Started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage
- Open the app in your browser.
- Upload a file (PDF, image, text, CSV) or paste content.
- Select question type, difficulty, and answer length.
- Click **Generate Quiz**.
- Answer questions and submit to see your score.

## Modes
- **Local**: Generates quizzes using built-in rules; no internet or API key required.
- **AI-Powered**: Generates quizzes via an AI backend; requires a valid API key.
