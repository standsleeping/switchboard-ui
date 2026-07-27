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

# Type-check the workspace with mypy (the authoritative gate): core + theme src.
typecheck:
    uv run mypy src packages/switchboard-theme/src

# Type-check with ty (Astral's pre-1.0 checker; supplementary to mypy).
typecheck-ty:
    uv run ty check src packages/switchboard-theme/src

# Run the test suite: the core gate, then the theme gate (each its own coverage).
# `--directory` roots pytest in the member so it reads that member's config and
# collects only its tests (the two `tests` packages must not be collected together).
test:
    uv run pytest
    uv run --directory packages/switchboard-theme pytest

# Run the real-browser regression tests (needs `just browser-install` once).
# Deliberately outside `check`: those are the tests that need no browser, so a
# contributor without one still runs the same gate CI runs for them.
browser-test:
    uv run pytest tests_browser -p no:cacheprovider --no-header -q --no-cov

# Install the one engine the browser tests use.
browser-install:
    uv run playwright install --with-deps chromium
