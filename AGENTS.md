# AGENTS.md - Project Commands

## 1. Install Dependencies
This command installs the project in editable mode along with all development tools. Run this once after cloning the repo or when `pyproject.toml` changes.
```bash
pip install -e .[dev]
```

## Set Up Environment (one-time)
Create `ai-quiz-generator/.env` from `.env.example` and add your API key:
```bash
# Copy .env.example to .env and edit
cp ai-quiz-generator/.env.example ai-quiz-generator/.env
# Then edit ai-quiz-generator/.env to add your GEMINI_API_KEY
```

## Run Flask Server
```bash
cd ai-quiz-generator; python app.py
```