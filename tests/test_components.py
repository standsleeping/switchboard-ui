"""The segmented toggle factory, and the geometry-only contract for component CSS.

Two concerns. First, :func:`segmented` builds a correct mount descriptor: the
adapter name, the published topic, and an ``initial`` that is a complete,
accessible radio group at first paint — every option a server-rendered
``role="radio"``, exactly the chosen one checked, the checked one the single tab
stop (roving ``tabindex``), the group named for assistive tech, inert separators
between. Second, a component's structural CSS obeys the same contract as
``layout.css`` — geometry only, no box-spacing, no tokens but ``--sb-fit-*``, and
only ``.sb-*`` selectors — so paint never creeps into the structural layer. The
guard reuses the ``test_layout_css`` helpers and runs over every component sheet,
so a new component is covered the moment its CSS file lands.
"""

import re
from importlib.resources import files

import pytest

from switchboard_ui.components import (
    color_input,
    color_input_scripts,
    color_input_styles,
    color_picker,
    color_picker_scripts,
    color_picker_styles,
    popover,
    popover_scripts,
    popover_styles,
    segmented,
    segmented_scripts,
    segmented_styles,
)
from switchboard_ui.model import Island
from tests.htmlprobe import find
from tests.test_layout_css import _LAYOUT_PROPERTIES, _declared_properties, _selectors

_OPTIONS = (("overview", "Overview"), ("api", "API"), ("examples", "Examples"))
_LABEL = "View"


def _make(value: str = "overview") -> Island:
    """A segmented island over the standard options, selecting ``value``."""
    return segmented(topic="view:changed", options=_OPTIONS, value=value, label=_LABEL)


def test_segmented_builds_a_segmented_island() -> None:
    """The factory names the segmented adapter and publishes the chosen topic."""
    island = _make()
    assert isinstance(island, Island)
    assert island.name == "segmented"
    assert island.publishes == ("view:changed",)
    assert island.props == {"topic": "view:changed"}


def test_segmented_is_a_named_radio_group() -> None:
    """The control is a radio group with an accessible name and radio options."""
    island = _make()
    (group,) = find(island.initial, "div", role="radiogroup")
    assert group["aria-label"] == _LABEL
    radios = find(island.initial, "button", role="radio")
    assert [r["data-value"] for r in radios] == ["overview", "api", "examples"]


def test_segmented_server_renders_every_option_label() -> None:
    """Each option's visible label is present at first paint."""
    island = _make()
    assert "Overview" in island.initial
    assert "API" in island.initial
    assert "Examples" in island.initial


def test_segmented_checks_only_the_chosen_option() -> None:
    """Exactly the option whose value is ``value`` carries aria-checked=true."""
    island = _make(value="api")
    checked = [
        r["data-value"]
        for r in find(island.initial, "button", role="radio")
        if r.get("aria-checked") == "true"
    ]
    assert checked == ["api"]


def test_segmented_makes_the_checked_option_the_only_tab_stop() -> None:
    """Roving tabindex: the checked option is focusable, the rest arrow-only."""
    radios = find(_make(value="api").initial, "button", role="radio")
    tabindex = {r["data-value"]: r["tabindex"] for r in radios}
    assert tabindex == {"overview": "-1", "api": "0", "examples": "-1"}


def test_segmented_separates_options() -> None:
    """Inert dot separators sit between options, one fewer than the options."""
    separators = find(_make().initial, "span", **{"class": "sb-segmented-sep"})
    assert len(separators) == len(_OPTIONS) - 1
    assert all(s.get("aria-hidden") == "true" for s in separators)


def test_segmented_rejects_empty_options() -> None:
    """An empty option set fails at the authoring boundary, not at render."""
    with pytest.raises(ValueError, match="at least one option"):
        segmented(topic="view:changed", options=(), value="overview", label=_LABEL)


