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
from switchboard_ui.components import (
    ArmBinding,
    Cell,
    FilterControl,
    NavItem,
    NavSection,
    TocEntry,
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
    filter_table,
    filter_table_scripts,
    filter_table_styles,
    hero,
    hero_styles,
    masthead,
    masthead_styles,
    modal,
    modal_scripts,
    modal_styles,
    nav,
    nav_scripts,
    nav_styles,
    popover,
    popover_scripts,
    popover_styles,
    preview,
    preview_styles,
    prose,
    prose_lead,
    prose_styles,
    section,
    section_heading,
    section_styles,
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
    toc,
    toc_styles,
    value_field,
    value_field_scripts,
    value_field_styles,
)
from switchboard_ui.model import Island
from tests.htmlprobe import elements, find

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
    """A malformed id would break the trigger/panel wiring or the anchor-name
    ident it becomes; reject it up front."""
    with pytest.raises(ValueError, match="not a valid id"):
        _popover(panel_id="2 bad id")
    with pytest.raises(ValueError, match="not a valid id"):
        _popover(panel_id="dot.and:colon")


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


def test_popover_carries_the_anchor_link() -> None:
    """The wrapper carries the per-instance anchor name as a custom-property
    value; the structural sheet consumes it on both sides of the link."""
    island = _popover()
    (wrapper,) = find(island.initial, "div", **{"class": "sb-popover"})
    assert wrapper["style"] == "--sb-anchor: --sb-anchor-settings-pop"
    css = popover_styles()
    assert "anchor-name: var(--sb-anchor)" in css
    assert "position-anchor: var(--sb-anchor)" in css
    assert "position-try-fallbacks" in css


def test_popover_adapter_owns_no_geometry() -> None:
    """Placement is the structural sheet's (anchor positioning); the adapter
    never measures, writes, or invalidates a position — the retired reposition
    ledger stays retired."""
    (adapter,) = popover_scripts()
    assert 'addEventListener("toggle"' in adapter  # the one subscription left
    for marker in (
        "getBoundingClientRect",
        "ResizeObserver",
        '"resize"',
        '"scroll"',
        ".style.",
    ):
        assert marker not in adapter


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
    with pytest.raises(ValueError, match="not a valid id"):
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


# --- nav ----------------------------------------------------------------------


def _nav() -> Island:
    """A two-section nav: a leading ungrouped item, then a headed group."""
    return nav(
        sections=(
            NavSection(items=(NavItem(label="Index", href="/", current=True),)),
            NavSection(
                heading="Groups",
                items=(
                    NavItem(label="Types", href="/types/", meta="17"),
                    NavItem(label="Layout", href="/layout/"),
                ),
            ),
        ),
        label="Site",
    )


def test_nav_builds_a_static_nav_island() -> None:
    """The factory names the nav slot and ships no pub/sub (it is inert)."""
    island = _nav()
    assert island.name == "nav"
    assert island.publishes == () and island.subscribes == ()


def test_nav_renders_sections_with_headings_over_items() -> None:
    """A headed section renders its group label; items carry their hrefs."""
    island = _nav()
    groups = find(island.initial, "div", **{"class": "sb-nav-group"})
    assert len(groups) == 1
    assert ">Groups<" in island.initial
    hrefs = [a["href"] for a in find(island.initial, "a", **{"class": "sb-nav-item"})]
    assert hrefs == ["/", "/types/", "/layout/"]


def test_nav_marks_only_the_current_item() -> None:
    """Exactly the current item carries aria-current; the others say false."""
    island = _nav()
    current = find(island.initial, "a", **{"aria-current": "page"})
    assert [a["href"] for a in current] == ["/"]


def test_nav_renders_meta_only_where_given() -> None:
    """An item's meta annotation renders at the row's edge; absent meta renders nothing."""
    island = _nav()
    metas = find(island.initial, "span", **{"class": "sb-nav-meta"})
    assert len(metas) == 1
    assert ">17<" in island.initial


def test_nav_uses_semantic_list_markup() -> None:
    """The hierarchy is carried by nav/ul/li/a, not by sibling divs.

    The list is what tells assistive technology that these rows form a tree and
    how deep each one sits; a flat run of anchors carries no such information.
    """
    island = _nav()
    assert find(island.initial, "nav", **{"aria-label": "Site"})
    assert find(island.initial, "ul", **{"class": "sb-nav-list"})
    nodes = find(island.initial, "li", **{"class": "sb-nav-node"})
    assert len(nodes) == 3  # one per item, each holding its own anchor


