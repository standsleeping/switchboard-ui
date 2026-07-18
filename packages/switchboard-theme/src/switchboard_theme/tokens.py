"""The token registry: the single source of truth for the default theme.

``static/default.css`` is *generated* from this module, not hand-edited. Every token
is a typed record carrying its category (the ``--sb-<category>-*`` name prefix, a
closed enum) and its value type (what the builder edits). The category enum is the
finite, maintained source of truth that earlier lived only as a naming convention: a
new category is a deliberate edit to :class:`Category`, caught by the type checker,
never an accident in a string. That closed enum, plus the fact that every token's
classification now sits in one reviewable place, is what keeps the categories from
eroding.

Scheme-varying tokens are authored per ``-light`` / ``-dark`` arm and composed with
``light-dark()`` (the arm model; see ``test_tokens.py``);
the renderer applies that rule so it cannot be gotten wrong. The Component Geometry
Contract (``--sb-fit-*``) is a :class:`Derived` value, a ``calc()`` over the causes.

Tiebreak for the inevitable hybrids: a token's category is its dominant value type. A
shadow lives in ``shadow`` even though its color varies by scheme; the scheme variance
rides the arm model, an orthogonal axis, not a second category.

Regenerate after editing this module:

    uv run --directory packages/switchboard-theme python -c \\
        "from switchboard_theme.tokens import render_css; \\
         import switchboard_theme, pathlib; \\
         (pathlib.Path(switchboard_theme.__file__).parent / 'static' / 'default.css') \\
             .write_text(render_css(), encoding='utf-8')"

``test_generated.py`` fails the build if the committed CSS drifts from this source.
"""

from dataclasses import dataclass
from enum import Enum
from typing import assert_never


class Category(Enum):
    """The token's namespace category: the ``--sb-<category>-*`` name prefix.

    A closed set. Adding a category is a deliberate edit here (the anti-erosion
    gate); it cannot drift in as a stray prefix string.
    """

    COLOR = "color"
    FONT = "font"
    SPACE = "space"
    RADIUS = "radius"
    BORDER_WIDTH = "border-width"
    SHADOW = "shadow"
    FIT = "fit"


class ValueType(Enum):
    """The token's value type: what the builder edits and how it validates."""

    COLOR = "color"
    LENGTH = "length"
    NUMBER = "number"
    FONT_FAMILY = "font-family"
    SHADOW = "shadow"


@dataclass(frozen=True)
class Themed:
    """A scheme-varying value: authored per arm, composed with ``light-dark()``."""

    light: str
    dark: str


@dataclass(frozen=True)
class Fixed:
    """A scheme-invariant value: a single declaration."""

    value: str


@dataclass(frozen=True)
class Derived:
    """A value computed from other tokens (a ``calc()`` / ``var()`` expression)."""

    expr: str


@dataclass(frozen=True)
class Token:
    """One design token: its category (name prefix), value type, and value."""

    category: Category
    role: str
    type: ValueType
    value: Themed | Fixed | Derived

    @property
    def name(self) -> str:
        """The CSS custom-property name, ``--sb-<category>-<role>``."""
        return f"--sb-{self.category.value}-{self.role}"


def _color(role: str, light: str, dark: str) -> Token:
    """A scheme-varying color token (the common case)."""
    return Token(Category.COLOR, role, ValueType.COLOR, Themed(light, dark))


def _len(category: Category, role: str, value: str) -> Token:
    """A scheme-invariant length token."""
    return Token(category, role, ValueType.LENGTH, Fixed(value))


def _num(role: str, value: str) -> Token:
    """A unitless number token (weights, line-height) in the font category."""
    return Token(Category.FONT, role, ValueType.NUMBER, Fixed(value))


