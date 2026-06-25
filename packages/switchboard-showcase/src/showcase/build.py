"""Build the showcase document(s) through the public API.

Mirrors the package's own ``demo.py`` build / ``cli.py`` serve split: this module
returns what to render; :mod:`showcase.server` serves and hot-reloads it. It builds
two pages:

- :func:`build_showcase` — the component gallery: each island and preset rendered
  on a self-rendered page, the forcing function the theme and components are shaped
  against (the segmented toggle, popover, colour picker, slider, value field, and a
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
from dataclasses import dataclass
from typing import Literal

from switchboard_theme import REGISTRY, Category, Fixed, Themed, Token, ValueType
from switchboard_ui import Document, Island
from switchboard_ui.components import (
    ArmBinding,
    Binding,
    ValueBinding,
    code_block,
    code_block_scripts,
    code_block_styles,
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
# registry (`_gallery_specs`): the nav lists each component, the centre renders it,
# and the inspector shows its props and tokens. So a column placement is never
# arbitrary — it is the component's row read in a different direction.
_SELECT_TOPIC = "gallery:select"


@dataclass(frozen=True)
class _Spec:
    """One gallery entry, projected into all three columns.

    ``body`` is the specimen island(s) the centre renders (an invisible wiring
    island like ``theme_state`` is carried here too and floated to the end of the
    column so it adds no gap mid-content). ``props`` and ``tokens`` are the
    inspector's two sections for this component.
    """

    id: str
    name: str
    section: str
    body: tuple[Island, ...]
    props: tuple[tuple[str, str], ...]
    tokens: tuple[str, ...]


def _gallery_specs() -> tuple[_Spec, ...]:
    """The component registry the three columns are projected from.

    The colour picker and value field publish the same topics the preview's
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
                ),
            ),
            props=(("topic", "view:changed"), ("options", "overview · api · examples")),
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
                ),
            ),
            props=(("topic", "weight:changed"), ("range", "200-900"), ("step", "10")),
            tokens=("--sb-color-accent", "--sb-color-border", "--sb-fit-slider-thumb"),
        ),
        _Spec(
            id="color-picker",
            name="Colour picker",
            section="Controls",
            body=(color_picker(topic="token:accent", value="#5b4bd6", label="Accent"),),
            props=(("topic", "token:accent"), ("value", "#5b4bd6")),
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
            props=(("panel_id", "demo-popover"), ("haspopup", "dialog")),
            tokens=("--sb-color-bg-raised", "--sb-color-border"),
        ),
        _Spec(
            id="value-field",
            name="Value field",
            section="Controls",
            body=(value_field(topic="token:radius", value="0", label="Radius"),),
            props=(("topic", "token:radius"), ("value", "0")),
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
            props=(("scope_id", "preview-1"), ("binds", "accent · radius")),
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
                        ("colour picker", "control", "yes"),
                        ("slider", "control", "yes"),
                        ("preview", "display", "no"),
                        ("table", "display", "no"),
                        ("code block", "display", "copy only"),
                    ),
                    label="Component set",
                ),
            ),
            props=(("columns", "3"), ("rows", "6")),
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
            props=(("language", "python"), ("copy", "true")),
            tokens=("--sb-color-bg-raised", "--sb-color-border", "--sb-color-accent"),
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


def _inspector_panel(spec: _Spec, *, active: bool) -> str:
    """One inspector panel: the component's name, section, props table, and tokens.

    The props reuse the `table` component (its rendered ``initial`` markup, so the
    panel gets the table paint without nesting a second island). Only the active
    panel is shown at first paint; the adapter swaps them on selection.
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
    props = table(
        columns=("Prop", "Value"), rows=spec.props, label=f"{spec.name} props"
    ).initial
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
    component, the centre (body-c) renders it under a section heading, and the
    inspector (body-r) shows its props and tokens. Selecting a nav item publishes
    ``gallery:select``; the inspector subscribes and swaps to that component's
    panel — the bus carrying a selection across regions, the same coordination the
    demo proves with counter → readout. Invisible wiring islands float to the end
    of the centre column so they add no gap between specimens.
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
        "head-c": (Island(name="brand", initial="switchboard-ui"),),
        "body-l": (_gallery_nav(specs),),
        "body-c": tuple(content + trailing),
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
        + slider_scripts()
        + value_field_scripts()
        + theme_state_scripts()
        + code_block_scripts()
        + (_GALLERY_NAV_JS, _GALLERY_INSPECTOR_JS)
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
# centre column owns both internal seams (single-owner; the side columns draw
# neither). The nav's active item reserves the accent channel as a transparent
# inline-start border, recoloured on selection, so the indicator never shifts the
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
  color: var(--sb-color-muted);
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
  color: var(--sb-color-muted);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
}
.sb-gallery-heading {
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
  color: var(--sb-color-muted);
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
"""