def _deep_nav(current_at_depth: int = 3) -> Island:
    """A three-level nav, current marked at the requested depth."""
    return nav(
        sections=(
            NavSection(
                heading="Projects",
                items=(
                    NavItem(
                        label="alpha",
                        href="/p/alpha/",
                        current=current_at_depth == 1,
                        children=(
                            NavItem(
                                label="Roadmap",
                                href="/p/alpha/roadmap/",
                                current=current_at_depth == 2,
                                children=(
                                    NavItem(
                                        label="Q1",
                                        href="/p/alpha/roadmap/q1/",
                                        current=current_at_depth == 3,
                                    ),
                                ),
                            ),
                            NavItem(label="Docs", href="/p/alpha/docs/"),
                        ),
                    ),
                    NavItem(label="beta", href="/p/beta/"),
                ),
            ),
        ),
        label="Site",
    )


def test_nav_nests_children_inside_their_own_parent_node() -> None:
    """A child belongs to the item it is written inside, at any depth.

    The flattened model this replaces made nesting order-dependent: a run of
    nested rows attached to whatever preceded it, so moving a row reparented it
    without the row changing. Here the tree is the value's own shape.
    """
    island = _deep_nav()
    order = [
        (tag, attrs.get("href", ""))
        for tag, attrs in elements(island.initial)
        if attrs.get("class") in ("sb-nav-item", "sb-nav-list sb-nav-sublist")
    ]
    assert order == [
        ("a", "/p/alpha/"),
        ("ul", ""),
        ("a", "/p/alpha/roadmap/"),
        ("ul", ""),
        ("a", "/p/alpha/roadmap/q1/"),
        ("a", "/p/alpha/docs/"),
        ("a", "/p/beta/"),
    ]
    # beta closes out of both sublists: it is a sibling of alpha, not of Docs.
    docs_at = island.initial.index("/p/alpha/docs/")
    assert island.initial.index("</ul>", docs_at) < island.initial.index("/p/beta/")


def test_nav_marks_every_ancestor_of_the_current_item() -> None:
    """The path to the current page is computed server-side, at every depth.

    The hook lands on ancestors only; the current item itself is identified by
    `aria-current`, so a theme can paint the path and the destination apart.
    """
    island = _deep_nav(current_at_depth=3)
    ancestors = find(island.initial, "li", **{"data-current-ancestor": ""})
    hrefs = [
        a["href"]
        for a in find(island.initial, "a", **{"class": "sb-nav-item"})
        if a.get("aria-current") == "page"
    ]
    assert hrefs == ["/p/alpha/roadmap/q1/"]
    assert len(ancestors) == 2  # alpha and Roadmap, not Q1 itself


def test_nav_marks_no_ancestor_when_the_current_item_is_top_level() -> None:
    """A top-level current page has no ancestors, so no node carries the hook."""
    island = _deep_nav(current_at_depth=1)
    assert find(island.initial, "li", **{"data-current-ancestor": ""}) == []


def test_nav_rejects_blank_label_sections_and_items() -> None:
    """A blank nav label, an empty section list, or a blank item fails at the boundary."""
    section = NavSection(items=(NavItem(label="A", href="/a"),))
    with pytest.raises(ValueError, match="non-empty label"):
        nav(sections=(section,), label="")
    with pytest.raises(ValueError, match="at least one section"):
        nav(sections=(), label="Site")
    with pytest.raises(ValueError, match="blank label"):
        nav(
            sections=(NavSection(items=(NavItem(label="", href="/a"),)),),
            label="Site",
        )
    with pytest.raises(ValueError, match="blank href"):
        nav(
            sections=(NavSection(items=(NavItem(label="A", href=""),)),),
            label="Site",
        )


