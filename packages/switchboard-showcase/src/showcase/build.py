"""Build the showcase document(s) through the public API.

Mirrors the package's own ``demo.py`` build / ``cli.py`` serve split: this module
returns what to render; :mod:`showcase.server` serves and hot-reloads it. It builds
two pages:

- :func:`build_showcase` — the component gallery: each island and preset rendered
  on a self-rendered page, the forcing function the theme and components are shaped
  against (the segmented toggle, popover, color picker, slider, value field, and a
  live preview).
- :func:`build_theme_builder` — the capstone dogfood: a control panel generated
  from the theme's token registry beside a live light/dark preview, with a
  ``tokens.css`` export. Editing a control repaints the preview through the bus.

A component ships three parts; the host wires each. The ``build_*`` functions place
the islands, the ``*_scripts`` functions carry the adapters (for ``extra_scripts``),
and the ``*_styles`` functions carry the structural CSS (for ``extra_head``, beside
the theme). That is the same opt-in a real host performs.
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import assert_never

from showcase.chrome import surface_switch, surface_switch_styles
from switchboard_theme import REGISTRY, Category, Fixed, Themed, Token, ValueType
from switchboard_theme.modes import (
    mode_stamp_head,
    mode_state,
    mode_switch,
    mode_switch_scripts,
    mode_switch_styles,
)
from switchboard_ui import Document, Island, render_island
from switchboard_ui.components import (
    ArmBinding,
    Binding,
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
    preview_items,
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
from switchboard_ui.html import element, escape_text
from switchboard_ui.model import Frame, Region, Slot
from switchboard_ui.presets import three_column

# The gallery is a nav | content | inspector tool, the three columns of the
# three_column preset used for what they mean. All three are projections of one
# registry (`_gallery_specs`): the nav lists each component, the center renders it,
# and the inspector shows its props and tokens. So a column placement is never
# arbitrary — it is the component's row read in a different direction.
_SELECT_TOPIC = "gallery:select"


# --- typed prop descriptors --------------------------------------------------
#
# The inspector's props are typed, one frozen dataclass per kind, so the panel can
# pick a control per prop and illegal states stay unrepresentable: a text prop
# carries no numeric bounds, a number prop carries its range, an enum carries its
# choices. This mirrors the core's own `Binding = ArmBinding | ValueBinding` union.
# An editable kind renders its control (value field / color input / slider /
# segmented); a `DisplayProp` renders as read-only text — a structural or
# descriptive prop only the factory can change, which waits for the server render
# endpoint. The wiring is symmetric and lives entirely on the bus: the inspector
# control publishes on `<id>:prop:<name>` and the specimen listens there, so an
# inspector edit updates the live component; an editable descriptor's `follows`
# names the specimen's own publish topic, so interacting with the specimen moves
# the inspector control too. Both directions apply silently (an applied value is
# never republished), which is what makes the cycle loop-free.


@dataclass(frozen=True)
class TextProp:
    """An editable string prop — a length, a number-as-text, any CSS string.

    ``follows`` optionally names the specimen's publish topic, so the control
    tracks the live component's own edits.
    """

    name: str
    value: str
    follows: str | None = None


@dataclass(frozen=True)
class ColorProp:
    """An editable six-digit-hex color prop (``#rrggbb``).

    ``follows`` optionally names the specimen's publish topic, so the control
    tracks the live component's own edits.
    """

    name: str
    value: str
    follows: str | None = None


@dataclass(frozen=True)
class NumberProp:
    """An editable numeric prop bounded to ``[min, max]`` in ``step`` increments.

    ``follows`` optionally names the specimen's publish topic, so the control
    tracks the live component's own edits.
    """

    name: str
    value: float
    min: float
    max: float
    step: float = 1
    follows: str | None = None


@dataclass(frozen=True)
class EnumProp:
    """An editable one-of prop; ``choices`` are ordered ``(value, label)`` pairs.

    ``follows`` optionally names the specimen's publish topic, so the control
    tracks the live component's own edits.
    """

    name: str
    value: str
    choices: tuple[tuple[str, str], ...]
    follows: str | None = None


@dataclass(frozen=True)
class StructProp:
    """An editable structural prop: the edit changes the specimen's markup, which
    only the Python factory can produce.

    Its control publishes on the same ``<id>:prop:<name>`` convention as a value
    prop, but the subscriber is the remount island, which round-trips the edit
    through the server render endpoint: the factory re-renders the specimen and
    the client swaps the returned mount point in place. The browser never
    re-implements what the factory expresses.
    """

    name: str
    value: str


@dataclass(frozen=True)
class DisplayProp:
    """A prop shown read-only: descriptive, or not yet worth an editing surface."""

    name: str
    value: str


Prop = TextProp | ColorProp | NumberProp | EnumProp | StructProp | DisplayProp
"""One inspector prop row: an editable control chosen by kind, or read-only text."""


def _prop_topic(spec_id: str, name: str) -> str:
    """The bus topic an inspector edit of one prop travels on."""
    return f"{spec_id}:prop:{name}"


@dataclass(frozen=True)
class _Spec:
    """One gallery entry, projected into all three columns.

    ``body`` is the specimen island(s) the center renders (an invisible wiring
    island like ``theme_state`` is carried here too and floated to the end of the
    column so it adds no gap mid-content). ``props`` (typed descriptors, one per
    inspector row) and ``tokens`` are the inspector's two sections for this
    component. ``rebuild``, on a spec with structural props, re-runs the factory
    with edited prop values — the server render endpoint calls it, so the factory
    stays the single source of truth for the specimen's markup.
    """

    id: str
    name: str
    section: str
    body: tuple[Island, ...]
    props: tuple[Prop, ...]
    tokens: tuple[str, ...]
    rebuild: Callable[[Mapping[str, str]], Island] | None = None


def _specimen(island: Island, spec_id: str) -> Island:
    """Mark a rebuildable specimen's mount point (``sb-specimen-<id>``) so the
    remount island can find and replace it after a structural re-render."""
    return replace(island, class_=f"sb-specimen-{spec_id}")


def _modal_specimen(edits: Mapping[str, str]) -> Island:
    """The modal specimen; ``edits`` overrides its structural props."""
    return _specimen(
        modal(
            trigger="Open dialog",
            body=(
                "<p>A modal dialog in the top layer, with a focus trap and "
                "Esc to close.</p>"
            ),
            label="Example dialog",
            dialog_id="demo-modal",
            title=edits.get("title", "Dialog"),
        ),
        "modal",
    )


def _breadcrumb_specimen(edits: Mapping[str, str]) -> Island:
    """The breadcrumb specimen; ``edits`` overrides its structural props."""
    return _specimen(
        breadcrumb(
            trail=(("Showcase", "#"), ("Components", "#")),
            current=edits.get("current", "Breadcrumb"),
        ),
        "breadcrumb",
    )


def _collapsible_specimen(edits: Mapping[str, str]) -> Island:
    """The collapsible specimen; ``edits`` overrides its structural props.

    ``count`` is parsed here, so a non-numeric edit raises :class:`ValueError`
    exactly like any factory-rejected value: the endpoint surfaces it and the
    live specimen stays unchanged.
    """
    return _specimen(
        collapsible(
            title=edits.get("title", "Grouped items"),
            body=(
                "<p>Related items live in a collapsible section with a count "
                "badge; the disclosure is the native &lt;details&gt;.</p>"
            ),
            count=int(edits.get("count", "3")),
            open=True,
        ),
        "collapsible",
    )


def _gallery_specs() -> tuple[_Spec, ...]:
    """The component registry the three columns are projected from.

    The color picker and value field publish the same topics the preview's
    ``theme_state`` subscribes to, so editing either live-restyles the preview even
    though they sit in different sections — the bus crossing the gallery, which is
    the showcase's whole point.
    """
    return (
        _Spec(
            id="segmented",
            name="Segmented toggle",
            section="Controls",
            body=(
                segmented(
                    topic="view:changed",
                    options=(
                        ("overview", "Overview"),
                        ("api", "API"),
                        ("examples", "Examples"),
                    ),
                    value="overview",
                    label="View",
                    listen=_prop_topic("segmented", "value"),
                ),
            ),
            props=(
                EnumProp(
                    name="value",
                    value="overview",
                    choices=(
                        ("overview", "Overview"),
                        ("api", "API"),
                        ("examples", "Examples"),
                    ),
                    follows="view:changed",
                ),
                DisplayProp("topic", "view:changed"),
            ),
            tokens=(
                "--sb-color-accent",
                "--sb-color-muted",
                "--sb-border-width-accent",
            ),
        ),
        _Spec(
            id="slider",
            name="Slider",
            section="Controls",
            body=(
                slider(
                    topic="weight:changed",
                    min=200,
                    max=900,
                    step=10,
                    value=400,
                    label="Weight",
                    listen=_prop_topic("slider", "value"),
                ),
            ),
            props=(
                NumberProp(
                    name="value",
                    value=400,
                    min=200,
                    max=900,
                    step=10,
                    follows="weight:changed",
                ),
                DisplayProp("topic", "weight:changed"),
            ),
            tokens=("--sb-color-accent", "--sb-color-border", "--sb-fit-slider-thumb"),
        ),
        _Spec(
            id="color-picker",
            name="Color picker",
            section="Controls",
            body=(
                color_picker(
                    topic="token:accent",
                    value="#5b4bd6",
                    label="Accent",
                    listen=_prop_topic("color-picker", "value"),
                ),
            ),
            props=(
                ColorProp(name="value", value="#5b4bd6", follows="token:accent"),
                DisplayProp("topic", "token:accent"),
            ),
            tokens=("--sb-color-accent", "--sb-color-border", "--sb-color-handle-ring"),
        ),
        _Spec(
            id="popover",
            name="Popover",
            section="Controls",
            body=(
                popover(
                    trigger="Settings",
                    panel=(
                        "<p>A popover panel in the top layer.</p>"
                        '<button type="button">Action</button>'
                    ),
                    label="Settings",
                    panel_id="demo-popover",
                ),
            ),
            props=(
                DisplayProp("panel_id", "demo-popover"),
                DisplayProp("haspopup", "dialog"),
            ),
            tokens=("--sb-color-bg-raised", "--sb-color-border"),
        ),
        _Spec(
            id="modal",
            name="Modal",
            section="Controls",
            body=(_modal_specimen({}),),
            props=(
                StructProp("title", "Dialog"),
                DisplayProp("dialog_id", "demo-modal"),
            ),
            tokens=(
                "--sb-color-modal-scrim",
                "--sb-color-bg-raised",
                "--sb-color-border",
            ),
            rebuild=_modal_specimen,
        ),
        _Spec(
            id="value-field",
            name="Value field",
            section="Controls",
            body=(
                value_field(
                    topic="token:radius",
                    value="0",
                    label="Radius",
                    listen=_prop_topic("value-field", "value"),
                ),
            ),
            props=(
                TextProp(name="value", value="0", follows="token:radius"),
                DisplayProp("topic", "token:radius"),
            ),
            tokens=("--sb-color-fg", "--sb-color-border", "--sb-color-accent"),
        ),
        _Spec(
            id="preview",
            name="Live preview",
            section="Display",
            body=(
                preview(scope_id="preview-1"),
                theme_state(
                    scope='[data-sb-scope="preview-1"]',
                    bindings=(
                        ArmBinding(
                            topic="token:accent", token="--sb-color-accent", arm="light"
                        ),
                        ArmBinding(
                            topic="token:accent", token="--sb-color-accent", arm="dark"
                        ),
                        ValueBinding(topic="token:radius", token="--sb-radius-base"),
                    ),
                ),
            ),
            props=(
                DisplayProp("scope_id", "preview-1"),
                DisplayProp("binds", "accent · radius"),
            ),
            tokens=("--sb-color-bg", "--sb-color-fg", "--sb-font-family"),
        ),
        _Spec(
            id="table",
            name="Table",
            section="Display",
            body=(
                table(
                    columns=("Component", "Section", "Adapter"),
                    rows=(
                        ("segmented", "control", "yes"),
                        ("color picker", "control", "yes"),
                        ("slider", "control", "yes"),
                        ("preview", "display", "no"),
                        ("table", "display", "no"),
                        ("code block", "display", "copy only"),
                    ),
                    label="Component set",
                ),
            ),
            props=(DisplayProp("columns", "3"), DisplayProp("rows", "6")),
            tokens=(
                "--sb-color-border",
                "--sb-color-bg-raised",
                "--sb-font-tracking-wide",
            ),
        ),
        _Spec(
            id="code-block",
            name="Code block",
            section="Display",
            body=(
                code_block(
                    code=(
                        "from switchboard_ui.components import table\n"
                        "\n"
                        "grid = table(\n"
                        '    columns=("Name", "Role"),\n'
                        '    rows=(("accent", "interactive"),),\n'
                        '    label="Tokens",\n'
                        ")"
                    ),
                    label="Using the table component",
                    language="python",
                ),
            ),
            props=(DisplayProp("language", "python"), DisplayProp("copy", "true")),
            tokens=("--sb-color-bg-raised", "--sb-color-border", "--sb-color-accent"),
        ),
        _Spec(
            id="breadcrumb",
            name="Breadcrumb",
            section="Display",
            body=(_breadcrumb_specimen({}),),
            props=(
                StructProp("current", "Breadcrumb"),
                DisplayProp("trail", "Showcase / Components"),
            ),
            tokens=("--sb-color-muted", "--sb-color-subtle", "--sb-color-fg"),
            rebuild=_breadcrumb_specimen,
        ),
        _Spec(
            id="collapsible",
            name="Collapsible",
            section="Display",
            body=(_collapsible_specimen({}),),
            props=(
                StructProp("title", "Grouped items"),
                StructProp("count", "3"),
                DisplayProp("open", "true"),
            ),
            tokens=("--sb-color-border", "--sb-color-muted", "--sb-color-fg"),
            rebuild=_collapsible_specimen,
        ),
    )


def _gallery_heading(spec: _Spec) -> Island:
    """A specimen's heading — the nav's scroll target (the anchor ``id`` lands here)."""
    heading = element(
        "div",
        {
            "id": f"sec-{spec.id}",
            "class": "sb-gallery-heading",
            "role": "heading",
            "aria-level": "2",
        },
        [escape_text(spec.name)],
    )
    return Island(name="gallery-heading", initial=heading)


def _gallery_nav(specs: tuple[_Spec, ...]) -> Island:
    """The nav column: one mono link per specimen, grouped by section, first active.

    Each link is an in-page anchor (native scroll to the specimen's heading) whose
    adapter also publishes the selection on the bus, so the inspector follows.
    """
    items: list[str] = []
    section = ""
    for index, spec in enumerate(specs):
        if spec.section != section:
            section = spec.section
            items.append(
                element(
                    "div", {"class": "sb-gallery-nav-group"}, [escape_text(section)]
                )
            )
        items.append(
            element(
                "a",
                {
                    "class": "sb-gallery-nav-item",
                    "href": f"#sec-{spec.id}",
                    "data-id": spec.id,
                    "aria-current": "true" if index == 0 else "false",
                },
                [escape_text(spec.name)],
            )
        )
    nav = element("nav", {"class": "sb-gallery-nav", "aria-label": "Components"}, items)
    return Island(
        name="gallery-nav",
        props={"topic": _SELECT_TOPIC},
        publishes=(_SELECT_TOPIC,),
        initial=nav,
    )


def _prop_control(spec_id: str, prop: Prop) -> str:
    """The inspector's editor for one prop, rendered to HTML by the prop's kind.

    An editable kind renders its control's full mount point (via
    :func:`render_island`, so the already-registered adapter mounts it and the
    control is live), publishing on the prop's ``<id>:prop:<name>`` topic — the
    topic the specimen listens on, so the edit drives the live component. The
    control also listens on the descriptor's ``follows`` topic (the specimen's
    own publish topic), so interacting with the specimen moves this control. A
    ``DisplayProp`` renders as read-only text — a structural or descriptive prop
    only the factory can change.
    """
    topic = _prop_topic(spec_id, prop.name)
    label = _humanize(prop.name)
    match prop:
        case TextProp(value=value, follows=follows):
            return render_island(
                value_field(topic=topic, value=value, label=label, listen=follows)
            )
        case ColorProp(value=value, follows=follows):
            return render_island(
                color_input(topic=topic, value=value, label=label, listen=follows)
            )
        case NumberProp(value=value, min=low, max=high, step=step, follows=follows):
            return render_island(
                slider(
                    topic=topic,
                    min=low,
                    max=high,
                    value=value,
                    step=step,
                    label=label,
                    listen=follows,
                )
            )
        case EnumProp(value=value, choices=choices, follows=follows):
            return render_island(
                segmented(
                    topic=topic,
                    options=choices,
                    value=value,
                    label=label,
                    listen=follows,
                )
            )
        case StructProp(value=value):
            # A structural edit's control is the plain value field: it publishes
            # on the prop topic like any value prop, but the subscriber is the
            # remount island, which round-trips it through the render endpoint.
            return render_island(value_field(topic=topic, value=value, label=label))
        case DisplayProp(value=value):
            return element(
                "div",
                {"class": "sb-gallery-inspector-prop-value"},
                [escape_text(value)],
            )
    assert_never(prop)  # pragma: no cover


def _prop_row(spec_id: str, prop: Prop) -> str:
    """One inspector prop: the prop's name over its control (or read-only value)."""
    label = element(
        "div", {"class": "sb-gallery-inspector-prop-label"}, [escape_text(prop.name)]
    )
    return element(
        "div",
        {"class": "sb-gallery-inspector-prop"},
        [label, _prop_control(spec_id, prop)],
    )


