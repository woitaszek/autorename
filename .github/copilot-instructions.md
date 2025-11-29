# Copilot Instructions for autorename

## Environment Setup

This project uses `uv` for Python environment management.

### Python Commands
- Instead of using `python` or system Python, use: `uv run python`
- To run scripts: `uv run python <script.py>`
- To install packages: `uv pip install <package>`
- To run pytest: `uv run pytest`
- To run mypy: `uv run mypy`

### Key Project Information
- Python version: >=3.12
- Dev dependencies: pytest, pytest-mock, pytest-cov, ruff, mypy
- Main module: `src/autorename/autorename.py`
- Tests: `tests/test_autorename.py`
