# Task runner. `just check` runs the full gate; CI calls the same target,
# so what passes locally is exactly what passes in CI.

# List available recipes.
default:
    @just --list

# Run the full check gate (lint, format, types, tests).
check: lint format-check typecheck test

# Lint with ruff.
lint:
    uv run ruff check .

# Verify formatting with ruff (does not modify files).
format-check:
    uv run ruff format --check .

# Apply ruff formatting.
format:
    uv run ruff format .

# Type-check the package with mypy (the authoritative gate).
typecheck:
    uv run mypy src

# Type-check with ty (Astral's pre-1.0 checker; supplementary to mypy).
typecheck-ty:
    uv run ty check src

# Run the test suite.
test:
    uv run pytest