REGISTRY: tuple[Token, ...] = (
    # Color: scheme-varying, authored per -light / -dark arm.
    _color("bg", "#ffffff", "#16181d"),
    _color("bg-raised", "#f6f7f9", "#1c1f27"),
    _color("fg", "#1b1d22", "#e6e8ec"),
    _color("muted", "#6b7280", "#9aa1ad"),
    _color("subtle", "#9ca3af", "#6b7280"),
    _color("border", "#e3e5e9", "#2b2f37"),
    _color("accent", "#5b4bd6", "#9d8bff"),
    _color("accent-fg", "#ffffff", "#16181d"),
    _color("danger", "#c2334b", "#ff6b81"),
    _color("danger-fg", "#ffffff", "#16181d"),
    # The popover backdrop. Transparent by default (a non-modal popover does not
    # dim the page); arms so a host can opt into a faint scrim per scheme without
    # leaking the UA ::backdrop color (no-UA-default).
    _color("popover-scrim", "rgb(0 0 0 / 0)", "rgb(0 0 0 / 0)"),
    # The modal backdrop. Unlike the popover scrim it dims the page (a modal is
    # the sole focus); darker in the dark scheme so the dimming reads against the
    # darker ground. Arms keep it off the UA ::backdrop color (no-UA-default).
    _color("modal-scrim", "rgb(0 0 0 / 0.4)", "rgb(0 0 0 / 0.6)"),
    # The color-picker handle ring. Near-white so the drag handle stays visible
    # over any spectrum color beneath it, in either scheme (holding contrast
    # against an unknown ground).
    _color("handle-ring", "#ffffff", "#f6f7f9"),
    # Type. One variable typeface (Recursive) carries every role; the UI and prose
    # families differ only in their fallback stacks, because the real distinction is
    # the axis tokens below. The face itself ships in this distribution's static/
    # (recursive.woff2, OFL) and is delivered by the host via font_head(); a page
    # without it degrades to the system stacks.
    Token(
        Category.FONT,
        "family",
        ValueType.FONT_FAMILY,
        Fixed(
            '"Recursive", ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas,'
            " monospace"
        ),
    ),
    Token(
        Category.FONT,
        "family-prose",
        ValueType.FONT_FAMILY,
        Fixed('"Recursive", ui-sans-serif, system-ui, sans-serif'),
    ),
    # Variable-font axis positions: MONO (proportional 0 to monospace 1) and CASL
    # (linear 0 to casual 1). The UI arm is strict mono; the prose arm is
    # proportional with a warm cast. Weight stays on font-weight (the registered
    # wght axis follows it), so these settings never fight the weight tokens.
    _num("axis-mono", "1"),
    _num("axis-casual", "0"),
    _num("axis-mono-prose", "0"),
    _num("axis-casual-prose", "0.36"),
    _len(Category.FONT, "size-sm", "0.8125rem"),
    _len(Category.FONT, "size-base", "0.9375rem"),
    _len(Category.FONT, "size-lg", "1.125rem"),
    _num("weight-normal", "400"),
    _num("weight-medium", "500"),
    _num("weight-bold", "700"),
    _num("line-height", "1.5"),
    _len(Category.FONT, "tracking", "0"),
    _len(Category.FONT, "tracking-wide", "0.04em"),
    # Space: a step scale plus the control inset (a semantic token the density modes
    # reassign, distinct from the scale so density does not move every md use).
    _len(Category.SPACE, "2xs", "0.125rem"),
    _len(Category.SPACE, "xs", "0.25rem"),
    _len(Category.SPACE, "sm", "0.5rem"),
    _len(Category.SPACE, "md", "0.75rem"),
    _len(Category.SPACE, "lg", "1rem"),
    _len(Category.SPACE, "xl", "1.5rem"),
    _len(Category.SPACE, "inset", "0.75rem"),
    # Radius: base is 0 (square default, the common token); steps for opt-in rounding.
    _len(Category.RADIUS, "base", "0"),
    _len(Category.RADIUS, "sm", "0.125rem"),
    _len(Category.RADIUS, "lg", "0.375rem"),
    # Border width. Border color is --sb-color-border.
    _len(Category.BORDER_WIDTH, "thin", "1px"),
    _len(Category.BORDER_WIDTH, "accent", "2px"),
    # Shadow: none by default (the look has no shadows); shadow-sm is the themed step
    # a host opts into (its color varies by scheme, so it gets arms).
    Token(Category.SHADOW, "base", ValueType.SHADOW, Fixed("none")),
    Token(
        Category.SHADOW,
        "sm",
        ValueType.SHADOW,
        Themed("0 1px 2px rgb(0 0 0 / 0.08)", "0 1px 2px rgb(0 0 0 / 0.45)"),
    ),
    # Component Geometry Contract: obligations projected from the causes above; the
    # only theme values structure consumes (test_contract.py).
    Token(
        Category.FIT,
        "control-block",
        ValueType.LENGTH,
        Derived(
            "calc(var(--sb-font-size-base) * var(--sb-font-line-height)"
            " + 2 * var(--sb-space-inset) + 2 * var(--sb-border-width-thin))"
        ),
    ),
    Token(Category.FIT, "control-inline", ValueType.LENGTH, Fixed("6rem")),
    # The minimum pointer-target square (24px): the block-size floor an
    # interactive control's hit area must grant even when its visual reads
    # smaller. Interaction geometry is an obligation like any other, so it is
    # published here rather than guessed per control.
    Token(Category.FIT, "hit-target", ValueType.LENGTH, Fixed("1.5rem")),
    Token(
        Category.FIT,
        "rail-block",
        ValueType.LENGTH,
        Derived("var(--sb-fit-control-block)"),
    ),
    # Color-picker geometry: the square saturation/value surface, its slim hue
    # track (one control-block tall, so it reads as a control row and reprojects
    # under density), and the drag handle.
    Token(Category.FIT, "color-area", ValueType.LENGTH, Fixed("12rem")),
    Token(
        Category.FIT,
        "color-hue",
        ValueType.LENGTH,
        Derived("var(--sb-fit-control-block)"),
    ),
    Token(Category.FIT, "color-handle", ValueType.LENGTH, Fixed("0.75rem")),
    # Slider geometry: the thumb's inline size. Its block size is the hit-target
    # obligation — the input is exactly that tall and the thumb fills the height,
    # so it centers with no margin (banned) or transform (forbidden) while the
    # whole control grants the minimum pointer target.
    Token(Category.FIT, "slider-thumb", ValueType.LENGTH, Fixed("0.875rem")),
    # Modal geometry: the dialog's max width (it caps at this or the viewport,
    # whichever is smaller) and its max height. The block cap stops short of the
    # full viewport so a band of scrim stays visible around the dialog — it reads
    # as an overlay on the page, never as a page itself.
    Token(Category.FIT, "modal-inline", ValueType.LENGTH, Fixed("32rem")),
    Token(Category.FIT, "modal-block", ValueType.LENGTH, Fixed("90dvb")),
)


