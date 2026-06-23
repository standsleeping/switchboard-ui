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
``light-dark()`` (the arm model; see PF ``theme-layer.md`` and ``test_tokens.py``);
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
    # leaking the UA ::backdrop colour (no-UA-default).
    _color("popover-scrim", "rgb(0 0 0 / 0)", "rgb(0 0 0 / 0)"),
    # The colour-picker handle ring. Near-white so the drag handle stays visible
    # over any spectrum colour beneath it, in either scheme (TOKEN_PAIR_CONTRAST
    # against an unknown ground).
    _color("handle-ring", "#ffffff", "#f6f7f9"),
    # Type. A UI family + a prose family, a small size scale, weights, line-height,
    # and tracking. Recursive's variable-font axes are a builder extension, not core.
    Token(
        Category.FONT,
        "family",
        ValueType.FONT_FAMILY,
        Fixed('ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace'),
    ),
    Token(
        Category.FONT,
        "family-prose",
        ValueType.FONT_FAMILY,
        Fixed("ui-sans-serif, system-ui, sans-serif"),
    ),
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
    Token(
        Category.FIT,
        "rail-block",
        ValueType.LENGTH,
        Derived("var(--sb-fit-control-block)"),
    ),
    # Colour-picker geometry: the square saturation/value surface, its slim hue
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
    # Slider geometry: the thumb is a square this tall, and the input is the same
    # height so the thumb centres with no margin (banned) or transform (forbidden).
    Token(Category.FIT, "slider-thumb", ValueType.LENGTH, Fixed("0.875rem")),
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
  font-size: var(--sb-font-size-base);
  line-height: var(--sb-font-line-height);
}

/* The fixed head and foot rails read as chrome, separated by a hairline. */
.sb-head-l,
.sb-head-c,
.sb-head-r {
  border-bottom: var(--sb-border-width-thin) solid var(--sb-color-border);
}
.sb-foot-l,
.sb-foot-c,
.sb-foot-r {
  border-top: var(--sb-border-width-thin) solid var(--sb-color-border);
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
  outline-offset: -2px;
}

/* Segmented toggle: a small-set selector. Mono tabs over a transparent ground;
 * the selected tab carries the accent underline. The class beats the base
 * `button` paint by specificity, so an option is not an accent button. Every
 * option reserves the underline as a transparent accent-width block-end border,
 * recoloured only when selected, so moving the selection never shifts layout
 * (PEER_EDGE_RESERVATION, state-stable geometry: the width is on the base rule,
 * the selected rule only recolours). */
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
 * the live value (an inline background the adapter sets); the theme owns only its
 * frame. The field is a standard control — square inset, the bg surface, a
 * hairline border, the accent caret, and an inset focus ring. An invalid hex
 * recolours the border to danger (a state recolour, never a reshape). The
 * non-default form surfaces (caret, placeholder, selection) are tokenised so no
 * UA colour leaks (the no-UA-default rule). */
.sb-color-input {
  gap: var(--sb-space-xs);
}
.sb-color-input-swatch {
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
  outline-offset: -2px;
}
.sb-color-input-text[aria-invalid="true"] {
  border-color: var(--sb-color-danger);
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
 * to a hairline; its colour is the live value set inline). The spectrum surfaces
 * carry a hairline frame and an inset focus ring; their gradients are adapter-set
 * data-viz, not theme paint. The handle/thumb carry a near-white ring that reads
 * over any spectrum colour. */
.sb-color-picker-swatch {
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
  outline-offset: -2px;
}
.sb-color-picker-area-handle,
.sb-color-picker-hue-thumb {
  border: var(--sb-border-width-accent) solid var(--sb-color-handle-ring);
  border-radius: var(--sb-radius-base);
}

/* Slider: a native range, fully restyled off the UA accent (no-UA-default). The
 * track groove is a thin centred line drawn on the input's own background; the
 * track pseudo is transparent at full height, so the square accent thumb — itself
 * the full input height — centres with no margin (banned) and no transform
 * (forbidden). `appearance: none` strips the UA chrome. */
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
  block-size: var(--sb-fit-slider-thumb);
  background: var(--sb-color-accent);
  border-radius: var(--sb-radius-base);
}
.sb-slider-input::-moz-range-thumb {
  inline-size: var(--sb-fit-slider-thumb);
  block-size: var(--sb-fit-slider-thumb);
  background: var(--sb-color-accent);
  border: none;
  border-radius: var(--sb-radius-base);
}
.sb-slider-input:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: -2px;
}
.sb-slider-value {
  font: inherit;
  color: var(--sb-color-muted);
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


def render_css() -> str:
    """Render the full default theme CSS from the registry."""
    return "\n\n".join((_HEADER, _render_root(), _render_modes(), _PAINT)) + "\n"
