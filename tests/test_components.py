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

from importlib.resources import files

import pytest

from switchboard_ui import ownership
from switchboard_ui.assets import read_static
from switchboard_ui.components import (
    ArmBinding,
    Cell,
    ValueBinding,
    breadcrumb,
    breadcrumb_styles,
    code_block,
    code_block_scripts,
    code_block_styles,
    collapsible,
    collapsible_styles,
    color_input,
    color_input_scripts,
    color_input_styles,
    color_picker,
    color_picker_scripts,
    color_picker_styles,
    modal,
    modal_scripts,
    modal_styles,
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
    table,
    table_styles,
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


def _listening_controls() -> dict[str, Island]:
    """Every value control built with ``listen="follow:me"``, keyed by name."""
    return {
        "segmented": segmented(
            topic="t",
            options=_OPTIONS,
            value="overview",
            label=_LABEL,
            listen="follow:me",
        ),
        "slider": slider(
            topic="t", min=0, max=10, value=5, label="Size", listen="follow:me"
        ),
        "value-field": value_field(
            topic="t", value="0", label="Radius", listen="follow:me"
        ),
        "color-input": color_input(
            topic="t", value="#5b4bd6", label="Accent", listen="follow:me"
        ),
        "color-picker": color_picker(
            topic="t", value="#5b4bd6", label="Accent", listen="follow:me"
        ),
    }


def test_controls_declare_the_listen_topic() -> None:
    """A control given ``listen`` carries it in props and declares the subscription,
    so the adapter can follow the topic and the analyzer sees the edge."""
    for name, island in _listening_controls().items():
        assert island.props.get("listen") == "follow:me", name
        assert island.subscribes == ("follow:me",), name


def test_controls_reject_a_blank_listen_topic() -> None:
    """An empty ``listen`` would declare a subscription nothing can publish to."""
    with pytest.raises(ValueError, match="listen"):
        value_field(topic="t", value="0", label="Radius", listen="")


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
    assert "--sb-swatch:#5b4bd6" in swatch["style"]  # a value, not inline paint
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
    """The chip trigger holds the live color; the spectrum and hex field are present."""
    html = color_picker(topic="token:accent", value="#5b4bd6", label="Accent").initial
    swatch = [
        b
        for b in find(html, "button")
        if "sb-color-picker-swatch" in b.get("class", "")
    ]
    assert len(swatch) == 1
    assert "--sb-swatch:#5b4bd6" in swatch[0]["style"]  # a value, not inline paint
    assert swatch[0]["aria-label"] == "Accent"
    sliders = {s["class"]: s for s in find(html, "div", role="slider")}
    assert "sb-color-picker-area" in sliders
    assert sliders["sb-color-picker-hue"]["aria-valuemin"] == "0"
    assert sliders["sb-color-picker-hue"]["aria-valuemax"] == "360"
    # Both sliders carry the ARIA-required value trio, computed from the initial
    # color (#5b4bd6 is hue 247, saturation 65%, brightness 84%), so the markup
    # is correct at first paint, before the adapter mounts.
    assert sliders["sb-color-picker-hue"]["aria-valuenow"] == "247"
    area = sliders["sb-color-picker-area"]
    assert area["aria-valuemin"] == "0"
    assert area["aria-valuemax"] == "100"
    assert area["aria-valuenow"] == "84"
    assert area["aria-valuetext"] == "65% saturation, 84% brightness"
    (field,) = find(html, "input", **{"class": "sb-color-input-text"})
    assert field["value"] == "#5b4bd6"


def test_color_picker_shares_the_hex_field_with_the_color_input() -> None:
    """Both color controls render the identical hex field (one shared authoring)."""
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
    assert "style" not in swatch  # the accent fill is the theme's, not inline paint


def test_preview_pins_the_scheme_when_given() -> None:
    """A ``scheme`` stamps the scheme class so the pane can pin one color scheme."""
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


# --- table -------------------------------------------------------------------

_COLUMNS = ("Token", "Role")
_ROWS = (("accent", "interactive"), ("fg", "text"))


def _table() -> Island:
    """A table over two columns and two rows, named for assistive tech."""
    return table(columns=_COLUMNS, rows=_ROWS, label="Tokens")


def test_table_builds_a_static_table_island() -> None:
    """The factory names the table slot and ships no pub/sub or props (it is inert)."""
    island = _table()
    assert isinstance(island, Island)
    assert island.name == "table"
    assert island.publishes == ()
    assert island.subscribes == ()
    assert island.props == {}


def test_table_renders_a_named_grid() -> None:
    """The grid is a real <table> carrying the label as its accessible name."""
    (grid,) = find(_table().initial, "table", **{"class": "sb-table-grid"})
    assert grid["aria-label"] == "Tokens"


def test_table_server_renders_every_header_as_a_column_scope_th() -> None:
    """Each column is a ``<th scope="col">``, present and named at first paint."""
    island = _table()
    headers = find(island.initial, "th", scope="col")
    assert len(headers) == len(_COLUMNS)
    for column in _COLUMNS:
        assert column in island.initial


def test_table_server_renders_one_row_of_cells_per_data_row() -> None:
    """Every data row is a ``<tr>`` of ``<td>`` cells with the supplied text."""
    island = _table()
    assert len(find(island.initial, "tr")) == len(_ROWS) + 1  # + the header row
    assert len(find(island.initial, "td")) == len(_ROWS) * len(_COLUMNS)
    assert "interactive" in island.initial


def test_table_escapes_cell_text() -> None:
    """Cell text is escaped, never injected as markup."""
    island = table(columns=("X",), rows=(("<b>raw</b>",),), label="T")
    assert "<b>raw</b>" not in island.initial
    assert "&lt;b&gt;raw&lt;/b&gt;" in island.initial


def test_table_allows_a_header_only_table() -> None:
    """Zero rows is valid: a header with an empty body."""
    island = table(columns=_COLUMNS, rows=(), label="Tokens")
    assert find(island.initial, "td") == []


def test_table_rejects_no_columns() -> None:
    """A table needs at least one column; an empty set fails where it is written."""
    with pytest.raises(ValueError, match="at least one column"):
        table(columns=(), rows=(), label="Tokens")


def test_table_rejects_blank_label() -> None:
    """A table needs an accessible name; a blank label fails at the boundary."""
    with pytest.raises(ValueError, match="non-empty label"):
        table(columns=_COLUMNS, rows=_ROWS, label="")


def test_table_rejects_a_ragged_row() -> None:
    """A row whose cell count does not match the columns fails where it is written."""
    with pytest.raises(ValueError, match="row 1 has 1 cells, expected 2"):
        table(columns=_COLUMNS, rows=(("a", "b"), ("c",)), label="Tokens")


def test_table_emits_a_rich_cell_as_trusted_inline_html() -> None:
    """A ``Cell`` carries already-rendered inline HTML into the ``<td>`` verbatim."""
    island = table(
        columns=("Doc",),
        rows=((Cell('<a href="/docs/x">X</a>'),),),
        label="Docs",
    )
    assert '<td><a href="/docs/x">X</a></td>' in island.initial


def test_table_escapes_plain_cells_beside_rich_cells() -> None:
    """A plain ``str`` cell is still escaped even when a row also carries a ``Cell``."""
    island = table(
        columns=("A", "B"),
        rows=((Cell("<em>safe</em>"), "<b>raw</b>"),),
        label="Mixed",
    )
    assert "<em>safe</em>" in island.initial  # the rich cell is trusted
    assert "&lt;b&gt;raw&lt;/b&gt;" in island.initial  # the plain cell is escaped
    assert "<b>raw</b>" not in island.initial


def test_table_counts_a_rich_cell_as_one_cell_for_the_rectangular_check() -> None:
    """A ``Cell`` is one cell, so mixing kinds does not break the column-count rule."""
    with pytest.raises(ValueError, match="row 0 has 1 cells, expected 2"):
        table(columns=("A", "B"), rows=((Cell("<i>x</i>"),),), label="T")


def test_table_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-table" in table_styles()


# --- code block --------------------------------------------------------------

_CODE = "x = 1\nprint(x)"


def _code() -> Island:
    """A code block with the default chrome (a copy action, no language)."""
    return code_block(code=_CODE, label="Example")


def test_code_block_builds_a_named_group_island() -> None:
    """The factory names the code-block adapter and labels the group for AT."""
    island = _code()
    assert isinstance(island, Island)
    assert island.name == "code-block"
    assert island.publishes == ()
    (group,) = find(island.initial, "div", role="group")
    assert group["aria-label"] == "Example"


def test_code_block_server_renders_the_escaped_source() -> None:
    """The source lands in a <code> element, escaped, never injected as markup."""
    island = code_block(code="a < b && c", label="Example")
    assert find(island.initial, "code", **{"class": "sb-code-text"})
    assert "a &lt; b &amp;&amp; c" in island.initial
    assert "a < b && c" not in island.initial


def test_code_block_shows_the_copy_action_by_default() -> None:
    """The default block ships the copy button and a polite status node."""
    island = _code()
    assert find(island.initial, "button", **{"class": "sb-code-copy"})
    (status,) = find(island.initial, "span", **{"class": "sb-code-status"})
    assert status["role"] == "status"
    assert status["aria-live"] == "polite"


def test_code_block_shows_a_language_tag_when_given() -> None:
    """A supplied language renders in the chrome strip's language slot."""
    island = code_block(code=_CODE, label="Example", language="python")
    (lang,) = find(island.initial, "span", **{"class": "sb-code-lang"})
    assert "python" in island.initial
    assert lang is not None


def test_code_block_without_language_or_copy_has_no_chrome() -> None:
    """A bare block (no language, no copy) carries no chrome strip at all."""
    island = code_block(code=_CODE, label="Example", language=None, copy=False)
    assert find(island.initial, "div", **{"class": "sb-code-chrome"}) == []
    assert find(island.initial, "button", **{"class": "sb-code-copy"}) == []


def test_code_block_keeps_chrome_for_a_language_without_copy() -> None:
    """A language with copy off still has a chrome strip (the tag), but no button."""
    island = code_block(code=_CODE, label="Example", language="sh", copy=False)
    assert find(island.initial, "div", **{"class": "sb-code-chrome"})
    assert find(island.initial, "button", **{"class": "sb-code-copy"}) == []


def test_code_block_rejects_empty_code() -> None:
    """An empty code block is a likely mistake; it fails where it is written."""
    with pytest.raises(ValueError, match="non-empty code"):
        code_block(code="", label="Example")


def test_code_block_rejects_blank_label() -> None:
    """A code block needs an accessible name; a blank label fails at the boundary."""
    with pytest.raises(ValueError, match="non-empty label"):
        code_block(code=_CODE, label="")


def test_code_block_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the code-block name."""
    (adapter,) = code_block_scripts()
    assert 'register("code-block"' in adapter


def test_code_block_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-code" in code_block_styles()


# --- modal --------------------------------------------------------------------


def _modal() -> Island:
    """A modal with a titled header and a default close button."""
    return modal(
        trigger="Open",
        body="<p>Body.</p>",
        label="Example dialog",
        dialog_id="demo-modal",
        title="Dialog",
    )


def test_modal_builds_a_modal_island() -> None:
    """The factory names the modal adapter; with no open_topic it is silent on the bus."""
    island = _modal()
    assert isinstance(island, Island)
    assert island.name == "modal"
    assert island.publishes == ()
    assert island.props == {}


def test_modal_trigger_controls_a_named_dialog() -> None:
    """The trigger advertises a dialog popup and points at the dialog by id."""
    island = _modal()
    (trigger,) = find(island.initial, "button", **{"class": "sb-modal-trigger"})
    assert trigger["aria-haspopup"] == "dialog"
    assert trigger["aria-controls"] == "demo-modal"
    assert trigger["aria-expanded"] == "false"
    (dialog,) = find(island.initial, "dialog", id="demo-modal")
    assert dialog["aria-label"] == "Example dialog"


def test_modal_renders_a_title_and_a_close_button() -> None:
    """A titled modal shows the heading and an accessible close control."""
    island = _modal()
    (title,) = find(island.initial, "div", **{"class": "sb-modal-title"})
    assert title["role"] == "heading"
    assert "Dialog" in island.initial
    (close,) = find(island.initial, "button", **{"class": "sb-modal-close"})
    assert close["aria-label"] == "Close"


def test_modal_omits_the_title_when_not_given() -> None:
    """An untitled modal has only the close control in its header."""
    island = modal(
        trigger="Open", body="<p>Body.</p>", label="Bare", dialog_id="bare-modal"
    )
    assert find(island.initial, "div", **{"class": "sb-modal-title"}) == []
    assert find(island.initial, "button", **{"class": "sb-modal-close"})


def test_modal_echoes_open_state_when_given_a_topic() -> None:
    """An open_topic makes the modal publish its open/close on the bus."""
    island = modal(
        trigger="Open",
        body="<p>Body.</p>",
        label="Echoing",
        dialog_id="echo-modal",
        open_topic="modal:open",
    )
    assert island.publishes == ("modal:open",)
    assert island.props == {"topic": "modal:open"}


def test_modal_supports_a_content_less_chip_trigger() -> None:
    """An empty trigger is allowed when a trigger_label names it."""
    island = modal(
        trigger="",
        body="<p>Body.</p>",
        label="Chip",
        dialog_id="chip-modal",
        trigger_label="Open settings",
    )
    (trigger,) = find(island.initial, "button", **{"class": "sb-modal-trigger"})
    assert trigger["aria-label"] == "Open settings"


def test_modal_rejects_blank_label() -> None:
    """A dialog needs an accessible name; a blank label fails at the boundary."""
    with pytest.raises(ValueError, match="non-empty label"):
        modal(trigger="Open", body="<p>x</p>", label="", dialog_id="m")


def test_modal_rejects_an_invalid_dialog_id() -> None:
    """A malformed id silently breaks the trigger/dialog wiring, so it fails early."""
    with pytest.raises(ValueError, match="not a valid HTML id"):
        modal(trigger="Open", body="<p>x</p>", label="M", dialog_id="2 bad")


def test_modal_rejects_empty_body() -> None:
    """A modal with no content is a likely mistake; it fails where it is written."""
    with pytest.raises(ValueError, match="requires body content"):
        modal(trigger="Open", body="", label="M", dialog_id="m")


def test_modal_rejects_a_content_less_trigger_without_a_label() -> None:
    """An empty trigger with no trigger_label has no accessible name; it fails early."""
    with pytest.raises(ValueError, match="trigger content or a trigger_label"):
        modal(trigger="", body="<p>x</p>", label="M", dialog_id="m")


def test_modal_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the modal name."""
    (adapter,) = modal_scripts()
    assert 'register("modal"' in adapter


def test_modal_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-modal" in modal_styles()


# --- breadcrumb ---------------------------------------------------------------

_TRAIL = (("Home", "/"), ("Components", "/components"))


def _breadcrumb() -> Island:
    """A breadcrumb of two ancestor links ending at the current page."""
    return breadcrumb(trail=_TRAIL, current="Modal")


def test_breadcrumb_builds_a_static_nav_island() -> None:
    """The factory names the breadcrumb slot and ships no pub/sub (it is inert)."""
    island = _breadcrumb()
    assert isinstance(island, Island)
    assert island.name == "breadcrumb"
    assert island.publishes == ()
    (nav,) = find(island.initial, "nav", **{"class": "sb-breadcrumb"})
    assert nav["aria-label"] == "Breadcrumb"


def test_breadcrumb_renders_each_ancestor_as_a_link() -> None:
    """Every trail crumb is an anchor to its href; the current page is not a link."""
    island = _breadcrumb()
    links = find(island.initial, "a", **{"class": "sb-breadcrumb-link"})
    assert [(a_["href"]) for a_ in links] == ["/", "/components"]
    assert "Home" in island.initial and "Components" in island.initial


def test_breadcrumb_marks_the_current_page() -> None:
    """The current page is a non-link crumb carrying aria-current=page."""
    island = _breadcrumb()
    (current,) = find(island.initial, "span", **{"class": "sb-breadcrumb-current"})
    assert current["aria-current"] == "page"
    assert "Modal" in island.initial


def test_breadcrumb_separates_crumbs() -> None:
    """Inert separators sit between every crumb (links plus the current page)."""
    seps = find(_breadcrumb().initial, "span", **{"class": "sb-breadcrumb-sep"})
    assert len(seps) == len(_TRAIL)  # one before each of the two links' successor
    assert all(s["aria-hidden"] == "true" for s in seps)


def test_breadcrumb_allows_a_root_only_trail() -> None:
    """An empty trail is valid: just the current page, no separators."""
    island = breadcrumb(trail=(), current="Home")
    assert find(island.initial, "a") == []
    assert find(island.initial, "span", **{"class": "sb-breadcrumb-sep"}) == []


def test_breadcrumb_rejects_blank_current() -> None:
    """The trail must end somewhere; a blank current page fails at the boundary."""
    with pytest.raises(ValueError, match="non-empty current"):
        breadcrumb(trail=_TRAIL, current="")


def test_breadcrumb_rejects_blank_label() -> None:
    """The nav landmark needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        breadcrumb(trail=_TRAIL, current="Modal", label="")


def test_breadcrumb_rejects_a_blank_crumb_href() -> None:
    """A link with no target fails where it is written, not silently in the browser."""
    with pytest.raises(ValueError, match="crumb 0 has a blank href"):
        breadcrumb(trail=(("Home", ""),), current="Modal")


def test_breadcrumb_rejects_a_blank_crumb_label() -> None:
    """A crumb with no visible label fails at the authoring boundary."""
    with pytest.raises(ValueError, match="crumb 0 has a blank label"):
        breadcrumb(trail=(("", "/"),), current="Modal")


def test_breadcrumb_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-breadcrumb" in breadcrumb_styles()


# --- collapsible --------------------------------------------------------------


def _collapsible() -> Island:
    """A collapsible section with a count badge, expanded."""
    return collapsible(title="Items", body="<p>Body.</p>", count=3, open=True)


def test_collapsible_builds_a_native_details_island() -> None:
    """The factory is a static <details> island (no adapter, native disclosure)."""
    island = _collapsible()
    assert isinstance(island, Island)
    assert island.name == "collapsible"
    assert island.publishes == ()
    (details,) = find(island.initial, "details", **{"class": "sb-collapsible"})
    assert "open" in details


def test_collapsible_starts_closed_by_default() -> None:
    """Without ``open`` the details has no open attribute (collapsed at first paint)."""
    (details,) = find(
        collapsible(title="T", body="<p>x</p>").initial,
        "details",
        **{"class": "sb-collapsible"},
    )
    assert "open" not in details


def test_collapsible_summary_carries_the_title_and_count() -> None:
    """The summary shows the title and, when given, a count badge."""
    island = _collapsible()
    assert find(island.initial, "summary", **{"class": "sb-collapsible-summary"})
    (count,) = find(island.initial, "span", **{"class": "sb-collapsible-count"})
    assert count is not None
    assert "Items" in island.initial
    assert ">3<" in island.initial


def test_collapsible_omits_the_count_when_not_given() -> None:
    """A section with no count renders no badge."""
    island = collapsible(title="T", body="<p>x</p>")
    assert find(island.initial, "span", **{"class": "sb-collapsible-count"}) == []


def test_collapsible_rejects_blank_title() -> None:
    """A section needs a heading; a blank title fails at the boundary."""
    with pytest.raises(ValueError, match="non-empty title"):
        collapsible(title="", body="<p>x</p>")


def test_collapsible_rejects_empty_body() -> None:
    """A section with no content is a likely mistake; it fails where it is written."""
    with pytest.raises(ValueError, match="requires body content"):
        collapsible(title="T", body="")


def test_collapsible_rejects_a_negative_count() -> None:
    """A count is a tally; a negative one fails at the authoring boundary."""
    with pytest.raises(ValueError, match="non-negative"):
        collapsible(title="T", body="<p>x</p>", count=-1)


def test_collapsible_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-collapsible" in collapsible_styles()


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
        non_layout = ownership.declared_properties(css) - ownership.LAYOUT_PROPERTIES
        assert not non_layout, (
            f"{name} declares non-layout properties: {sorted(non_layout)}"
        )


def test_component_css_selects_only_sb_classes() -> None:
    """A component sheet styles only its own ``.sb-*`` hooks, never host elements."""
    for name, css in _component_sheets():
        foreign = [s for s in ownership.selectors(css) if not s.startswith(".sb-")]
        assert not foreign, f"{name} selects non-sb elements: {foreign}"


def test_component_css_carries_no_paint_tokens_or_magic_numbers() -> None:
    """A component sheet stays token-free (only ``--sb-fit-*``) with no bare length."""
    for name, css in _component_sheets():
        assert "light-dark(" not in css, (
            f"{name} consumes theming (a cause, not structure)"
        )
        non_contract = sorted(
            {
                t
                for t in ownership.referenced_tokens(css)
                if not t.startswith(ownership.CONTRACT_TOKEN_PREFIX)
            }
        )
        assert not non_contract, f"{name} references non-contract tokens {non_contract}"
        magic = sorted(ownership.magic_lengths(css))
        assert not magic, (
            f"{name} has bare absolute lengths {magic}; use a token or keyword"
        )


def test_popover_adapter_subscribes_its_invalidation_ledger() -> None:
    """The popover's hand placement stays current: every covered invalidation
    source in the adapter's ledger has its subscription in the code — open
    (toggle), viewport resize, ancestor scroll (capture phase), and panel
    growth. The written position is derived state; a ledger row without its
    subscription is a stale-position bug."""
    js = read_static("popover.js")
    assert 'addEventListener("toggle"' in js
    assert 'addEventListener("resize"' in js
    assert 'addEventListener("scroll", onResize, true)' in js  # capture phase
    assert "new ResizeObserver" in js