@dataclass(frozen=True)
class Mode:
    """A density mode: reassigns cause tokens on :root; the contract reprojects."""

    name: str
    overrides: tuple[tuple[str, str], ...]


MODES: tuple[Mode, ...] = (
    Mode(
        "compact",
        (("--sb-font-size-base", "0.875rem"), ("--sb-space-inset", "0.5rem")),
    ),
    Mode(
        "spacious",
        (("--sb-font-size-base", "1rem"), ("--sb-space-inset", "1rem")),
    ),
)


_SECTION: dict[Category, str] = {
    Category.COLOR: "Color: scheme-varying, authored per -light / -dark arm (test_tokens.py).",
    Category.FONT: "Type.",
    Category.SPACE: "Space.",
    Category.RADIUS: "Radius.",
    Category.BORDER_WIDTH: "Border width.",
    Category.SHADOW: "Shadow.",
    Category.FIT: "Contract: projected from the causes above; the only values structure consumes.",
}

_HEADER = """\
/* switchboard-ui default theme -- GENERATED from tokens.py; do not edit here.
 *
 * Rendered from the typed token registry in tokens.py (the source of truth). Edit
 * tokens there and regenerate; test_generated.py fails the build if this file drifts.
 * The theme paints the mechanism's hooks with --sb-* tokens; scheme-varying colors
 * use the -light / -dark arm model so the builder edits each scheme value
 * (test_tokens.py). */"""

