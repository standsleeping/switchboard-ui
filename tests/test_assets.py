"""Tests for the static-asset reader."""

from switchboard_ui.assets import read_static


def test_read_static_returns_asset_text() -> None:
    """A packaged asset is read as text."""
    assert ".sb-frame" in read_static("layout.css")


def test_read_static_is_memoized() -> None:
    """Repeated reads return the same cached object."""
    assert read_static("switchboard.js") is read_static("switchboard.js")
