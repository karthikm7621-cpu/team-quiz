# AGENTS.md - Project Commands

## Install Dependencies (ai-quiz-generator)
```bash
pip install -r ai-quiz-generator/requirements.txt
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