_PAINT = """\
/* The viewport surface: the mechanism's root frame fills it (position: fixed;
 * inset: 0), so the surface paint belongs here, not on body. */
.sb-root {
  background: var(--sb-color-bg);
  color: var(--sb-color-fg);
  font-family: var(--sb-font-family);
  font-variation-settings: "MONO" var(--sb-font-axis-mono), "CASL" var(--sb-font-axis-casual);
  font-size: var(--sb-font-size-base);
  line-height: var(--sb-font-line-height);
}

/* The head and foot rails read as chrome. Each full-width horizontal seam has
 * one row owner; border-box keeps the hairline inside the rail's promised size. */
.sb-head-row,
.sb-foot-row {
  box-sizing: border-box;
}
.sb-head-row {
  border-block-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-foot-row {
  border-block-start: var(--sb-border-width-thin) solid var(--sb-color-border);
}

/* The single accent signals "interactive". Square inset plus a min-width floor for
 * short labels (the published control-inline obligation), never asymmetric padding.
 * The ring draws inside the box (negative offset) so a clipping ancestor can't clip
 * it. */
button {
  font: inherit;
  color: var(--sb-color-accent-fg);
  background: var(--sb-color-accent);
  border: var(--sb-border-width-thin) solid var(--sb-color-accent);
  border-radius: var(--sb-radius-base);
  padding: var(--sb-space-inset);
  min-width: var(--sb-fit-control-inline);
  cursor: pointer;
}
button:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}

/* Segmented toggle: a small-set selector. Mono tabs over a transparent ground;
 * the selected tab carries the accent underline. The class beats the base
 * `button` paint by specificity, so an option is not an accent button. Every
 * option reserves the underline as a transparent accent-width block-end border,
 * recolored only when selected, so moving the selection never shifts layout
 * (state-stable geometry: the width is on the base rule,
 * the selected rule only recolors). */
.sb-segmented {
  gap: var(--sb-space-sm);
}
.sb-segmented-option {
  font: inherit;
  min-width: 0;
  color: var(--sb-color-muted);
  background: none;
  border: none;
  border-block-end: var(--sb-border-width-accent) solid transparent;
  padding: var(--sb-space-sm);
  cursor: pointer;
}
.sb-segmented-option[aria-checked="true"] {
  color: var(--sb-color-fg);
  border-block-end-color: var(--sb-color-accent);
}
.sb-segmented-sep {
  color: var(--sb-color-subtle);
}

/* Color input: a swatch plus a hex field, a tokenised stand-in for the native
 * <input type="color"> (whose picker popover cannot be themed). The swatch shows
 * the live value: the factory carries it as the per-instance `--sb-swatch` value
 * (a value, not a registry token, and not an inline paint declaration) and the
 * theme paints `background` from it here, so paint stays the theme's. The field
 * is a standard control — square inset, the bg surface, a hairline border, the
 * accent caret, and an inset focus ring. An invalid hex recolors the border to
 * danger (a state recolor, never a reshape). The non-default form surfaces
 * (caret, placeholder, selection) are tokenised so no UA color leaks (the
 * no-UA-default rule). */
.sb-color-input {
  gap: var(--sb-space-xs);
}
.sb-color-input-swatch {
  background: var(--sb-swatch);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
}
.sb-color-input-text {
  font: inherit;
  color: var(--sb-color-fg);
  background: var(--sb-color-bg);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
  padding: var(--sb-space-inset);
  caret-color: var(--sb-color-accent);
}
.sb-color-input-text::placeholder {
  color: var(--sb-color-subtle);
}
.sb-color-input-text::selection {
  color: var(--sb-color-accent-fg);
  background: var(--sb-color-accent);
}
.sb-color-input-text:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}
.sb-color-input-text[aria-invalid="true"] {
  border-color: var(--sb-color-danger);
}

/* Value field: the general single-line editor for a scheme-invariant token
 * (length, number, font family, shadow). The same field look as the color
 * input's hex field — square inset, the bg surface, a hairline border, the accent
 * caret and an inset focus ring — with the non-default form surfaces (caret,
 * placeholder, selection) tokenised so no UA color leaks (the no-UA-default
 * rule). */
.sb-value-field-text {
  font: inherit;
  color: var(--sb-color-fg);
  background: var(--sb-color-bg);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
  padding: var(--sb-space-inset);
  caret-color: var(--sb-color-accent);
}
.sb-value-field-text::placeholder {
  color: var(--sb-color-subtle);
}
.sb-value-field-text::selection {
  color: var(--sb-color-accent-fg);
  background: var(--sb-color-accent);
}
.sb-value-field-text:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}

/* Popover: a non-modal floating panel rendered in the top layer. Flat by the
 * house default — a raised surface, a hairline border for separation (no
 * shadow), square corners. The trigger carries no special paint (it inherits the
 * embedded control's look). No position/transform: the adapter positions the
 * panel inline, the UA top-layers it. */
.sb-popover-panel {
  background: var(--sb-color-bg-raised);
  color: var(--sb-color-fg);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
  box-shadow: var(--sb-shadow-base);
  padding: var(--sb-space-inset);
}
.sb-popover-panel::backdrop {
  background: var(--sb-color-popover-scrim);
}

/* Color picker: the swatch is a chip trigger (the base button paint, re-bordered
 * to a hairline; its color is the live value the factory carries as the
 * per-instance `--sb-swatch` value, painted here, not declared inline — the
 * background overrides the base button fill by class specificity). The spectrum
 * surfaces carry a hairline frame and an inset focus ring; their gradients are
 * adapter-set data-viz, not theme paint. The handle/thumb carry a near-white ring
 * that reads over any spectrum color. */
.sb-color-picker-swatch {
  background: var(--sb-swatch);
  border-color: var(--sb-color-border);
}
.sb-color-picker-controls {
  gap: var(--sb-space-sm);
}
.sb-color-picker-area,
.sb-color-picker-hue {
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
}
.sb-color-picker-area:focus-visible,
.sb-color-picker-hue:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}
.sb-color-picker-area-handle,
.sb-color-picker-hue-thumb {
  border: var(--sb-border-width-accent) solid var(--sb-color-handle-ring);
  border-radius: var(--sb-radius-base);
}

/* Slider: a native range, fully restyled off the UA accent (no-UA-default). The
 * track groove is a thin centered line drawn on the input's own background; the
 * track pseudo is transparent at full height, so the accent thumb — itself the
 * full input height, the published hit-target obligation — centers with no
 * margin (banned) and no transform (forbidden). `appearance: none` strips the
 * UA chrome. */
.sb-slider {
  gap: var(--sb-space-sm);
}
.sb-slider-input {
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  background: linear-gradient(
    to bottom,
    transparent calc(50% - var(--sb-border-width-thin)),
    var(--sb-color-border) calc(50% - var(--sb-border-width-thin)),
    var(--sb-color-border) calc(50% + var(--sb-border-width-thin)),
    transparent calc(50% + var(--sb-border-width-thin))
  );
}
.sb-slider-input::-webkit-slider-runnable-track {
  block-size: 100%;
  background: none;
}
.sb-slider-input::-moz-range-track {
  block-size: 100%;
  background: none;
}
.sb-slider-input::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  inline-size: var(--sb-fit-slider-thumb);
  block-size: var(--sb-fit-hit-target);
  background: var(--sb-color-accent);
  border-radius: var(--sb-radius-base);
}
.sb-slider-input::-moz-range-thumb {
  inline-size: var(--sb-fit-slider-thumb);
  block-size: var(--sb-fit-hit-target);
  background: var(--sb-color-accent);
  border: none;
  border-radius: var(--sb-radius-base);
}
.sb-slider-input:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}
.sb-slider-value {
  font: inherit;
  color: var(--sb-color-muted);
}

/* Live preview pane: a sample surface separated from the editing chrome by a
 * hairline. `color-scheme` on the scheme variants pins a pane to one arm (a
 * side-by-side light/dark preview). The scope re-establishes the full token
 * context — color and the type base (family / size / line-height) — rather than
 * inheriting computed values from the root, so a scoped edit to *any* of those
 * tokens reprojects inside the pane (the live theme builder depends on this). The
 * table is the canonical display surface: collapsed hairline cells with a raised
 * header row. */
.sb-preview {
  border-inline-start: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-preview-scope {
  background: var(--sb-color-bg);
  color: var(--sb-color-fg);
  font-family: var(--sb-font-family);
  font-variation-settings: "MONO" var(--sb-font-axis-mono), "CASL" var(--sb-font-axis-casual);
  font-size: var(--sb-font-size-base);
  line-height: var(--sb-font-line-height);
}
.sb-preview-light {
  color-scheme: light;
}
.sb-preview-dark {
  color-scheme: dark;
}
.sb-preview-sample {
  gap: var(--sb-space-lg);
}
.sb-preview-heading {
  font-weight: var(--sb-font-weight-bold);
}
.sb-preview-prose {
  font-family: var(--sb-font-family-prose);
  font-variation-settings: "MONO" var(--sb-font-axis-mono-prose), "CASL" var(--sb-font-axis-casual-prose);
  color: var(--sb-color-muted);
}
.sb-preview-swatch {
  background: var(--sb-color-accent);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-preview-table {
  border-collapse: collapse;
}
.sb-preview-table th,
.sb-preview-table td {
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  padding: var(--sb-space-sm);
  text-align: start;
}
.sb-preview-table th {
  background: var(--sb-color-bg-raised);
  font-weight: var(--sb-font-weight-bold);
}

/* Export control: the button carries the base button paint; the status note
 * beside it is muted, set off by a gap. */
.sb-export {
  gap: var(--sb-space-sm);
}
.sb-export-status {
  color: var(--sb-color-muted);
}

/* Table: the canonical structured-data surface. Collapsed hairline cells over the
 * page surface; the header row reads as a structural label band — a raised
 * surface, mono semibold uppercase with wide tracking — while the body cells stay
 * natural case. Square corners, no zebra: the grid reads from the hairlines and
 * the header band alone. Values align to the start edge (logical, so it follows
 * writing direction). */
.sb-table-grid {
  border-collapse: collapse;
  background: var(--sb-color-bg);
  color: var(--sb-color-fg);
}
.sb-table-grid th,
.sb-table-grid td {
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  padding: var(--sb-space-sm);
  text-align: start;
}
.sb-table-grid th {
  background: var(--sb-color-bg-raised);
  font-weight: var(--sb-font-weight-bold);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
}

/* Code block: a raised, hairline-bordered surface. A chrome strip (a muted
 * uppercase language tag, the copy action) sits over the code area, separated by a
 * hairline seam the chrome owns at its block-end. The code is mono (the UI family
 * already is) at the small size and never wraps (`white-space: pre`); the area
 * owns the horizontal scroll declared in the structural sheet. The copy button is
 * a quiet accent-text action, not the accent fill — it beats the base `button`
 * paint by class specificity and drops the inline floor so a short label is not
 * stretched to the control-inline width — so it recedes into the chrome. */
.sb-code {
  background: var(--sb-color-bg-raised);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
}
.sb-code-chrome {
  gap: var(--sb-space-sm);
  padding: var(--sb-space-sm);
  border-block-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-code-lang {
  color: var(--sb-color-muted);
  font-size: var(--sb-font-size-sm);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
}
.sb-code-actions {
  gap: var(--sb-space-sm);
}
.sb-code-copy {
  font: inherit;
  min-width: 0;
  color: var(--sb-color-accent);
  background: none;
  border: none;
  padding: var(--sb-space-xs);
  cursor: pointer;
}
.sb-code-copy:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}
.sb-code-status {
  color: var(--sb-color-muted);
  font-size: var(--sb-font-size-sm);
}
.sb-code-pre {
  padding: var(--sb-space-inset);
  color: var(--sb-color-fg);
  font-size: var(--sb-font-size-sm);
  white-space: pre;
}
.sb-code-text {
  font-family: var(--sb-font-family);
  font-variation-settings: "MONO" var(--sb-font-axis-mono), "CASL" var(--sb-font-axis-casual);
}

/* Modal: a centered dialog over a dimming scrim. The surface is the raised color
 * with a hairline border and square corners (flat by the house default; the scrim
 * supplies the elevation, not a shadow). The header lays a bold title against a
 * quiet close control. The trigger keeps the base button paint. The browser owns
 * the centering, the focus trap, and Esc through `showModal()`; the theme paints
 * only the surfaces. */
.sb-modal-dialog {
  background: var(--sb-color-bg-raised);
  color: var(--sb-color-fg);
  border: var(--sb-border-width-thin) solid var(--sb-color-border);
  border-radius: var(--sb-radius-base);
  box-shadow: var(--sb-shadow-base);
  padding: var(--sb-space-inset);
  gap: var(--sb-space-md);
}
.sb-modal-dialog::backdrop {
  background: var(--sb-color-modal-scrim);
}
.sb-modal-header {
  gap: var(--sb-space-md);
}
.sb-modal-title {
  font-weight: var(--sb-font-weight-bold);
}
.sb-modal-close {
  font: inherit;
  min-width: 0;
  color: var(--sb-color-muted);
  background: none;
  border: none;
  padding: var(--sb-space-xs);
  cursor: pointer;
}
.sb-modal-close:hover {
  color: var(--sb-color-fg);
}
.sb-modal-close:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}

/* Breadcrumb: a trail of muted ancestor links and subtle separators ending at the
 * current page — the one crumb in the foreground color, and not a link. Links
 * recede until hovered, when they take the accent. */
.sb-breadcrumb {
  gap: var(--sb-space-sm);
}
.sb-breadcrumb-link {
  color: var(--sb-color-muted);
  text-decoration: none;
}
.sb-breadcrumb-link:hover {
  color: var(--sb-color-accent);
}
.sb-breadcrumb-link:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}
.sb-breadcrumb-sep {
  color: var(--sb-color-subtle);
}
.sb-breadcrumb-current {
  color: var(--sb-color-fg);
}

/* Collapsible section: a flat disclosure, separated from its neighbours by a
 * hairline rather than boxed. The summary is a bold header row — a +/- marker and
 * the title against a muted count — that takes the accent on hover; the native
 * disclosure marker is suppressed (no-UA-default) for the tokenised +/- one. The
 * body insets the revealed content. */
.sb-collapsible {
  border-block-end: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-collapsible-summary {
  gap: var(--sb-space-md);
  padding: var(--sb-space-sm);
  color: var(--sb-color-fg);
  font-weight: var(--sb-font-weight-bold);
  cursor: pointer;
  list-style: none;
}
.sb-collapsible-summary::-webkit-details-marker {
  display: none;
}
.sb-collapsible-summary:hover {
  color: var(--sb-color-accent);
}
.sb-collapsible-summary:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: calc(-1 * var(--sb-border-width-accent));
}
.sb-collapsible-label {
  gap: var(--sb-space-sm);
}
.sb-collapsible-marker::before {
  content: "+";
  color: var(--sb-color-muted);
}
.sb-collapsible[open] .sb-collapsible-marker::before {
  content: "-";
}
.sb-collapsible-count {
  color: var(--sb-color-muted);
}
.sb-collapsible-body {
  padding: var(--sb-space-sm);
  color: var(--sb-color-fg);
}"""