def test_nav_validation_errors_name_the_node_by_its_path() -> None:
    """An error identifies which node is bad, unambiguously across sections.

    The flattened model numbered items per section, so a page with several
    sections produced several different "item 0" errors, none of which said
    which section. A path is unique in the whole tree and survives reordering.
    """
    with pytest.raises(
        ValueError, match=r"section 1 > item 0 > item 1 has a blank label"
    ):
        nav(
            sections=(
                NavSection(items=(NavItem(label="ok", href="/ok"),)),
                NavSection(
                    items=(
                        NavItem(
                            label="parent",
                            href="/p",
                            children=(
                                NavItem(label="fine", href="/p/a"),
                                NavItem(label="", href="/p/b"),
                            ),
                        ),
                    )
                ),
            ),
            label="Site",
        )


def test_nav_rejects_more_than_one_current_item() -> None:
    """Two current pages is a contradiction, so it fails where it is written.

    Rendering both would leave the reader with two "you are here" marks and no
    way to tell which is true; failing names the count instead.
    """
    with pytest.raises(ValueError, match="2 items marked current"):
        nav(
            sections=(
                NavSection(
                    items=(
                        NavItem(label="a", href="/a", current=True),
                        NavItem(
                            label="b",
                            href="/b",
                            children=(NavItem(label="c", href="/c", current=True),),
                        ),
                    )
                ),
            ),
            label="Site",
        )


def test_nav_without_a_scroll_key_is_entirely_static() -> None:
    """A nav that does not opt in ships no props and no script.

    The persistence is an enhancement for shared chrome, not a tax on every nav.
    """
    island = _nav()
    assert island.props == {}
    assert "<script" not in island.initial


def test_nav_with_a_scroll_key_emits_a_restore_script_before_the_nav() -> None:
    """The restoring script is inline and sits before the markup it restores.

    Position is the whole point, and it is counter-intuitive. Placed *after* the
    nav the script reads more naturally and still works on a fast connection, but
    a chunked response lets the parser finish the nav, yield, and paint the
    finished rail at the top before reaching the next byte — measured at one
    frame on a 2KB-chunked fixture. Starting before the nav means the script is
    already re-applying as rows arrive, so no complete-and-unscrolled frame
    exists to be seen.
    """
    island = nav(
        sections=(NavSection(items=(NavItem(label="A", href="/a"),)),),
        label="Site",
        scroll_key="primary",
    )
    assert island.props == {"scrollKey": "primary"}
    assert island.initial.index("<script") < island.initial.index("<nav")
    [script] = find(island.initial, "script")
    assert script["data-scroll-key"] == "primary"


def test_the_restore_script_reads_a_namespaced_per_tab_key() -> None:
    """Restoration is per-tab and namespaced, so two navs never collide.

    sessionStorage rather than localStorage: the position wanted is navigation
    continuity within one tab, not a durable preference that outlives the visit.
    """
    island = nav(
        sections=(NavSection(items=(NavItem(label="A", href="/a"),)),),
        label="Site",
        scroll_key="primary",
    )
    assert "sessionStorage" in island.initial
    assert "localStorage" not in island.initial
    assert "sb-nav-scroll:" in island.initial


def test_the_restore_script_reveals_the_current_item_without_a_stored_offset() -> None:
    """A first visit places the rail by the current item, not by a stored value.

    A deep link, a search result, or a shared URL arrives with nothing stored, so
    the rail opens at the top; on a long rail that hides which page the reader is
    on. The script therefore carries both jobs, and picks between them on whether
    a usable offset exists.
    """
    island = nav(
        sections=(NavSection(items=(NavItem(label="A", href="/a"),)),),
        label="Site",
        scroll_key="primary",
    )
    assert 'aria-current="page"' in island.initial  # the reveal target selector
    assert "getBoundingClientRect" in island.initial  # the nearest calculation


def test_the_restore_script_survives_unavailable_storage() -> None:
    """Storage throws in a private or blocked context; the nav must still work."""
    island = nav(
        sections=(NavSection(items=(NavItem(label="A", href="/a"),)),),
        label="Site",
        scroll_key="primary",
    )
    assert "try {" in island.initial and "catch" in island.initial


def test_nav_scripts_ships_the_saving_adapter_only() -> None:
    """The adapter saves; restoring ships inline with the markup.

    Splitting them is the point: saving has no deadline, restoring has a hard one
    (before first paint), and only the restoring half must therefore be inline.
    """
    (source,) = nav_scripts()
    assert 'register("nav"' in source
    assert "sessionStorage.setItem" in source
    assert "scrollTop =" not in source  # the adapter never restores


