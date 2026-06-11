# Contributing

Thank you for your interest in contributing to this project. Please follow these guidelines.

## Reporting Bugs
- Use the issue tracker.
- Include steps to reproduce, expected behavior, and actual behavior.
- Attach logs or screenshots if applicable.

## Development Setup
```bash
git clone https://code.swecha.org/karthik_7621/team-quiz.git
cd team-quiz

# It is recommended to use a virtual environment
python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Code Standards
- Follow PEP 8.
- Add tests for new behavior.
- Update docs when behavior changes.

## Pull Requests
- Keep changes focused and minimal.
- Reference related issues.
- Ensure CI passes before requesting review.