def _inspector_panel(spec: _Spec, *, active: bool) -> str:
    """One inspector panel: the component's name, section, prop controls, and tokens.

    The props render as a column of controls, one per prop, chosen by the prop's
    type: an editable value prop is a live control driving the specimen, a structural
    or descriptive prop is read-only text. Only the active panel is shown at first
    paint; the adapter swaps them on selection.
    """
    title = element(
        "div", {"class": "sb-gallery-inspector-title"}, [escape_text(spec.name)]
    )
    section = element(
        "div", {"class": "sb-gallery-inspector-kind"}, [escape_text(spec.section)]
    )
    props_label = element(
        "div", {"class": "sb-gallery-inspector-label"}, [escape_text("Props")]
    )
    props = element(
        "div",
        {"class": "sb-gallery-inspector-props"},
        [_prop_row(spec.id, prop) for prop in spec.props],
    )
    tokens_label = element(
        "div", {"class": "sb-gallery-inspector-label"}, [escape_text("Tokens")]
    )
    tokens = element(
        "div",
        {"class": "sb-gallery-inspector-tokens"},
        [element("code", {}, [escape_text(token)]) for token in spec.tokens],
    )
    return element(
        "div",
        {
            "class": "sb-gallery-inspector-panel",
            "data-id": spec.id,
            "hidden": None if active else "",
        },
        [title, section, props_label, props, tokens_label, tokens],
    )


