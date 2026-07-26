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


def test_font_bytes_is_the_packaged_woff2() -> None:
    """font_bytes returns the shipped face, identified by the woff2 magic."""
    assert themes.font_bytes().startswith(b"wOF2")


def test_font_head_declares_the_face_at_the_supplied_url() -> None:
    """font_head wraps an @font-face naming the host's URL and the full weight range."""
    out = themes.font_head("/fonts/recursive.woff2")
    assert out.endswith("</style>")
    assert "@font-face" in out
    assert 'src: url("/fonts/recursive.woff2") format("woff2");' in out
    assert "font-weight: 300 1000;" in out


def test_font_head_preloads_the_face_from_the_same_url() -> None:
    """The fetch starts at head-parse, not when the face is first matched.

    The hint carries crossorigin because a font is fetched in anonymous CORS
    mode; a preload without it is a second, separate request.
    """
    out = themes.font_head("/fonts/recursive.woff2")
    assert out.startswith('<link rel="preload" href="/fonts/recursive.woff2"')
    assert 'as="font"' in out
    assert "crossorigin" in out


def test_the_face_never_swaps_after_paint() -> None:
    """optional is the one display value that cannot re-render text under a reader.

    A face that misses its block period sits out that page load rather than
    replacing the fallback mid-read; the next navigation has it cached.
    """
    assert "font-display: optional;" in themes.font_head("/f.woff2")
    assert "font-display: swap" not in themes.font_head("/f.woff2")


def test_family_tokens_lead_with_the_packaged_face() -> None:
    """The theme's family tokens name the packaged face before the system stacks."""
    css = themes.head("default")
    assert '--sb-font-family: "Recursive", ui-monospace' in css
    assert '--sb-font-family-prose: "Recursive", ui-sans-serif' in css