def showcase_styles() -> str:
    """The components' structural CSS plus the gallery's page chrome, for ``extra_head``."""
    sheets = "\n".join(
        (
            segmented_styles(),
            popover_styles(),
            color_picker_styles(),
            slider_styles(),
            value_field_styles(),
            preview_styles(),
            table_styles(),
            code_block_styles(),
        )
    )
    return f"<style>{sheets}</style><style>{_GALLERY_CSS}</style>"


# --- the theme builder -------------------------------------------------------
#
# The capstone dogfood: an SBUI page that edits the theme's own token registry
# live. It iterates switchboard_theme's REGISTRY to generate one control per
# editable token, grouped by category, and binds each to a shared preview scope
# through a single theme_state island. A scheme-varying colour is edited per arm
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
    """The editor for one token value: a swatch + hex colour input for a hex
    colour, else the general value field (lengths, numbers, families, the rgba
    scrim that is a colour but not a hex)."""
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
            Slot(_static("builder-label", label, "sb-builder-label"), basis="11rem"),
            *controls,
        ),
        class_="sb-builder-row",
    )
    return row, bindings


def _builder_controls() -> tuple[Frame, list[Binding]]:
    """The controls column: every editable token, grouped by category, plus the
    full binding list the one theme_state island applies to the preview scope."""
    children: list[Island | Frame | Slot] = []
    bindings: list[Binding] = []
    seen: set[Category] = set()
    for token in REGISTRY:
        if token.category is Category.FIT:
            continue
        if token.category not in seen:
            seen.add(token.category)
            children.append(
                _static(
                    "builder-section",
                    _humanize(token.category.value),
                    "sb-builder-section",
                )
            )
        row, row_bindings = _token_row(token)
        children.append(row)
        bindings.extend(row_bindings)
    column = Frame(
        direction="column",
        children=tuple(children),
        class_="sb-builder-controls sb-scroll",
    )
    return column, bindings


def _builder_pane(scheme: Literal["light", "dark"], label: str) -> Frame:
    """One preview pane pinned to a colour scheme, sharing the builder scope so a
    scoped edit repaints it (the arm matching its scheme; both for a value edit)."""
    return Frame(
        direction="column",
        children=(
            _static("builder-pane-label", label, "sb-builder-pane-label"),
            preview(scope_id=_BUILDER_SCOPE, scheme=scheme),
        ),
        class_="sb-builder-pane sb-scroll",
    )


def build_theme_builder() -> Document:
    """The theme builder page: a generated control panel beside a live light/dark
    preview, all wired to the registry's tokens through one theme_state island."""
    controls, bindings = _builder_controls()
    scope = f'[data-sb-scope="{_BUILDER_SCOPE}"]'
    state = theme_state(scope=scope, bindings=tuple(bindings))
    preview_col = Frame(
        direction="row",
        children=(
            Slot(_builder_pane("light", "Light")),
            Slot(_builder_pane("dark", "Dark")),
        ),
        class_="sb-builder-preview",
    )
    header = Frame(
        direction="row",
        children=(
            _static("brand", "theme builder", "sb-builder-brand"),
            theme_export(scope=scope, bindings=tuple(bindings)),
        ),
        class_="sb-rail sb-builder-header",
    )
    main = Frame(
        direction="row",
        children=(Slot(controls, basis="34rem"), Slot(preview_col)),
        class_="sb-builder-main",
    )
    body = Frame(direction="column", children=(header, Slot(main), state))
    return Document(body=body, title="switchboard-ui theme builder")


def theme_builder_scripts() -> tuple[str, ...]:
    """The adapters the builder registers: the colour input, the value field, the
    theme-state island that applies every edit, and the export control."""
    return (
        color_input_scripts()
        + value_field_scripts()
        + theme_state_scripts()
        + theme_export_scripts()
    )


# The builder's own page layout (host CSS, not the core's structure or the theme's
# paint): gaps, insets, and the section/label chrome for the control panel and the
# preview panes. It reads the theme's --sb-* tokens because the theme is loaded.
_BUILDER_CSS = """
.sb-builder-header {
  align-items: center;
  justify-content: space-between;
  padding: var(--sb-space-inset);
  font-weight: var(--sb-font-weight-bold);
}
.sb-builder-controls {
  gap: var(--sb-space-md);
  padding: var(--sb-space-lg);
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
.sb-builder-label {
  color: var(--sb-color-fg);
}
.sb-builder-pane {
  gap: var(--sb-space-sm);
  padding: var(--sb-space-md);
}
.sb-builder-pane-label {
  color: var(--sb-color-muted);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
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
        )
    )
    return f"<style>{sheets}</style><style>{_BUILDER_CSS}</style>"
