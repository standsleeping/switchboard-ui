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

# Regenerate everything rendered from the theme's token registry: the theme
# stylesheet and the token reference page. `just check` fails when either has
# drifted, so run this after editing tokens.py.
generate:
    uv run python -c "import pathlib, switchboard_theme; from switchboard_theme.tokens import render_css; pathlib.Path(switchboard_theme.__file__).parent.joinpath('static', 'default.css').write_text(render_css(), encoding='utf-8')"
    uv run python -c "import pathlib; from switchboard_theme.reference import render_reference; pathlib.Path('docs', 'reference', 'tokens.md').write_text(render_reference(), encoding='utf-8')"

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

# Run the real-browser regression tests in all three engines (needs
# `just browser-install` once). Deliberately outside `check`: those are the
# tests that need no browser, so a contributor without one still runs the same
# gate CI runs for them. A failing case leaves its screenshot and trace under
# test-results/, which matters most for the cases that only run under classic
# scrollbars: those never fail on an overlay-scrollbar machine, so the
# artifact is the whole reproduction.
browser-test:
    uv run pytest tests_browser -p no:cacheprovider --no-header -q --no-cov --browser chromium --browser firefox --browser webkit --screenshot only-on-failure --tracing retain-on-failure --output test-results

# Run the classic-scrollbar cases once more, headed: a real widget layer can
# present classic bars that headless rendering never does, and the Firefox and
# WebKit gutter verdicts only exist there. On Linux this needs a display
# server (CI wraps it in xvfb-run); the GTK variable reaches the headed GTK
# builds and is inert everywhere else. The probe still decides per engine.
classic-test $GTK_OVERLAY_SCROLLING="0":
    uv run pytest tests_browser/test_classic_scrollbars.py -p no:cacheprovider --no-header -q --no-cov --browser chromium --browser firefox --browser webkit --headed --screenshot only-on-failure --output test-results

# Install the three engines the browser tests run in.
browser-install:
    uv run playwright install --with-deps chromium firefox webkit

# Run the real-Safari regression tests (macOS only; needs `safaridriver
# --enable` once). Safari opens real windows while these run: safaridriver has
# no headless mode, which is also why this is a separate target rather than a
# fourth engine in `browser-test`.
safari-test:
    uv run --group safari pytest tests_safari -p no:cacheprovider --no-header -q --no-cov