def test_segmented_rejects_blank_label() -> None:
    """A radio group needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        segmented(topic="view:changed", options=_OPTIONS, value="overview", label="")


def test_segmented_rejects_value_outside_options() -> None:
    """A selected value absent from the options fails where the call is written."""
    with pytest.raises(ValueError, match="not among options"):
        segmented(
            topic="view:changed", options=_OPTIONS, value="settings", label=_LABEL
        )


def test_segmented_scripts_returns_the_keyboard_radio_adapter() -> None:
    """The adapter ships, registers under the segmented name, and navigates by arrow key."""
    (adapter,) = segmented_scripts()
    assert 'register("segmented"' in adapter
    assert "ArrowRight" in adapter
    assert "aria-checked" in adapter


def test_segmented_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-segmented" in segmented_styles()


def test_color_input_builds_a_color_input_island() -> None:
    """The factory names the color-input adapter and publishes the chosen topic."""
    island = color_input(topic="token:accent", value="#5b4bd6", label="Accent")
    assert isinstance(island, Island)
    assert island.name == "color-input"
    assert island.publishes == ("token:accent",)
    assert island.props == {"topic": "token:accent"}


def test_color_input_server_renders_the_swatch_and_field() -> None:
    """The swatch shows the value and the named hex field holds it at first paint."""
    island = color_input(topic="token:accent", value="#5b4bd6", label="Accent")
    (swatch,) = find(island.initial, "span", **{"class": "sb-color-input-swatch"})
    assert "background:#5b4bd6" in swatch["style"]
    (field,) = find(island.initial, "input", **{"class": "sb-color-input-text"})
    assert field["value"] == "#5b4bd6"
    assert field["aria-label"] == "Accent"
    assert field["aria-invalid"] == "false"


def test_color_input_rejects_a_non_hex_value() -> None:
    """A value that is not a six-digit hex fails where the call is written."""
    with pytest.raises(ValueError, match="six-digit hex"):
        color_input(topic="token:accent", value="rebeccapurple", label="Accent")


def test_color_input_rejects_a_short_hex_value() -> None:
    """A three-digit hex is rejected: the v0 field accepts only ``#rrggbb``."""
    with pytest.raises(ValueError, match="six-digit hex"):
        color_input(topic="token:accent", value="#abc", label="Accent")


def test_color_input_rejects_a_blank_label() -> None:
    """The field needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        color_input(topic="token:accent", value="#5b4bd6", label="")


def test_color_input_scripts_returns_the_adapter() -> None:
    """The adapter ships, registers under the color-input name, and validates hex."""
    (adapter,) = color_input_scripts()
    assert 'register("color-input"' in adapter
    assert "aria-invalid" in adapter


def test_color_input_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-color-input" in color_input_styles()


def test_color_picker_builds_a_color_picker_island() -> None:
    """The factory names the color-picker adapter and publishes the chosen topic."""
    island = color_picker(topic="token:accent", value="#5b4bd6", label="Accent")
    assert isinstance(island, Island)
    assert island.name == "color-picker"
    assert island.publishes == ("token:accent",)
    assert island.props == {"topic": "token:accent"}


def test_color_picker_renders_swatch_spectrum_and_field() -> None:
    """The chip trigger holds the live colour; the spectrum and hex field are present."""
    html = color_picker(topic="token:accent", value="#5b4bd6", label="Accent").initial
    swatch = [
        b
        for b in find(html, "button")
        if "sb-color-picker-swatch" in b.get("class", "")
    ]
    assert len(swatch) == 1
    assert "background:#5b4bd6" in swatch[0]["style"]
    assert swatch[0]["aria-label"] == "Accent"
    sliders = {s["class"]: s for s in find(html, "div", role="slider")}
    assert "sb-color-picker-area" in sliders
    assert sliders["sb-color-picker-hue"]["aria-valuemin"] == "0"
    assert sliders["sb-color-picker-hue"]["aria-valuemax"] == "360"
    (field,) = find(html, "input", **{"class": "sb-color-input-text"})
    assert field["value"] == "#5b4bd6"


def test_color_picker_shares_the_hex_field_with_the_color_input() -> None:
    """Both colour controls render the identical hex field (one shared authoring)."""
    field = '<input class="sb-color-input-text" type="text" value="#5b4bd6"'
    assert field in color_input(topic="t", value="#5b4bd6", label="Accent").initial
    assert field in color_picker(topic="t", value="#5b4bd6", label="Accent").initial


def test_color_picker_rejects_a_non_hex_value() -> None:
    """A non-hex value fails at the authoring boundary, not at render."""
    with pytest.raises(ValueError, match="six-digit hex"):
        color_picker(topic="t", value="nope", label="Accent")


def test_color_picker_rejects_a_blank_label() -> None:
    """The control needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        color_picker(topic="t", value="#5b4bd6", label="")


def test_color_picker_scripts_returns_the_adapter() -> None:
    """The picker ships its own adapter; the popover adapter is paired separately."""
    (adapter,) = color_picker_scripts()
    assert 'register("color-picker"' in adapter
    assert "hsvToRgb" in adapter


def test_color_picker_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-color-picker" in color_picker_styles()