def test_the_saving_adapter_leaves_the_back_forward_cache_alone() -> None:
    """A bfcache traversal reuses the live DOM, whose scroll the browser restored.

    Writing to it on restore would fight the platform, so the adapter listens for
    ``pagehide`` (which fires for both unload and bfcache suspension) and never
    for ``pageshow``.
    """
    (source,) = nav_scripts()
    assert "pagehide" in source
    assert "pageshow" not in source
    assert '"unload"' not in source


def test_nav_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-nav" in nav_styles()


# --- toc ----------------------------------------------------------------------


def _toc() -> Island:
    """A toc with one top-level entry followed by a nested run and another top."""
    return toc(
        entries=(
            TocEntry(text="Recipe", anchor="recipe"),
            TocEntry(text="Why", anchor="why", nested=True),
            TocEntry(text="Rules", anchor="rules", nested=True),
            TocEntry(text="Related", anchor="related"),
        ),
        label="On this page",
    )


def test_toc_builds_a_static_nav_island() -> None:
    """The factory names the toc slot and ships no pub/sub (it is inert)."""
    island = _toc()
    assert island.name == "toc"
    assert island.publishes == () and island.subscribes == ()


def test_toc_links_every_entry_to_its_anchor() -> None:
    """Each entry renders as an in-page anchor link to its heading id."""
    island = _toc()
    links = find(island.initial, "a")
    assert [a["href"] for a in links] == ["#recipe", "#why", "#rules", "#related"]


def test_toc_groups_a_nested_run_into_one_sublist() -> None:
    """Consecutive nested entries share a sublist that owns the indent; the
    following top-level entry closes it."""
    island = _toc()
    sublists = find(island.initial, "div", **{"class": "sb-toc-sublist"})
    assert len(sublists) == 1
    nested = find(island.initial, "a", **{"class": "sb-toc-link sb-toc-link-nested"})
    assert [a["href"] for a in nested] == ["#why", "#rules"]


def test_toc_with_no_entries_keeps_its_label() -> None:
    """A page with no headings keeps the rail label over an empty list."""
    island = toc(entries=(), label="On this page")
    assert "On this page" in island.initial
    assert find(island.initial, "a") == []


def test_toc_rejects_blank_label_text_or_anchor() -> None:
    """A blank rail label, entry text, or anchor fails at the authoring boundary."""
    with pytest.raises(ValueError, match="non-empty label"):
        toc(entries=(), label="")
    with pytest.raises(ValueError, match="blank text"):
        toc(entries=(TocEntry(text="", anchor="a"),))
    with pytest.raises(ValueError, match="blank anchor"):
        toc(entries=(TocEntry(text="T", anchor=""),))


def test_toc_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-toc" in toc_styles()


def test_masthead_builds_a_static_brand_link() -> None:
    """The brand is a static island (no adapter, no pub/sub): a link that navigates."""
    island = masthead(name="System Principles", href="/")
    assert island.name == "masthead"
    assert island.publishes == () and island.subscribes == ()
    (brand,) = find(island.initial, "a", **{"class": "sb-masthead"})
    assert brand["href"] == "/"
    assert "System Principles" in island.initial


def test_masthead_defaults_its_link_to_the_site_root() -> None:
    """The brand links home unless the host routes it elsewhere."""
    (brand,) = find(masthead(name="Dashboard").initial, "a", **{"class": "sb-masthead"})
    assert brand["href"] == "/"


def test_masthead_rejects_a_blank_name() -> None:
    """A nameless brand fails where it is written."""
    with pytest.raises(ValueError, match="non-empty name"):
        masthead(name="")


def test_masthead_rejects_a_blank_href() -> None:
    """A brand that links nowhere fails where it is written."""
    with pytest.raises(ValueError, match="non-empty href"):
        masthead(name="Dashboard", href="")