RENDER_ENDPOINT = "/render/island"
"""The URL the remount island POSTs structural edits to; the server routes it."""


def render_specimen(spec_id: str, edits: Mapping[str, str]) -> str:
    """Re-render one rebuildable specimen's mount point with edited structural props.

    The render endpoint's core: the Python factory re-runs with the edits (the
    single source of truth for the specimen's markup) and the client swaps the
    returned mount point in place. A spec without structural props, or an unknown
    id, raises :class:`KeyError`; an edit the factory rejects raises
    :class:`ValueError` and the live specimen stays unchanged.
    """
    for spec in _gallery_specs():
        if spec.id == spec_id:
            if spec.rebuild is None:
                raise KeyError(f"specimen {spec_id!r} has no structural props")
            return render_island(spec.rebuild(edits))
    raise KeyError(f"unknown specimen {spec_id!r}")


def _gallery_remount(specs: tuple[_Spec, ...]) -> Island:
    """The invisible round-trip island: structural edits re-render on the server.

    Subscribes every structural prop's ``<id>:prop:<name>`` topic. On an edit it
    POSTs the spec's full structural prop set to the render endpoint, then swaps
    the returned mount point over the live specimen (unmount, replace, boot).
    The factory re-renders; the browser never re-implements markup.
    """
    tracked = {
        spec.id: {p.name: p.value for p in spec.props if isinstance(p, StructProp)}
        for spec in specs
        if spec.rebuild is not None
    }
    topics = tuple(
        _prop_topic(spec_id, name)
        for spec_id, props in tracked.items()
        for name in props
    )
    return Island(
        name="gallery-remount",
        props={"endpoint": RENDER_ENDPOINT, "specs": tracked},
        subscribes=topics,
    )


