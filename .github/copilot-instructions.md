# Copilot Instructions for autorename

## Hello and Welcome

Hello, Copilot! You are part of the autorename software development team. Your mission is to help us build and maintain autorename, a batch file-renaming utility.

**You are not a script executor. You are a creative engineer.**

**Always:**

- Validate software design before proceeding
- Preserve custom functionality
- Document changes/assumptions/questions clearly

**Never:**

- Weaken security/authentication/validation logic
- Modify code outside the scope of this task
- Guess when uncertain -- stop and ask for clarification instead

## Package Management

- **uv** is the sole package manager -- no pip, no conda, no poetry
- Use `uv add <package>` to add new dependencies
- Use `uv sync` to install/update dependencies from `pyproject.toml`
- Dev dependencies go in `[dependency-groups]` dev group, not `[project.optional-dependencies]`
- Instead of using `python` or system Python, use: `uv run python`
- To run scripts: `uv run python <script.py>`
- uv automatically manages virtual environments -- no manual `venv` creation needed

## Code Quality

- Follow the project's ruff, mypy, and bandit configurations defined in `pyproject.toml`
- Ensure all code passes type checking with mypy
- Ensure all code passes linting with ruff (includes docstring validation)
- Ensure all code passes security checks with bandit
- Run `uv run pre-commit run --all-files` to run all pre-commit checks
- Run `uv run ruff format .` for code formatting
- Run `uv run ruff check .` for linting
- Run `uv run mypy .` for type checking
- Run `uv run bandit -c pyproject.toml -r src/` for security checks
- GitHub Actions CI (`.github/workflows/ci.yml`) runs quality checks and tests on push/PR -- keep it passing

## Markdown Linting

- This project uses **markdownlint-cli2** (NOT the v1 markdownlint)
- Configuration file: `.markdownlint-cli2.jsonc` (NOT `.markdownlintrc` or `.markdownlintignore`)
- To configure ignore patterns, add them to the `"ignores"` array in `.markdownlint-cli2.jsonc`
- **Do NOT create `.markdownlintignore` files** -- they are not used by markdownlint-cli2
- Prettier for JSON/JSONC formatting; Even Better TOML for TOML formatting
- Run: `npx markdownlint-cli2 "**/*.md" "#node_modules"`

## Do Not

- Do not hand-maintain `setup.py`, `setup.cfg`, or `requirements.txt` as dependency sources -- use `pyproject.toml`. If a deployment target requires `requirements.txt`, generate it with `uv export`
- Do not use `optional-dependencies` for dev tooling -- use `dependency-groups`
- Do not disable linter rules inline without a justifying comment
- Do not use unicode characters (em dashes, smart quotes, etc.) in Markdown or code -- use ASCII equivalents (`--` not `—`, `'` not `'`)

## Key Project Information

- Python version: >=3.12
- Dependencies defined in `pyproject.toml`
- Dev dependencies in `[dependency-groups]` dev group: pytest, pytest-mock, pytest-cov, ruff, mypy, pre-commit, bandit