def _popover(**overrides: object) -> Island:
    """A popover island over standard trigger/panel/id, with optional overrides."""
    kwargs: dict[str, object] = {
        "trigger": "<span>open</span>",
        "panel": "<p>contents</p>",
        "label": "Settings",
        "panel_id": "settings-pop",
    }
    kwargs.update(overrides)
    return popover(**kwargs)  # type: ignore[arg-type]


def test_popover_builds_a_popover_island() -> None:
    """The factory names the popover adapter; open_topic drives what it publishes."""
    quiet = _popover()
    assert isinstance(quiet, Island)
    assert quiet.name == "popover"
    assert quiet.publishes == ()
    assert quiet.props == {}
    loud = _popover(open_topic="picker:open")
    assert loud.publishes == ("picker:open",)
    assert loud.props == {"topic": "picker:open"}


def test_popover_wires_the_trigger_to_the_panel() -> None:
    """The trigger's popovertarget/aria-controls match the panel id; both are present."""
    island = _popover()
    (trigger,) = find(island.initial, "button", **{"class": "sb-popover-trigger"})
    assert trigger["popovertarget"] == "settings-pop"
    assert trigger["aria-controls"] == "settings-pop"
    assert trigger["aria-expanded"] == "false"
    assert trigger["aria-haspopup"] == "dialog"
    (panel,) = find(island.initial, "div", **{"class": "sb-popover-panel"})
    assert panel["id"] == "settings-pop"
    assert panel["popover"] == "auto"
    assert panel["aria-label"] == "Settings"


def test_popover_embeds_the_supplied_fragments() -> None:
    """The caller's trigger and panel HTML are embedded verbatim."""
    island = _popover(trigger="<span>pick</span>", panel="<p>body</p>")
    assert "<span>pick</span>" in island.initial
    assert "<p>body</p>" in island.initial


def test_popover_rejects_a_blank_label() -> None:
    """The panel needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        _popover(label="")


def test_popover_rejects_an_invalid_panel_id() -> None:
    """A malformed id would break the trigger/panel wiring; reject it up front."""
    with pytest.raises(ValueError, match="valid HTML id"):
        _popover(panel_id="2 bad id")


def test_popover_rejects_empty_trigger_or_panel() -> None:
    """An empty trigger or panel is meaningless; reject both at the boundary."""
    with pytest.raises(ValueError, match="trigger content"):
        _popover(trigger="")
    with pytest.raises(ValueError, match="panel content"):
        _popover(panel="")


def test_popover_scripts_returns_the_adapter() -> None:
    """The adapter ships, registers under the popover name, and syncs open state."""
    (adapter,) = popover_scripts()
    assert 'register("popover"' in adapter
    assert "toggle" in adapter
    assert "aria-expanded" in adapter


def test_popover_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-popover" in popover_styles()


def _component_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every component's structural CSS (not ``layout.css``)."""
    static = files("switchboard_ui") / "static"
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in static.iterdir()
        if path.name.endswith(".css") and path.name != "layout.css"
    ]


def test_component_css_declares_only_geometry() -> None:
    """A component sheet declares only layout properties — no paint, no box-spacing."""
    for name, css in _component_sheets():
        non_layout = _declared_properties(css) - _LAYOUT_PROPERTIES
        assert not non_layout, (
            f"{name} declares non-layout properties: {sorted(non_layout)}"
        )


def test_component_css_selects_only_sb_classes() -> None:
    """A component sheet styles only its own ``.sb-*`` hooks, never host elements."""
    for name, css in _component_sheets():
        foreign = [s for s in _selectors(css) if not s.startswith(".sb-")]
        assert not foreign, f"{name} selects non-sb elements: {foreign}"


def test_component_css_carries_no_paint_tokens_or_magic_numbers() -> None:
    """A component sheet stays token-free (only ``--sb-fit-*``) with no bare length."""
    for name, css in _component_sheets():
        body = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        assert "light-dark(" not in body, (
            f"{name} consumes theming (a cause, not structure)"
        )
        tokens = re.findall(r"var\(\s*(--[\w-]+)", body)
        non_contract = sorted({t for t in tokens if not t.startswith("--sb-fit-")})
        assert not non_contract, f"{name} references non-contract tokens {non_contract}"
        stripped = re.sub(r"var\([^)]*\)", "", body)
        bodies = " ".join(re.findall(r"\{([^{}]*)\}", stripped))
        lengths = re.findall(r"(\d*\.?\d+)(px|rem|em|cm|mm|pt|pc|in)\b", bodies)
        magic = sorted({f"{n}{unit}" for n, unit in lengths if float(n) != 0})
        assert not magic, (
            f"{name} has bare absolute lengths {magic}; use a token or keyword"
        )