def _gallery_inspector(specs: tuple[_Spec, ...]) -> Island:
    """The inspector column: every specimen's panel, only the first shown.

    Subscribes the selection topic; the adapter unhides the chosen panel and hides
    the rest, so the inspector tracks the nav across regions over the bus.
    """
    panels = [
        _inspector_panel(spec, active=index == 0) for index, spec in enumerate(specs)
    ]
    return Island(
        name="gallery-inspector",
        props={"topic": _SELECT_TOPIC},
        subscribes=(_SELECT_TOPIC,),
        initial=element("div", {"class": "sb-gallery-inspector"}, panels),
    )


def build_showcase() -> Document:
    """The component gallery as a nav | content | inspector tool.

    The three columns are projections of one registry: the nav (body-l) lists each
    component, the center (body-c) renders it under a section heading, and the
    inspector (body-r) shows its props and tokens. Selecting a nav item publishes
    ``gallery:select``; the inspector subscribes and swaps to that component's
    panel — the bus carrying a selection across regions, the same coordination the
    demo proves with counter → readout. Invisible wiring islands float to the end
    of the center column so they add no gap between specimens.
    """
    specs = _gallery_specs()
    content: list[Island] = []
    trailing: list[Island] = []
    section = ""
    for spec in specs:
        if spec.section != section:
            section = spec.section
            content.append(
                Island(
                    name="gallery-group",
                    initial=element(
                        "div",
                        {"class": "sb-gallery-group"},
                        [escape_text(spec.section)],
                    ),
                )
            )
        content.append(_gallery_heading(spec))
        for island in spec.body:
            (content if island.initial else trailing).append(island)
    regions: dict[Region, tuple[Island, ...]] = {
        "head-c": (surface_switch("gallery"),),
        "head-r": (mode_switch(),),
        "body-l": (_gallery_nav(specs),),
        # The remount and mode-state islands are invisible wiring; they trail the
        # content like the other zero-initial islands, so they add no gap
        # mid-column (and mode-state mounts after the toggles it syncs).
        "body-c": tuple(content + trailing + [_gallery_remount(specs), mode_state()]),
        "body-r": (_gallery_inspector(specs),),
        "foot-c": (Island(name="status", initial="component gallery"),),
    }
    # A wider right column than the default rail: the inspector holds props tables
    # and full token names, which the standard 200px inspector would clip.
    return three_column(regions, title="switchboard-ui showcase", right_width="20rem")