def _render_value(token: Token) -> str:
    """The declaration(s) for one token: arms + composition, or a single line."""
    match token.value:
        case Themed(light=light, dark=dark):
            return (
                f"  {token.name}-light: {light};\n"
                f"  {token.name}-dark: {dark};\n"
                f"  {token.name}: light-dark(var({token.name}-light), var({token.name}-dark));"
            )
        case Fixed(value=value):
            return f"  {token.name}: {value};"
        case Derived(expr=expr):
            return f"  {token.name}: {expr};"
    assert_never(token.value)  # pragma: no cover


def _render_root() -> str:
    """The ``:root`` block: color-scheme plus every token, grouped by category.

    Categories are grouped from the registry in declaration order (which matches the
    enum order), so the section order follows the data and an unpopulated category
    simply never appears.
    """
    groups: dict[Category, list[Token]] = {}
    for token in REGISTRY:
        groups.setdefault(token.category, []).append(token)
    blocks = [
        "  /* Drives the native scrollbar and form chrome to match in both schemes. */",
        "  color-scheme: light dark;",
    ]
    for category, tokens in groups.items():
        joiner = "\n\n" if any(isinstance(t.value, Themed) for t in tokens) else "\n"
        blocks.append("")
        blocks.append(f"  /* {_SECTION[category]} */")
        blocks.append(joiner.join(_render_value(t) for t in tokens))
    body = "\n".join(blocks)
    return f":root {{\n{body}\n}}"


