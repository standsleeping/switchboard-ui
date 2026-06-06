"""Tests for the application layer (CLI)."""

from switchboard_ui.cli import main, parse_args


def test_parse_args_defaults() -> None:
    """Runtime defaults to inline and log level to WARNING."""
    parsed = parse_args([])
    assert parsed.runtime == "inline"
    assert parsed.log_level == "WARNING"


def test_parse_args_overrides() -> None:
    """Runtime and log level can be overridden."""
    parsed = parse_args(["--runtime", "linked", "--log-level", "DEBUG"])
    assert parsed.runtime == "linked"
    assert parsed.log_level == "DEBUG"


def test_main_prints_demo_document(capsys) -> None:
    """main renders the demo page to stdout and exits zero."""
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("<!doctype html>")
    assert 'data-island="counter"' in captured.out