def test_masthead_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hook."""
    assert ".sb-masthead" in masthead_styles()


def test_section_heading_pairs_the_title_with_its_far_edge_meta() -> None:
    """The row carries the title as an h2 beside the annotation."""
    island = section_heading(title="Related", meta="3 principles")
    assert island.name == "section-heading"
    assert find(island.initial, "h2", **{"class": "sb-section-title"})
    assert find(island.initial, "span", **{"class": "sb-section-meta"})
    assert ">Related</h2>" in island.initial
    assert ">3 principles</span>" in island.initial


def test_section_heading_omits_the_meta_when_there_is_none() -> None:
    """A heading with nothing to annotate renders the title alone."""
    html = section_heading(title="Overview").initial
    assert not find(html, "span", **{"class": "sb-section-meta"})


def test_section_heading_anchors_the_row_when_asked() -> None:
    """The anchor lands on the row, so a rail entry scrolls to the heading itself."""
    (row,) = find(
        section_heading(title="Specs", anchor="specs").initial,
        "div",
        **{"class": "sb-section-heading"},
    )
    assert row["id"] == "specs"


def test_section_heading_carries_no_id_without_an_anchor() -> None:
    """An unanchored heading emits no empty id attribute."""
    (row,) = find(
        section_heading(title="Specs").initial, "div", **{"class": "sb-section-heading"}
    )
    assert "id" not in row


def test_section_heading_rejects_a_blank_title() -> None:
    """A heading with no title fails where it is written."""
    with pytest.raises(ValueError, match="non-empty title"):
        section_heading(title="")


def test_section_heading_rejects_an_invalid_anchor() -> None:
    """An anchor that could not be linked to fails at the authoring boundary."""
    with pytest.raises(ValueError, match="not a valid id"):
        section_heading(title="Specs", anchor="spec list")


def test_section_wraps_its_heading_and_body_in_one_column() -> None:
    """The section is the heading row over its content, marked for the theme's gap."""
    island = section(title="Groups", meta="4 total", body="<p>Body</p>")
    assert island.name == "section"
    assert island.class_ == "sb-section"
    assert find(island.initial, "h2", **{"class": "sb-section-title"})
    assert "<p>Body</p>" in island.initial


def test_section_rejects_empty_body() -> None:
    """A section with no content fails where it is written."""
    with pytest.raises(ValueError, match="body content"):
        section(title="Groups", body="")


def test_section_styles_returns_the_structural_css() -> None:
    """One sheet covers the container and its heading row."""
    css = section_styles()
    assert ".sb-section" in css and ".sb-section-heading" in css


def test_hero_stacks_the_eyebrow_title_and_description() -> None:
    """The display heading renders all three parts in reading order."""
    island = hero(
        title="System Principles",
        description="A catalog of design principles.",
        eyebrow="Design principles · catalog",
    )
    assert island.name == "hero"
    assert find(island.initial, "div", **{"class": "sb-hero-eyebrow"})
    assert find(island.initial, "h1", **{"class": "sb-hero-title"})
    assert find(island.initial, "p", **{"class": "sb-prose-lead"})
    assert ">Design principles · catalog</div>" in island.initial
    assert ">System Principles</h1>" in island.initial
    assert ">A catalog of design principles.</p>" in island.initial


def test_hero_renders_the_title_alone_when_that_is_all_there_is() -> None:
    """The optional parts leave no empty elements behind."""
    html = hero(title="Groups").initial
    assert not find(html, "div", **{"class": "sb-hero-eyebrow"})
    assert not find(html, "p", **{"class": "sb-prose-lead"})


def test_hero_rejects_a_blank_title() -> None:
    """A hero with no title fails where it is written."""
    with pytest.raises(ValueError, match="non-empty title"):
        hero(title="")


def test_hero_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hook."""
    assert ".sb-hero" in hero_styles()


def test_prose_wraps_rendered_markup_in_the_painted_surface() -> None:
    """The host's rendered markup passes through under the one hook the theme paints."""
    island = prose(html="<h2>Heading</h2><p>Body</p>")
    assert island.name == "prose"
    assert island.publishes == () and island.subscribes == ()
    (surface,) = find(island.initial, "div", **{"class": "sb-prose"})
    assert surface is not None
    assert "<h2>Heading</h2><p>Body</p>" in island.initial


def test_prose_rejects_empty_content() -> None:
    """An empty prose surface fails where it is written."""
    with pytest.raises(ValueError, match="rendered content"):
        prose(html="")


