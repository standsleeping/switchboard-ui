"""Tests for the page model."""

import pytest

from switchboard_ui.model import REGIONS, Island


def test_regions_are_the_nine_named_areas() -> None:
    """The region tuple matches the 3x3 grid, row-major."""
    assert REGIONS == (
        "head-l",
        "head-c",
        "head-r",
        "body-l",
        "body-c",
        "body-r",
        "foot-l",
        "foot-c",
        "foot-r",
    )


def test_island_defaults_are_empty() -> None:
    """An island needs only a name; the rest default to empty."""
    island = Island(name="counter")
    assert island.props == {}
    assert island.publishes == ()
    assert island.subscribes == ()
    assert island.initial == ""


def test_island_rejects_non_json_props() -> None:
    """Non-serializable props fail at construction, not mid-render."""
    with pytest.raises(ValueError, match="non-JSON"):
        Island(name="bad", props={"x": object()})
