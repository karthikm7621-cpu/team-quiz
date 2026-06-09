# AI Quiz Generator & Evaluator

A production-ready web application that generates quizzes from uploaded documents or text using Google Gemini AI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:
```bash
# Copy .env.example to .env and add your key
cp .env.example .env
# Edit .env to set GEMINI_API_KEY
```

3. Run the application:
```bash
python app.py
```

Visit `http://localhost:5000` to use the app.

## Features

- Upload PDF, PNG, JPG, TXT, or CSV files (max 16MB)
- Paste text directly into the input area
- Specify number of questions (1-20)
- Dark/light theme toggle
- Dynamic quiz interface with progress tracking
- Automatic local grading with detailed results

## File Structure

```
ai-quiz-generator/
├── app.py           # Flask backend with Gemini integration
├── requirements.txt # Python dependencies
├── .env.example     # Environment variable template
└── templates/
    └── index.html   # Single-page frontend
```