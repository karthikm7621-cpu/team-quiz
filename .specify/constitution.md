# Constitution

## Core Principles
1.  **Compliance**: This repository adheres to the AGPLv3 license and maintains high standards for open-source contributions.
2.  **Quality**: All code must be typed (Mypy), formatted (Ruff), and covered by tests (Pytest with coverage >85%).
3.  **Security**: We proactively run SAST (Semgrep) and dependency audits (pip-audit) on all commits.
4.  **Clarity**: Commits must follow the Conventional Commits specification to ensure a clear and automated changelog.

## Workflow
- **Spec-Driven Development**: All new features or significant refactors must begin with a specification file in the `specs/` directory.
- **CI First**: All changes must pass the full CI pipeline (`.gitlab-ci.yml`) before being considered for merge.
- **Review**: All merge requests require at least one approval from a project maintainer.