def _render_modes() -> str:
    """The ``[data-density]`` rules: each reassigns cause tokens (test_density.py)."""
    rules: list[str] = []
    for mode in MODES:
        decls = "\n".join(f"  {name}: {value};" for name, value in mode.overrides)
        rules.append(
            f'/* Density mode "{mode.name}": reassigns cause tokens; the --sb-fit-*\n'
            f" * contract reprojects automatically (test_density.py). */\n"
            f':root[data-density="{mode.name}"] {{\n{decls}\n}}'
        )
    return "\n\n".join(rules)


# Scheme pinning: the page follows the OS (the :root `color-scheme: light dark`)
# until the host stamps `data-scheme`, which pins every light-dark() token to one
# arm; removing the attribute returns to auto. The attribute contract mirrors the
# density modes' `data-density`: one root attribute per mode axis.
_SCHEME_PIN = """\
/* Scheme pinning: stamping data-scheme on the root pins every light-dark()
 * token to one arm; removing it returns to the OS scheme. */
:root[data-scheme="light"] {
  color-scheme: light;
}
:root[data-scheme="dark"] {
  color-scheme: dark;
}"""


def render_css() -> str:
    """Render the full default theme CSS from the registry."""
    return (
        "\n\n".join((_HEADER, _render_root(), _render_modes(), _SCHEME_PIN, _PAINT))
        + "\n"
    )
