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

# Install base dependencies and developer tools
pip install -e .[dev]

# To use the Document Q&A feature, install the required extras.
# Note: `llama-cpp-python` might need special flags for GPU support during installation.
pip install -e .[qna]
```

## Code Standards
- Follow PEP 8.
- Add tests for new behavior.
- Update docs when behavior changes.

## Pull Requests
- Keep changes focused and minimal.
- Reference related issues.
- Ensure CI passes before requesting review.
