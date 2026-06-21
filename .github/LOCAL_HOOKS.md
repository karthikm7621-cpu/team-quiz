# Local Git Hooks

This project uses the standard `pre-commit` framework for local quality gates.

## One-time setup

Run these commands from the repository root:

```bash
pip install -e .[dev]
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
```

## Running checks manually

Run all pre-commit checks:

```bash
pre-commit run --all-files
```

Run pre-push checks, including tests and dependency audit:

```bash
pre-commit run --hook-stage pre-push --all-files
```

## What the hooks check

- Python formatting and linting with Ruff.
- Python static typing with mypy.
- Dead code detection with Vulture.
- Python security scanning with Bandit.
- Python dependency auditing with pip-audit.
- Frontend and documentation formatting with Prettier.
- Unit tests with `python -m pytest` before push.
