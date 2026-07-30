"""Tests for the static-asset reader."""

from importlib.resources import files

from switchboard_ui.assets import read_asset_bytes, read_static


def test_read_static_returns_asset_text() -> None:
    """A packaged asset is read as text."""
    assert ".sb-frame" in read_static("layout.css")


def test_read_static_is_memoized() -> None:
    """Repeated reads return the same cached object."""
    assert read_static("switchboard.js") is read_static("switchboard.js")


def test_read_asset_bytes_returns_asset_bytes() -> None:
    """A packaged asset is read as bytes, uninterpreted."""
    text = read_static("layout.css")
    data = read_asset_bytes("switchboard_ui", "layout.css")
    assert data == text.encode()


def test_no_shipped_script_requests_smooth_scrolling() -> None:
    """The adapters position instantly; no script passes a smooth behaviour.

    Restoration, reveal, and the copy actions all set positions directly, so a
    reduced-motion reader needs nothing disabled: there is no animation to
    disable. Checked across every shipped script so a new adapter cannot
    reintroduce one quietly.
    """
    static = files("switchboard_ui") / "static"
    scripts = [entry for entry in static.iterdir() if entry.name.endswith(".js")]
    assert scripts, "precondition: the package must ship scripts to audit"
    for entry in scripts:
        assert "smooth" not in entry.read_text(), entry.name