def showcase_scripts() -> tuple[str, ...]:
    """The adapters the gallery registers: each specimen's, plus the nav and inspector."""
    return (
        segmented_scripts()
        + popover_scripts()
        + color_picker_scripts()
        + color_input_scripts()
        + slider_scripts()
        + value_field_scripts()
        + theme_state_scripts()
        + code_block_scripts()
        + modal_scripts()
        + mode_switch_scripts()
        + (_GALLERY_NAV_JS, _GALLERY_INSPECTOR_JS, _GALLERY_REMOUNT_JS)
    )


# The gallery's own two islands — host chrome, not core components: a nav that
# publishes the selected component, and an inspector that subscribes and swaps to
# that component's panel. Inlined here (like the page CSS below) because they are
# showcase-local, not part of the shipped component set.
_GALLERY_NAV_JS = """
window.switchboard.register("gallery-nav", function (el, props, bus) {
  var items = Array.prototype.slice.call(
    el.querySelectorAll(".sb-gallery-nav-item")
  );
  function onClick(e) {
    var item = e.currentTarget;
    items.forEach(function (it) {
      it.setAttribute("aria-current", it === item ? "true" : "false");
    });
    bus.publish(props.topic, item.dataset.id);
  }
  items.forEach(function (it) {
    it.addEventListener("click", onClick);
  });
  return function teardown() {
    items.forEach(function (it) {
      it.removeEventListener("click", onClick);
    });
  };
});
"""

# The structural-edit round-trip: subscribe every structural prop topic; on an
# edit, POST the spec's full structural prop set to the render endpoint and swap
# the returned mount point over the live specimen (unmount -> replace -> boot,
# so the old island's bus subscriptions are released and the fresh one mounts).
# Edits are debounced per spec: a value field publishes per keystroke, and one
# round-trip per pause is enough. A rejected edit (the factory raised) or an
# absent server (static render) leaves the specimen unchanged — the factory is
# the only judge of a structural prop's validity.
_GALLERY_REMOUNT_JS = """
window.switchboard.register("gallery-remount", function (el, props, bus) {
  var offs = [];
  var timers = {};

  function rerender(id, state) {
    fetch(props.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: id, props: state }),
    })
      .then(function (res) {
        return res.ok ? res.text() : null;
      })
      .then(function (html) {
        if (html === null) return;
        var node = document.querySelector(".sb-specimen-" + id);
        if (!node) return;
        window.switchboard.unmount(node);
        var tpl = document.createElement("template");
        tpl.innerHTML = html;
        node.replaceWith(tpl.content);
        window.switchboard.boot();
      })
      .catch(function () {});
  }

  Object.keys(props.specs).forEach(function (id) {
    var state = props.specs[id];
    Object.keys(state).forEach(function (name) {
      offs.push(
        bus.subscribe(id + ":prop:" + name, function (value) {
          if (typeof value !== "string") return;
          state[name] = value;
          clearTimeout(timers[id]);
          timers[id] = setTimeout(function () {
            rerender(id, state);
          }, 200);
        })
      );
    });
  });

  return function teardown() {
    offs.forEach(function (off) {
      off();
    });
    Object.keys(timers).forEach(function (id) {
      clearTimeout(timers[id]);
    });
  };
});
"""


_GALLERY_INSPECTOR_JS = """
window.switchboard.register("gallery-inspector", function (el, props, bus) {
  var panels = Array.prototype.slice.call(
    el.querySelectorAll(".sb-gallery-inspector-panel")
  );
  function show(id) {
    panels.forEach(function (p) {
      p.hidden = p.dataset.id !== id;
    });
  }
  var off = bus.subscribe(props.topic, function (id) {
    if (typeof id === "string") show(id);
  });
  return function teardown() {
    off();
  };
});
"""


