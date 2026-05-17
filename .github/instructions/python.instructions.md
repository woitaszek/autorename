---
description: "Python coding conventions for this project"
applyTo: "**/*.py"
---

# Python Conventions

## Language Level

- Python 3.12+ — use modern syntax throughout
- `X | None` not `Optional[X]`; `list[str]` not `List[str]`
- Do not import `List`, `Dict`, `Optional`, `Union`, or `Tuple` from `typing`

## Type Annotations

- All function parameters and return values must have type annotations
- Do not add `# type: ignore` without a specific error code and justifying comment

## Docstrings

- Google docstring convention
- Required on all public modules, classes, and functions
- Not required in test files (`tests/` is excluded from D rules)

## Style

- Ruff rules: E, F, I, UP, B, SIM, RUF, D1, D2, D4
- Line length: 88 characters (Ruff default)
- Import order enforced by Ruff's isort (I) — do not manually sort

## Testing

- pytest in `tests/`; run with `uv run pytest`
- Use fixtures for setup/teardown; mock external dependencies
- Catch specific exception types — no bare `except:`

## Security

- Validate all external inputs
- Use environment variables for sensitive configuration
- bandit scans `src/` (B101 skipped for assert allowance)
