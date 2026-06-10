# AGENTS.md for AI Quiz Generator

## Commands

### Lint & Typecheck
```bash
# No specific lint/typecheck configured for this project
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Notes
- Backend: Flask with google-genai for Gemini API
- Frontend: Vanilla JavaScript with fetch API
- The `/generate-quiz` endpoint expects POST requests with either a file or text input