# The gallery's page chrome (host CSS, not the core's structure or the theme's
# paint): the column seams, the component nav, the content rhythm, and the
# inspector. It reads the theme's --sb-* tokens because the theme is loaded. The
# center column owns both internal seams (single-owner; the side columns draw
# neither). The nav's active item reserves the accent channel as a transparent
# inline-start border, recolored on selection, so the indicator never shifts the
# row (peer edge reservation).
_GALLERY_CSS = """
.sb-body-c {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
  gap: var(--sb-space-lg);
  padding: var(--sb-space-lg);
}
.sb-gallery-nav {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
  padding: var(--sb-space-md);
}
.sb-gallery-nav-group {
  color: var(--sb-color-faint);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
  font-size: var(--sb-font-size-sm);
}
.sb-gallery-nav-item {
  color: var(--sb-color-fg);
  text-decoration: none;
  border-inline-start: var(--sb-border-width-accent) solid transparent;
  padding: var(--sb-space-xs);
}
.sb-gallery-nav-item:hover {
  color: var(--sb-color-accent);
}
.sb-gallery-nav-item[aria-current="true"] {
  color: var(--sb-color-accent);
  border-inline-start-color: var(--sb-color-accent);
}
.sb-gallery-nav-item:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: -2px;
}
.sb-gallery-group {
  color: var(--sb-color-faint);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
}
.sb-gallery-heading {
  font-size: var(--sb-font-size-lg);
  font-weight: var(--sb-font-weight-bold);
}
.sb-gallery-inspector {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-md);
  padding: var(--sb-space-md);
}
.sb-gallery-inspector-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-sm);
}
/* Re-assert the hidden attribute: the display rule above outranks the UA
 * `[hidden] { display: none }`, so an inactive panel needs this to stay hidden. */
.sb-gallery-inspector-panel[hidden] {
  display: none;
}
.sb-gallery-inspector-title {
  font-weight: var(--sb-font-weight-bold);
}
.sb-gallery-inspector-kind {
  color: var(--sb-color-faint);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
  font-size: var(--sb-font-size-sm);
}
.sb-gallery-inspector-label {
  color: var(--sb-color-muted);
  font-size: var(--sb-font-size-sm);
}
.sb-gallery-inspector-tokens {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
}
.sb-gallery-inspector-props {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-sm);
}
.sb-gallery-inspector-prop {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
}
.sb-gallery-inspector-prop-label {
  color: var(--sb-color-muted);
  font-size: var(--sb-font-size-sm);
}
.sb-gallery-inspector-prop-value {
  color: var(--sb-color-fg);
}
"""


def showcase_styles() -> str:
    """The components' structural CSS plus the gallery's page chrome, for ``extra_head``."""
    sheets = "\n".join(
        (
            segmented_styles(),
            popover_styles(),
            color_picker_styles(),
            color_input_styles(),
            slider_styles(),
            value_field_styles(),
            preview_styles(),
            table_styles(),
            code_block_styles(),
            modal_styles(),
            breadcrumb_styles(),
            collapsible_styles(),
        )
    )
    return (
        f"<style>{sheets}</style><style>{_GALLERY_CSS}</style>"
        f"{surface_switch_styles()}{mode_switch_styles()}{mode_stamp_head()}"
    )


# --- the theme builder -------------------------------------------------------
#
# The capstone dogfood: an SBUI page that edits the theme's own token registry
# live. It iterates switchboard_theme's REGISTRY to generate one control per
# editable token, grouped by category, and binds each to a shared preview scope
# through a single theme_state island. A scheme-varying color is edited per arm
# (two controls, two ArmBindings) against a side-by-side light/dark preview; a
# scheme-invariant token is edited directly (one control, one ValueBinding). The
# Component Geometry contract (the `fit` category) is structural, not taste, so it
# is not exposed. The whole control surface is generated from the typed registry,
# so a new token appears in the builder the moment it lands in tokens.py.

_BUILDER_SCOPE = "builder-preview"
_HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")


def _humanize(text: str) -> str:
    """A token role or category as a label: ``bg-raised`` -> ``Bg Raised``."""
    return text.replace("-", " ").title()


def _static(name: str, text: str, class_: str) -> Island:
    """A label-only island: it renders its text and never mounts (no adapter)."""
    return Island(name=name, initial=escape_text(text), class_=class_)


def _control(*, type_: ValueType, value: str, topic: str, label: str) -> Island:
    """The editor for one token value: a swatch + hex color input for a hex
    color, else the general value field (lengths, numbers, families, the rgba
    scrim that is a color but not a hex)."""
    # color_input (swatch + hex), not the richer color_picker: the builder shows
    # one control per token, so the denser input keeps the palette compact.
    if type_ is ValueType.COLOR and _HEX.match(value):
        return color_input(topic=topic, value=value, label=label)
    return value_field(topic=topic, value=value, label=label)