def test_prose_lead_escapes_its_text() -> None:
    """A lead is a fragment of escaped plain text, not trusted markup."""
    html = prose_lead("Tokens & their <arms>")
    assert 'class="sb-prose-lead"' in html
    assert "&amp;" in html and "&lt;arms&gt;" in html


def test_prose_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hook."""
    assert ".sb-prose" in prose_styles()


_FILTER_ROWS: tuple[tuple[str, ...], ...] = (
    ("Segmented", "Control"),
    ("Table", "Display"),
)
_FILTER_KEYS = ["segmented control", "table display"]


def _query_control() -> FilterControl:
    """A filter bar holding one typed-query field."""
    field = value_field(topic="index:filter", value="", label="Filter")
    return FilterControl(label="Filter", control=field)


def test_filter_table_subscribes_the_topic_its_control_publishes() -> None:
    """The bar's control and the grid meet on the bus, not through a reference."""
    island = filter_table(
        columns=("Name", "Kind"),
        rows=_FILTER_ROWS,
        label="Components",
        topic="index:filter",
        keys=_FILTER_KEYS,
        controls=(_query_control(),),
    )
    assert island.name == "filter-table"
    assert island.subscribes == ("index:filter",)
    assert island.class_ == "sb-filter-table"
    assert island.props["keys"] == _FILTER_KEYS
    assert island.props["match"] == "substring"
    assert island.props["allValue"] == ""


def test_filter_table_renders_every_row_for_the_browser_to_hide() -> None:
    """The grid is complete at first paint; filtering only hides what is there."""
    html = filter_table(
        columns=("Name", "Kind"),
        rows=_FILTER_ROWS,
        label="Components",
        topic="index:filter",
        keys=_FILTER_KEYS,
        controls=(_query_control(),),
    ).initial
    assert len(find(html, "tr")) == len(_FILTER_ROWS) + 1  # the header row
    (count,) = find(html, "span", **{"class": "sb-filter-count"})
    assert count["aria-live"] == "polite"  # the result size is announced


def test_filter_table_labels_each_control_in_the_bar() -> None:
    """A control is rendered under its own label, so a two-control bar reads."""
    html = filter_table(
        columns=("Name", "Kind"),
        rows=_FILTER_ROWS,
        label="Components",
        topic="index:filter",
        keys=_FILTER_KEYS,
        controls=(_query_control(),),
    ).initial
    assert len(find(html, "span", **{"class": "sb-filter-label"})) == 1
    assert ">Filter</span>" in html
    assert find(html, "input", **{"class": "sb-value-field-text"})


def test_filter_table_declares_the_sort_topic_and_keys_when_sorting() -> None:
    """A sort control adds a second subscription and its own aligned key list."""
    island = filter_table(
        columns=("Name", "Kind"),
        rows=_FILTER_ROWS,
        label="Components",
        topic="index:filter",
        keys=_FILTER_KEYS,
        controls=(_query_control(),),
        match="exact",
        all_value="all",
        sort_topic="index:sort",
        sort_keys=["2026-01-02", "2026-01-01"],
    )
    assert island.subscribes == ("index:filter", "index:sort")
    assert island.props["sortTopic"] == "index:sort"
    assert island.props["sortKeys"] == ["2026-01-02", "2026-01-01"]
    assert island.props["match"] == "exact"
    assert island.props["allValue"] == "all"


def test_filter_table_omits_sort_props_when_there_is_no_sort_control() -> None:
    """An unsorted table declares nothing about sorting."""
    island = filter_table(
        columns=("Name", "Kind"),
        rows=_FILTER_ROWS,
        label="Components",
        topic="index:filter",
        keys=_FILTER_KEYS,
        controls=(_query_control(),),
    )
    assert "sortTopic" not in island.props and "sortKeys" not in island.props


def test_filter_table_rejects_a_blank_topic() -> None:
    """A table subscribing to nothing fails where it is written."""
    with pytest.raises(ValueError, match="non-empty topic"):
        filter_table(
            columns=("Name",),
            rows=(("Segmented",),),
            label="Components",
            topic="",
            keys=["segmented"],
            controls=(_query_control(),),
        )


def test_filter_table_rejects_an_empty_control_bar() -> None:
    """A filterable table with no control to filter it fails where it is written."""
    with pytest.raises(ValueError, match="at least one control"):
        filter_table(
            columns=("Name",),
            rows=(("Segmented",),),
            label="Components",
            topic="index:filter",
            keys=["segmented"],
            controls=(),
        )


