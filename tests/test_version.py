"""Tests for package version metadata."""

from importlib.metadata import version

import switchboard_ui


def test_version_matches_distribution_metadata() -> None:
    """The package __version__ matches the installed distribution version.

    Guards the distribution-name/import-name split: __init__ looks up the
    distribution "switchboard-ui", not the import name "switchboard_ui".
    """
    assert switchboard_ui.__version__ == version("switchboard-ui")


def test_version_is_not_unknown() -> None:
    """The version resolves from installed metadata, not the fallback."""
    assert switchboard_ui.__version__ != "unknown"
