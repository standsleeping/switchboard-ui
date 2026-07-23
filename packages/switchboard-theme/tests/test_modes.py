"""The mode switch ships the theme's two mode axes as a host-ready control."""

from switchboard_theme.modes import (
    mode_stamp_head,
    mode_state,
    mode_switch,
    mode_switch_scripts,
    mode_switch_styles,
)
from switchboard_ui import render_island

from .htmlprobe import find


def test_mode_switch_offers_both_axes_at_their_defaults() -> None:
    """The panel's toggles cover scheme (Auto selected) and density (Comfortable)."""
    html = render_island(mode_switch())
    checked = find(html, "button", **{"aria-checked": "true"})
    assert [b["data-value"] for b in checked] == ["auto", "comfortable"]


def test_mode_toggles_publish_input_and_follow_sync() -> None:
    """Each nested toggle publishes on its :changed topic and listens on its :sync."""
    html = render_island(mode_switch())
    for axis in ("scheme", "density"):
        toggle = find(
            html, "div", **{"data-island": "segmented", "data-pub": f"{axis}:changed"}
        )
        assert len(toggle) == 1
        assert toggle[0]["data-sub"] == f"{axis}:sync"


def test_mode_switch_is_an_anchored_popover_in_the_rail() -> None:
    """The control is a quiet trigger opening a native popover panel (top layer),
    so the option set never has to fit the fixed head-r cell width."""
    island = mode_switch()
    html = render_island(island)
    trigger = find(html, "button", popovertarget="sb-modes")
    assert len(trigger) == 1
    assert "sb-modes-trigger" in trigger[0]["class"]
    panel = find(html, "div", id="sb-modes")
    assert len(panel) == 1
    assert panel[0].get("popover") is not None


def test_mode_state_closes_the_wiring() -> None:
    """The applier subscribes both input topics and publishes both sync topics."""
    applier = mode_state()
    assert applier.name == "mode-state"
    assert applier.subscribes == ("scheme:changed", "density:changed")
    assert applier.publishes == ("scheme:sync", "density:sync")
    assert applier.initial == ""  # invisible wiring, no first-paint footprint


def test_mode_state_adapter_touches_only_the_named_modes() -> None:
    """The applier and the pre-paint stamp write only the named mode values."""
    (script,) = mode_switch_scripts()
    assert 'register("mode-state"' in script
    for value in ("light", "dark", "compact", "spacious"):
        assert f'"{value}"' in script
    stamp = mode_stamp_head()
    assert stamp.startswith("<script>")
    for key in ("sb-scheme", "sb-density"):
        assert key in script and key in stamp


def test_mode_switch_styles_place_the_trigger_in_the_rail() -> None:
    """The head-r cell rows its content and the trigger reads as quiet rail chrome."""
    css = mode_switch_styles()
    assert ".sb-head-r" in css
    assert ".sb-modes-trigger" in css
    assert ".sb-modes-panel" in css