def _token_row(token: Token) -> tuple[Frame, list[Binding]]:
    """One control row for a token, plus the binding(s) that apply its edits.

    A ``Themed`` token gets two controls (light / dark arm) on two topics and two
    arm bindings; a ``Fixed`` token gets one control and one value binding. The
    ``fit`` contract (the only ``Derived`` values) is filtered out before here.
    """
    label = _humanize(token.role)
    match token.value:
        case Themed(light=light, dark=dark):
            light_topic = f"{token.name}@light"
            dark_topic = f"{token.name}@dark"
            controls: tuple[Island, ...] = (
                _control(
                    type_=token.type,
                    value=light,
                    topic=light_topic,
                    label=f"{label} (light)",
                ),
                _control(
                    type_=token.type,
                    value=dark,
                    topic=dark_topic,
                    label=f"{label} (dark)",
                ),
            )
            bindings: list[Binding] = [
                ArmBinding(topic=light_topic, token=token.name, arm="light"),
                ArmBinding(topic=dark_topic, token=token.name, arm="dark"),
            ]
        case Fixed(value=value):
            controls = (
                _control(type_=token.type, value=value, topic=token.name, label=label),
            )
            bindings = [ValueBinding(topic=token.name, token=token.name)]
        case _:  # Derived: only the `fit` contract, excluded before this call.
            raise ValueError(f"{token.name} is derived and not editable")
    row = Frame(
        direction="row",
        children=(
            Slot(_static("builder-label", label, "sb-builder-label"), basis="9rem"),
            *controls,
        ),
        class_="sb-builder-row",
    )
    return row, bindings


def _category_id(category: Category) -> str:
    """The anchor id of a category's section header (the nav's scroll target)."""
    return f"builder-cat-{category.value}"


def _builder_section(category: Category) -> Island:
    """A category header in the controls column, carrying the nav's anchor id.

    The id sits on the header text so the nav's in-page link scrolls the controls
    column (the scroll owner) to this section.
    """
    head = element(
        "span",
        {"id": _category_id(category), "class": "sb-builder-section-anchor"},
        [escape_text(_humanize(category.value))],
    )
    return Island(name="builder-section", class_="sb-builder-section", initial=head)


def _builder_controls() -> tuple[Frame, list[Binding], list[Category]]:
    """The controls column: every editable token, grouped by category, plus the
    full binding list and the ordered categories the nav is projected from."""
    children: list[Island | Frame | Slot] = []
    bindings: list[Binding] = []
    categories: list[Category] = []
    for token in REGISTRY:
        if token.category is Category.FIT:
            continue
        if token.category not in categories:
            categories.append(token.category)
            children.append(_builder_section(token.category))
        row, row_bindings = _token_row(token)
        children.append(row)
        bindings.extend(row_bindings)
    column = Frame(
        direction="column",
        children=tuple(children),
        class_="sb-builder-controls sb-scroll",
    )
    return column, bindings, categories


def _builder_nav(categories: list[Category]) -> Island:
    """The category nav rail: one in-page link per token category.

    A static island (no adapter): each link scrolls the controls column to that
    category's section. The categories are the same list the controls are grouped
    by, so the nav and the controls never drift (one projection, two readings).
    """
    items = [
        element(
            "a",
            {"class": "sb-builder-nav-item", "href": f"#{_category_id(category)}"},
            [escape_text(_humanize(category.value))],
        )
        for category in categories
    ]
    nav = element(
        "nav", {"class": "sb-builder-nav", "aria-label": "Token categories"}, items
    )
    return Island(name="builder-nav", initial=nav)


def _builder_matrix() -> Island:
    """The preview matrix: each sample surface in its own box, rendered in a light
    cell (left) and a dark cell (right).

    Both cells of every box carry the builder scope, so one token edit repaints the
    matching arm in every cell at once. Replaces the two whole-pane previews; the
    per-item split puts each surface's two arms adjacent, so a token's effect on
    both schemes reads at the level of the surface it paints.
    """
    boxes: list[str] = []
    for item in preview_items():
        # sb-preview-scope (beyond data-sb-scope) re-establishes the full token
        # context on each cell (color plus the type base), so a font edit
        # repaints here too, not only color edits.
        cells = [
            element(
                "div",
                {
                    "class": (
                        f"sb-builder-matrix-cell sb-preview-scope sb-preview-{scheme}"
                    ),
                    "data-sb-scope": _BUILDER_SCOPE,
                },
                [item],
            )
            for scheme in ("light", "dark")
        ]
        boxes.append(element("div", {"class": "sb-builder-matrix-item"}, cells))
    matrix = element("div", {"class": "sb-builder-matrix"}, boxes)
    return Island(name="preview-matrix", initial=matrix)


def build_theme_builder() -> Document:
    """The theme builder page: a generated control panel beside a live light/dark
    preview, all wired to the registry's tokens through one theme_state island."""
    controls, bindings, categories = _builder_controls()
    scope = f'[data-sb-scope="{_BUILDER_SCOPE}"]'
    state = theme_state(scope=scope, bindings=tuple(bindings))
    # The matrix is the region's single child; the region owns the scroll, so the
    # stack of per-item boxes scrolls within it.
    preview_col = Frame(
        direction="column",
        children=(_builder_matrix(),),
        class_="sb-builder-preview sb-scroll",
    )
    # The surface switch stands alone flush-left (as in head-c on the gallery and
    # docs); the shared mode switch and the page-local export group flush-right,
    # at the opposite end from Gallery · Docs · Builder, so the toggles read as
    # settings rather than a fourth surface tab. No brand label — the active
    # Builder tab and the page title name the surface, as the gallery and docs do.
    header = Frame(
        direction="row",
        children=(
            surface_switch("builder"),
            Frame(
                direction="row",
                children=(
                    mode_switch(),
                    theme_export(scope=scope, bindings=tuple(bindings)),
                ),
                class_="sb-builder-header-right",
            ),
        ),
        class_="sb-rail sb-builder-header",
    )
    # Not the three_column preset the gallery and docs use. The builder has two
    # width-hungry regions (the controls column and the side-by-side light/dark
    # preview), so the preset's one flex column between two narrow rails does not
    # fit. A left nav rail plus a two-pane main keeps rail-consistency with the
    # other surfaces without starving the preview.
    main = Frame(
        direction="row",
        children=(
            Slot(_builder_nav(categories), basis="12rem"),
            Slot(controls, basis="32rem"),
            Slot(preview_col),
        ),
        class_="sb-builder-main",
    )
    # The mode-state applier (invisible) sits beside the theme-state applier, at
    # the body's tail so it mounts after the header toggles it syncs.
    body = Frame(
        direction="column",
        children=(header, Slot(main), state, mode_state()),
    )
    return Document(body=body, title="switchboard-ui theme builder")