def test_filter_table_rejects_a_blank_control_label() -> None:
    """An unlabelled control fails where it is written."""
    field = value_field(topic="index:filter", value="", label="Filter")
    with pytest.raises(ValueError, match="control 0 has a blank label"):
        filter_table(
            columns=("Name",),
            rows=(("Segmented",),),
            label="Components",
            topic="index:filter",
            keys=["segmented"],
            controls=(FilterControl(label="", control=field),),
        )


def test_filter_table_rejects_keys_misaligned_with_the_rows() -> None:
    """Keys are matched by row position, so a short list fails at authoring time."""
    with pytest.raises(ValueError, match="1 keys for 2 rows"):
        filter_table(
            columns=("Name", "Kind"),
            rows=_FILTER_ROWS,
            label="Components",
            topic="index:filter",
            keys=["segmented"],
            controls=(_query_control(),),
        )


def test_filter_table_rejects_sort_keys_misaligned_with_the_rows() -> None:
    """The sort keys are aligned the same way, and fail the same way."""
    with pytest.raises(ValueError, match="1 sort keys for 2 rows"):
        filter_table(
            columns=("Name", "Kind"),
            rows=_FILTER_ROWS,
            label="Components",
            topic="index:filter",
            keys=_FILTER_KEYS,
            controls=(_query_control(),),
            sort_topic="index:sort",
            sort_keys=["2026-01-01"],
        )


def test_filter_table_rejects_sort_keys_with_no_topic_to_order_by() -> None:
    """Keys nothing publishes against are dead weight; the call fails instead."""
    with pytest.raises(ValueError, match="need a sort_topic"):
        filter_table(
            columns=("Name", "Kind"),
            rows=_FILTER_ROWS,
            label="Components",
            topic="index:filter",
            keys=_FILTER_KEYS,
            controls=(_query_control(),),
            sort_keys=["2026-01-02", "2026-01-01"],
        )


def test_filter_table_scripts_returns_the_adapter() -> None:
    """The adapter ships and registers under the component's name."""
    (adapter,) = filter_table_scripts()
    assert 'register("filter-table"' in adapter


def test_filter_table_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    css = filter_table_styles()
    assert ".sb-filter-table" in css and ".sb-filter-bar" in css


def _component_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every component's structural CSS (not ``layout.css``)."""
    static = files("switchboard_ui") / "static"
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in static.iterdir()
        if path.name.endswith(".css") and path.name != "layout.css"
    ]


def test_component_css_declares_only_geometry_and_permitted_resets() -> None:
    """A component sheet declares geometry, or a permitted user-agent reset.

    Same value-guarded rule the root layout sheet obeys: a sheet may clear the
    presentation a user agent puts on an element the package generated (a list's
    marker and inline padding), but may never use box-spacing for spacing or name
    a paint property.
    """
    for name, css in _component_sheets():
        offenders = ownership.non_structural_declarations(css)
        assert not offenders, f"{name} declares non-structural values: {offenders}"


def test_component_css_selects_only_sb_classes() -> None:
    """A component sheet styles only its own ``.sb-*`` hooks, never host elements."""
    for name, css in _component_sheets():
        foreign = [s for s in ownership.selectors(css) if not s.startswith(".sb-")]
        assert not foreign, f"{name} selects non-sb elements: {foreign}"


def test_component_css_carries_no_paint_tokens_or_magic_numbers() -> None:
    """A component sheet stays token-free (only ``--sb-fit-*`` obligations and
    the named per-instance link values) with no bare length."""
    for name, css in _component_sheets():
        assert "light-dark(" not in css, (
            f"{name} consumes theming (a cause, not structure)"
        )
        non_contract = sorted(
            {
                t
                for t in ownership.referenced_tokens(css)
                if not t.startswith(ownership.CONTRACT_TOKEN_PREFIX)
                and t not in ownership.STRUCTURAL_LINK_TOKENS
            }
        )
        assert not non_contract, f"{name} references non-contract tokens {non_contract}"
        magic = sorted(ownership.magic_lengths(css))
        assert not magic, (
            f"{name} has bare absolute lengths {magic}; use a token or keyword"
        )
