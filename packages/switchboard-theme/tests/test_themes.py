"""The opt-in theme layer: a ``<style>`` block delivered through ``extra_head``."""

import pytest

import switchboard_theme as themes
from switchboard_ui import render_document, three_column


def test_head_returns_a_style_block_carrying_the_tokens() -> None:
    """themes.head wraps the theme CSS in a <style> carrying the --sb-* tokens."""
    out = themes.head("default")
    assert out.startswith("<style>")
    assert out.endswith("</style>")
    assert "--sb-color-bg" in out
    assert "color-scheme: light dark" in out


def test_head_defaults_to_the_default_theme() -> None:
    """The default argument selects the 'default' theme."""
    assert themes.head() == themes.head("default")


def test_head_rejects_an_unknown_theme_at_the_call() -> None:
    """An unknown theme name fails where it is supplied, naming it."""
    with pytest.raises(ValueError, match="unknown theme 'midnight'"):
        themes.head("midnight")


def test_every_shipped_theme_resolves_to_a_style_block() -> None:
    """Each name in THEMES reads its CSS and wraps it for injection."""
    for name in themes.THEMES:
        assert themes.head(name).startswith("<style>")


def test_a_theme_enters_a_page_through_extra_head() -> None:
    """A themed page carries the theme's tokens in its head."""
    html = render_document(three_column(title="t"), extra_head=themes.head("default"))
    assert "<style>" in html
    assert "--sb-color-accent" in html