def theme_builder_scripts() -> tuple[str, ...]:
    """The adapters the builder registers: the color input, the value field, the
    theme-state island that applies every edit, the export control, the mode
    toggles, and the shared applier that stamps the chosen modes on the root."""
    return (
        color_input_scripts()
        + value_field_scripts()
        + theme_state_scripts()
        + theme_export_scripts()
        + popover_scripts()
        + segmented_scripts()
        + mode_switch_scripts()
    )


# The builder's own page layout (host CSS, not the core's structure or the theme's
# paint): gaps, insets, and the section/label chrome for the control panel and the
# preview panes. It reads the theme's --sb-* tokens because the theme is loaded.
_BUILDER_CSS = """
/* Flush like the gallery/docs head-c cell: no padding of its own, so the switch
 * self-insets to the same 12px the other surfaces show (rather than double-padding
 * the switch's own inset). The export sits flush at the trailing edge (flush
 * chrome). The rail floor still gives the row its height, and the bottom seam
 * anchors it as chrome, matching the head row on the gallery and docs. */
.sb-builder-header {
  align-items: center;
  justify-content: space-between;
  font-weight: var(--sb-font-weight-bold);
  border-block-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
/* The surface switch stands alone flush-left (its self-inset keeps the alignment
 * the gallery and docs heads show); the modes control, then the export, group
 * flush-right (the header's space-between), at the opposite end from the surface
 * tabs, so neither reads as a further surface. */
.sb-builder-header-right {
  align-items: center;
  gap: var(--sb-space-md);
}
.sb-builder-nav {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-2xs);
  padding: var(--sb-space-md);
}
.sb-builder-nav-item {
  color: var(--sb-color-fg);
  text-decoration: none;
  padding: var(--sb-space-xs);
}
.sb-builder-nav-item:hover {
  color: var(--sb-color-accent);
}
.sb-builder-nav-item:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: -2px;
}
/* The controls column owns both vertical seams (single owner): the seam to the
 * nav on its inline-start, the seam to the preview on its inline-end. It is the
 * full-height flex cell of the main row, so each seam runs the column's whole
 * height. The nav and preview draw neither. A side rail that bordered its own
 * <nav> would stop the line where the content stops: island content is
 * display:block and does not stretch to the cell, so the seam would truncate.
 * Mirrors the gallery's center cell (.sb-body-c) owning both of its seams. */
.sb-builder-controls {
  gap: var(--sb-space-md);
  padding: var(--sb-space-lg);
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
/* A row keeps its natural height: it is an .sb-frame (min-block-size: 0), so
 * without this it would flex-shrink to nothing in the fixed-height scroll column
 * and clip its own controls. flex: 0 0 auto makes the column overflow and scroll
 * instead. */
.sb-builder-row {
  flex: 0 0 auto;
  align-items: center;
  gap: var(--sb-space-md);
}
.sb-builder-section {
  flex: 0 0 auto;
  color: var(--sb-color-muted);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
}
/* The anchor the nav scrolls to: keep the section clear of the column's top edge
 * when jumped to, rather than flush against it. */
.sb-builder-section-anchor {
  scroll-margin-block-start: var(--sb-space-md);
}
.sb-builder-label {
  color: var(--sb-color-fg);
}
/* The preview region holds the matrix and owns the scroll; its inset floats the
 * matrix off the controls seam and the viewport edge. */
.sb-builder-preview {
  padding: var(--sb-space-md);
}
"""


# The preview matrix's display chrome — the per-item box and its internal
# light|dark divider. This is display chrome, not page-layout chrome: like a
# component's own CSS it sits inside an island, so it is bundled with the component
# sheets and kept out of _BUILDER_CSS (the layout chrome the seam guard scans). The
# divider between the two shades is single-owned by the trailing (dark) cell, and
# the two cells stretch to equal height as flex-row siblings, so that seam runs the
# box's full height rather than truncating.
_MATRIX_CSS = """
.sb-builder-matrix {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-md);
}
.sb-builder-matrix-item {
  display: flex;
  flex-direction: row;
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-builder-matrix-cell {
  flex: 1 1 0;
  min-inline-size: 0;
  padding: var(--sb-space-md);
}
.sb-builder-matrix-cell + .sb-builder-matrix-cell {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
}
"""


def theme_builder_styles() -> str:
    """The builder's component CSS plus its own page layout, for ``extra_head``."""
    sheets = "\n".join(
        (
            color_input_styles(),
            value_field_styles(),
            preview_styles(),
            theme_export_styles(),
            popover_styles(),
            segmented_styles(),
            _MATRIX_CSS,
        )
    )
    return (
        f"<style>{sheets}</style><style>{_BUILDER_CSS}</style>"
        f"{surface_switch_styles()}{mode_switch_styles()}{mode_stamp_head()}"
    )
