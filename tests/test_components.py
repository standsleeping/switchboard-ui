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
    ArmBinding,
    ValueBinding,
    color_input,
    color_input_scripts,
    color_input_styles,
    color_picker,
    color_picker_scripts,
    color_picker_styles,
    popover,
    popover_scripts,
    popover_styles,
    preview,
    preview_styles,
    segmented,
    segmented_scripts,
    segmented_styles,
    slider,
    slider_scripts,
    slider_styles,
    theme_export,
    theme_export_scripts,
    theme_export_styles,
    theme_state,
    theme_state_scripts,
    value_field,
    value_field_scripts,
    value_field_styles,
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


def test_segmented_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the segmented name (the runtime's dispatch key)."""
    (adapter,) = segmented_scripts()
    assert 'register("segmented"' in adapter


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
    """The adapter ships and registers under the color-input name (the runtime's dispatch key)."""
    (adapter,) = color_input_scripts()
    assert 'register("color-input"' in adapter


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
    """The picker ships exactly one adapter, registered under the color-picker name (popover is paired separately)."""
    (adapter,) = color_picker_scripts()
    assert 'register("color-picker"' in adapter


def test_color_picker_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-color-picker" in color_picker_styles()


def test_slider_builds_a_slider_island() -> None:
    """The factory names the slider adapter and publishes the chosen topic."""
    island = slider(
        topic="weight:changed", min=200, max=900, step=10, value=400, label="Weight"
    )
    assert isinstance(island, Island)
    assert island.name == "slider"
    assert island.publishes == ("weight:changed",)
    assert island.props == {"topic": "weight:changed", "integer": True}


def test_slider_server_renders_a_named_range_at_value() -> None:
    """The range carries its bounds, step, value, and accessible name at first paint."""
    island = slider(
        topic="weight:changed", min=200, max=900, step=10, value=400, label="Weight"
    )
    (field,) = find(island.initial, "input", **{"class": "sb-slider-input"})
    assert field["type"] == "range"
    assert field["min"] == "200"
    assert field["max"] == "900"
    assert field["step"] == "10"
    assert field["value"] == "400"
    assert field["aria-label"] == "Weight"


def test_slider_shows_a_decorative_readout_by_default() -> None:
    """The readout mirrors the value and is hidden from assistive tech (the range speaks)."""
    island = slider(topic="t", min=0, max=10, value=4, label="N")
    (readout,) = find(island.initial, "span", **{"class": "sb-slider-value"})
    assert readout["aria-hidden"] == "true"
    assert "4" in island.initial


def test_slider_omits_the_readout_when_not_requested() -> None:
    """With ``readout=False`` no readout span renders."""
    island = slider(topic="t", min=0, max=10, value=4, label="N", readout=False)
    assert find(island.initial, "span", **{"class": "sb-slider-value"}) == []


def test_slider_flags_float_bounds_as_non_integer() -> None:
    """A fractional step marks the value stream as float, not int (carried in props)."""
    island = slider(topic="t", min=0, max=1, step=0.1, value=0.5, label="N")
    assert island.props["integer"] is False
    (field,) = find(island.initial, "input", **{"class": "sb-slider-input"})
    assert field["step"] == "0.1"


def test_slider_rejects_min_not_below_max() -> None:
    """A non-increasing range fails where the call is written."""
    with pytest.raises(ValueError, match="min < max"):
        slider(topic="t", min=10, max=10, value=10, label="N")


def test_slider_rejects_a_non_positive_step() -> None:
    """A step of zero or less fails at the authoring boundary."""
    with pytest.raises(ValueError, match="step must be positive"):
        slider(topic="t", min=0, max=10, step=0, value=4, label="N")


def test_slider_rejects_a_value_out_of_range() -> None:
    """A value outside the bounds fails where the call is written."""
    with pytest.raises(ValueError, match="not in"):
        slider(topic="t", min=0, max=10, value=11, label="N")


def test_slider_rejects_a_blank_label() -> None:
    """The control needs a name; a blank label fails at the authoring boundary."""
    with pytest.raises(ValueError, match="non-empty label"):
        slider(topic="t", min=0, max=10, value=4, label="")


def test_slider_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the slider name (the runtime's dispatch key)."""
    (adapter,) = slider_scripts()
    assert 'register("slider"' in adapter


def test_slider_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-slider" in slider_styles()


def test_value_field_builds_a_value_field_island() -> None:
    """The factory names the value-field adapter and publishes the chosen topic."""
    island = value_field(topic="token:radius", value="0.375rem", label="Radius")
    assert isinstance(island, Island)
    assert island.name == "value-field"
    assert island.publishes == ("token:radius",)
    assert island.props == {"topic": "token:radius"}


def test_value_field_server_renders_the_named_field_with_its_value() -> None:
    """The field holds the initial value and carries the label at first paint."""
    island = value_field(topic="token:radius", value="0.375rem", label="Radius")
    (field,) = find(island.initial, "input", **{"class": "sb-value-field-text"})
    assert field["value"] == "0.375rem"
    assert field["aria-label"] == "Radius"


def test_value_field_carries_an_unvalidated_value() -> None:
    """It validates nothing: a font family with commas and quotes round-trips."""
    family = 'ui-monospace, "SF Mono", monospace'
    (field,) = find(
        value_field(topic="token:font", value=family, label="Family").initial,
        "input",
        **{"class": "sb-value-field-text"},
    )
    assert field["value"] == family


def test_value_field_rejects_a_blank_label() -> None:
    """The field needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        value_field(topic="token:radius", value="0", label="")


def test_value_field_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the value-field name (the runtime's dispatch key)."""
    (adapter,) = value_field_scripts()
    assert 'register("value-field"' in adapter


def test_value_field_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-value-field" in value_field_styles()


def test_preview_builds_a_scoped_sample_surface() -> None:
    """The preview is a static island wrapping a sample in a named scope wrapper."""
    island = preview(scope_id="preview-1")
    assert isinstance(island, Island)
    assert island.name == "preview"
    assert island.publishes == ()
    assert island.subscribes == ()
    (scope,) = find(island.initial, "div", **{"data-sb-scope": "preview-1"})
    assert "sb-preview-scope" in scope["class"]


def test_preview_renders_a_token_exercising_sample() -> None:
    """The sample includes the surfaces whose token adjacencies the preview shows."""
    html = preview(scope_id="preview-1").initial
    assert find(html, "button")
    assert find(html, "table", **{"class": "sb-preview-table"})
    (swatch,) = find(html, "span", **{"class": "sb-preview-swatch"})
    assert "var(--sb-color-accent)" in swatch["style"]


def test_preview_pins_the_scheme_when_given() -> None:
    """A ``scheme`` stamps the scheme class so the pane can pin one colour scheme."""
    (scope,) = find(
        preview(scope_id="p", scheme="dark").initial, "div", **{"data-sb-scope": "p"}
    )
    assert "sb-preview-dark" in scope["class"]
    (plain,) = find(preview(scope_id="p").initial, "div", **{"data-sb-scope": "p"})
    assert "sb-preview-light" not in plain["class"]
    assert "sb-preview-dark" not in plain["class"]


def test_preview_rejects_a_blank_scope_id() -> None:
    """The wrapper needs an id for a theme-state island to target; reject a blank."""
    with pytest.raises(ValueError, match="non-empty scope_id"):
        preview(scope_id="")


def test_preview_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-preview" in preview_styles()


def test_theme_state_serializes_an_arm_binding() -> None:
    """An arm binding becomes a kind-tagged payload carrying the token and arm."""
    island = theme_state(
        scope='[data-sb-scope="preview-1"]',
        bindings=(
            ArmBinding(topic="token:accent", token="--sb-color-accent", arm="light"),
        ),
    )
    assert island.name == "theme-state"
    assert island.subscribes == ("token:accent",)
    assert island.props == {
        "scope": '[data-sb-scope="preview-1"]',
        "bindings": [
            {
                "kind": "arm",
                "topic": "token:accent",
                "token": "--sb-color-accent",
                "arm": "light",
            }
        ],
    }


def test_theme_state_serializes_a_value_binding() -> None:
    """A value binding becomes a kind-tagged payload with no arm (set directly)."""
    island = theme_state(
        scope="[data-sb-scope]",
        bindings=(ValueBinding(topic="token:radius", token="--sb-radius-base"),),
    )
    assert island.subscribes == ("token:radius",)
    assert island.props["bindings"] == [
        {"kind": "value", "topic": "token:radius", "token": "--sb-radius-base"}
    ]


def test_theme_state_lists_each_topic_once_in_subscriptions() -> None:
    """Two arm bindings sharing a topic declare it once (the static-analysis set)."""
    island = theme_state(
        scope="[data-sb-scope]",
        bindings=(
            ArmBinding(topic="token:accent", token="--sb-color-accent", arm="light"),
            ArmBinding(topic="token:accent", token="--sb-color-accent", arm="dark"),
        ),
    )
    assert island.subscribes == ("token:accent",)
    # Both arm edits still ship as runtime bindings; only the declaration dedupes.
    assert island.props["bindings"] == [
        {
            "kind": "arm",
            "topic": "token:accent",
            "token": "--sb-color-accent",
            "arm": "light",
        },
        {
            "kind": "arm",
            "topic": "token:accent",
            "token": "--sb-color-accent",
            "arm": "dark",
        },
    ]


def test_theme_state_rejects_a_blank_scope() -> None:
    """Without a scope there is nothing to write onto; reject a blank."""
    with pytest.raises(ValueError, match="non-empty scope"):
        theme_state(
            scope="",
            bindings=(ValueBinding(topic="token:radius", token="--sb-radius-base"),),
        )


def test_theme_state_rejects_empty_bindings() -> None:
    """With no bindings the island would do nothing; reject it at the boundary."""
    with pytest.raises(ValueError, match="at least one binding"):
        theme_state(scope="[data-sb-scope]", bindings=())


def test_theme_state_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the theme-state name (the runtime's dispatch key)."""
    (adapter,) = theme_state_scripts()
    assert 'register("theme-state"' in adapter


def test_theme_export_carries_the_scope_and_bindings_with_no_topics() -> None:
    """The export island reads on demand: it ships the scope and binding payloads
    but subscribes to and publishes nothing (it never touches the bus)."""
    island = theme_export(
        scope="[data-sb-scope]",
        bindings=(
            ArmBinding(topic="token:accent", token="--sb-color-accent", arm="light"),
            ValueBinding(topic="token:radius", token="--sb-radius-base"),
        ),
    )
    assert island.name == "theme-export"
    assert island.subscribes == ()
    assert island.publishes == ()
    assert island.props == {
        "scope": "[data-sb-scope]",
        "bindings": [
            {
                "kind": "arm",
                "topic": "token:accent",
                "token": "--sb-color-accent",
                "arm": "light",
            },
            {"kind": "value", "topic": "token:radius", "token": "--sb-radius-base"},
        ],
    }


def test_theme_export_server_renders_a_copy_button() -> None:
    """The control is present at first paint: a button labelled for the export."""
    island = theme_export(
        scope="[data-sb-scope]",
        bindings=(ValueBinding(topic="token:radius", token="--sb-radius-base"),),
    )
    (button,) = find(island.initial, "button", **{"class": "sb-export-button"})
    assert button["type"] == "button"
    assert "Copy tokens.css" in island.initial


def test_theme_export_rejects_a_blank_scope() -> None:
    """Without a scope there is nothing to read from; reject a blank."""
    with pytest.raises(ValueError, match="non-empty scope"):
        theme_export(
            scope="",
            bindings=(ValueBinding(topic="token:radius", token="--sb-radius-base"),),
        )


def test_theme_export_rejects_empty_bindings() -> None:
    """With no bindings there is nothing to serialize; reject it at the boundary."""
    with pytest.raises(ValueError, match="at least one binding"):
        theme_export(scope="[data-sb-scope]", bindings=())


def test_theme_export_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the theme-export name (the runtime's dispatch key)."""
    (adapter,) = theme_export_scripts()
    assert 'register("theme-export"' in adapter


def test_theme_export_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-export" in theme_export_styles()


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
    """The adapter ships and registers under the popover name (the runtime's dispatch key)."""
    (adapter,) = popover_scripts()
    assert 'register("popover"' in adapter


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
