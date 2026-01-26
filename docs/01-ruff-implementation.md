# Ruff Implementation Plan

This document outlines the plan for implementing Ruff as the code formatting and linting tool for the NestStay API project.

## Overview

Ruff is an extremely fast Python linter and formatter written in Rust. It replaces multiple tools (Black, Flake8, isort, and others) with a single, unified solution.

## Phase 1: Installation

```bash
# Add ruff as a dev dependency
uv add --dev ruff
```

## Phase 2: Configuration

Add the following configuration to `pyproject.toml`:

```toml
[tool.ruff]
# Target Python 3.12
target-version = "py312"

# Same as Black
line-length = 88

# Exclude common directories
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "database/alembic/versions",  # Auto-generated migrations
]

[tool.ruff.lint]
select = [
    # Core
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort (import sorting)
    "UP",     # pyupgrade (modern Python syntax)

    # Code quality
    "B",      # flake8-bugbear (common bugs)
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking (optimize imports)

    # FastAPI/Pydantic specific
    "FA",     # flake8-future-annotations
    "PIE",    # flake8-pie (misc lints)
    "RUF",    # Ruff-specific rules

    # Security
    "S",      # flake8-bandit (security)

    # Async (important for FastAPI)
    "ASYNC",  # flake8-async
]

ignore = [
    "S101",   # Allow assert (useful in tests)
    "B008",   # Allow function calls in default args (Depends() pattern)
]

[tool.ruff.lint.per-file-ignores]
# Tests can have more relaxed rules
"tests/**/*.py" = ["S101", "PLR2004"]
# Alembic migrations are auto-generated
"database/alembic/**/*.py" = ["E501", "F401"]

[tool.ruff.lint.isort]
known-first-party = ["app", "database", "config"]
force-single-line = false
combine-as-imports = true

[tool.ruff.format]
# Use double quotes (consistent with Black)
quote-style = "double"
# Indent with spaces
indent-style = "space"
# Respect magic trailing commas
skip-magic-trailing-comma = false
# Auto-detect line endings
line-ending = "auto"
# Format docstrings
docstring-code-format = true
```

## Phase 3: Makefile Integration

Add these targets to the `Makefile`:

```makefile
# Linting and formatting
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# Combined check (for CI)
check:
	uv run ruff format --check .
	uv run ruff check .
```

## Phase 4: Initial Rollout Steps

1. **Install Ruff**
   ```bash
   uv add --dev ruff
   ```

2. **Add configuration** to `pyproject.toml`

3. **Run format check** to see what would change
   ```bash
   uv run ruff format --diff .
   ```

4. **Apply formatting**
   ```bash
   uv run ruff format .
   ```

5. **Run linter** to identify issues
   ```bash
   uv run ruff check .
   ```

6. **Auto-fix safe issues**
   ```bash
   uv run ruff check --fix .
   ```

7. **Review and manually fix** remaining issues

8. **Commit** all changes with a message like:
   ```
   chore: add ruff linting and formatting configuration
   ```

## Phase 5: Optional - Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Install:
```bash
uv add --dev pre-commit
uv run pre-commit install
```

## Rule Categories Explained

| Rule Set | Why It's Useful for FastAPI/SQLModel |
|----------|--------------------------------------|
| `B008` ignored | Allows `Depends()` in function defaults |
| `TCH` | Moves type-only imports to `TYPE_CHECKING` blocks, reducing runtime overhead |
| `ASYNC` | Catches async/await mistakes in FastAPI async endpoints |
| `S` (bandit) | Security checks for SQL injection, hardcoded secrets |
| `UP` | Ensures modern Python 3.12+ syntax |
| `FA` | Future annotations for Pydantic model forward references |
| `I` (isort) | Consistent import ordering across all files |

## Common Commands

| Command | Description |
|---------|-------------|
| `make lint` | Check for linting issues |
| `make lint-fix` | Auto-fix linting issues |
| `make format` | Format all files |
| `make format-check` | Check formatting without changes |
| `make check` | Run all checks (for CI) |

## IDE Integration

### VS Code

Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) and add to `.vscode/settings.json`:

```json
{
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    }
}
```

### PyCharm

Use the [Ruff plugin](https://plugins.jetbrains.com/plugin/20574-ruff) from the JetBrains marketplace.
