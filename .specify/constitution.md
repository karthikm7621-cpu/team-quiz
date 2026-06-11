# Constitution

## Core Principles
1. **Compliance**: This repository adheres to the AGPLv3 license and maintains high standards for open-source contributions.
2. **Quality**: All code must be typed (mypy), formatted (ruff), and covered by tests (pytest with coverage >80%).
3. **Security**: We proactively run Bandit and secret scanning on all commits.

## Workflow
- Use spec-driven development.
- Update `specs/` before changing core behavior.
- All changes must pass the CI pipeline before merging.