"""Build the showcase document(s) through the public API.

Mirrors the package's own ``demo.py`` build / ``cli.py`` serve split: this module
returns what to render; :mod:`showcase.server` serves and hot-reloads it. Phase 1
grows the component gallery here — each island and preset rendered on a
self-rendered page, the forcing function the theme and components are shaped
against. Its inhabitants so far: the segmented toggle, a popover, and the colour
picker (which composes the popover).

A component ships three parts; the host wires each. :func:`build_showcase` places
the islands, :func:`showcase_scripts` carries the adapters (for ``extra_scripts``),
and :func:`showcase_styles` carries the structural CSS (for ``extra_head``, beside
the theme). That is the same opt-in a real host performs.
"""

import re
from typing import Literal

from switchboard_theme import REGISTRY, Category, Fixed, Themed, Token, ValueType
from switchboard_ui import Document, Island
from switchboard_ui.components import (
    ArmBinding,
    Binding,
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
from switchboard_ui.html import escape_text
from switchboard_ui.model import Frame, Region, Slot
from switchboard_ui.presets import three_column


def build_showcase() -> Document:
    """The showcase page. Phase 1: the component gallery, growing one control at a time."""
    regions: dict[Region, tuple[Island, ...]] = {
        "head-c": (Island(name="brand", initial="switchboard-ui"),),
        "body-c": (
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
            preview(scope_id="preview-1"),
            # Binds the colour picker's topic to the preview's accent token, so
            # editing the colour live-restyles the preview (and only the preview).
            # One pane, so both arms move together: two arm bindings on the one
            # topic. The builder edits the arms on separate topics for independent
            # light/dark themes.
            theme_state(
                scope='[data-sb-scope="preview-1"]',
                bindings=(
                    ArmBinding(
                        topic="token:accent", token="--sb-color-accent", arm="light"
                    ),
                    ArmBinding(
                        topic="token:accent", token="--sb-color-accent", arm="dark"
                    ),
                    # A scheme-invariant token edited directly: the value field
                    # publishes a length string, written straight onto the radius.
                    ValueBinding(topic="token:radius", token="--sb-radius-base"),
                ),
            ),
        ),
        "body-l": (
            popover(
                trigger="Settings",
                panel=(
                    "<p>A popover panel in the top layer.</p>"
                    '<button type="button">Action</button>'
                ),
                label="Settings",
                panel_id="demo-popover",
            ),
            slider(
                topic="weight:changed",
                min=200,
                max=900,
                step=10,
                value=400,
                label="Weight",
            ),
            value_field(topic="token:radius", value="0", label="Radius"),
        ),
        "body-r": (
            color_picker(topic="token:accent", value="#5b4bd6", label="Accent"),
        ),
        "foot-c": (Island(name="status", initial="component gallery"),),
    }
    return three_column(regions, title="switchboard-ui showcase")


def showcase_scripts() -> tuple[str, ...]:
    """The island adapters the showcase page registers (the picker pairs the popover)."""
    return (
        segmented_scripts()
        + popover_scripts()
        + color_picker_scripts()
        + slider_scripts()
        + value_field_scripts()
        + theme_state_scripts()
    )


# A showcase-only visualization (paint, not structure): outline the nine
# three_column regions so the layout grid reads as a 3x3. Kept out of the default
# theme, which stays flat (rail hairlines only). Every seam is a border with a
# single owner: the root owns the perimeter, each row owns its full-width
# horizontal seam through the theme, and the centre column owns both internal
# column seams (its inline-start and inline-end borders; the side columns draw
# neither). The empty-cell override is scoped to direct row children: it reveals
# the complete demo grid without inventing application content. `box-sizing:
# border-box` keeps the fixed root inside the viewport. See
# docs/explanation/seams.md for the ownership map.
_GRID_DEMO = """
.sb-root {
  box-sizing: border-box;
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-head-row > .sb-frame:empty,
.sb-body-row > .sb-frame:empty,
.sb-foot-row > .sb-frame:empty {
  display: flex;
}
.sb-head-c, .sb-body-c, .sb-foot-c {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-inline-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
"""


def showcase_styles() -> str:
    """The components' structural CSS plus the grid visualization, for ``extra_head``."""
    sheets = "\n".join(
        (
            segmented_styles(),
            popover_styles(),
            color_picker_styles(),
            slider_styles(),
            value_field_styles(),
            preview_styles(),
        )
    )
    return f"<style>{sheets}</style><style>{_GRID_DEMO}</style>"


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
