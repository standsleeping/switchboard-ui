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
    # Type.
    Token(
        Category.FONT,
        "family",
        ValueType.FONT_FAMILY,
        Fixed('ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace'),
    ),
    Token(Category.FONT, "size-base", ValueType.LENGTH, Fixed("0.9375rem")),
    Token(Category.FONT, "line-height", ValueType.NUMBER, Fixed("1.5")),
    # Space. The control inset, a semantic token the density modes reassign.
    Token(Category.SPACE, "inset", ValueType.LENGTH, Fixed("0.75rem")),
    # Border width.
    Token(Category.BORDER_WIDTH, "thin", ValueType.LENGTH, Fixed("1px")),
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
  padding: var(--sb-space-inset);
  min-width: var(--sb-fit-control-inline);
  cursor: pointer;
}
button:focus-visible {
  outline: 2px solid var(--sb-color-accent);
  outline-offset: -2px;
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
    """The ``:root`` block: color-scheme plus every token, grouped by category."""
    blocks = [
        "  /* Drives the native scrollbar and form chrome to match in both schemes. */",
        "  color-scheme: light dark;",
    ]
    for category in Category:
        tokens = [t for t in REGISTRY if t.category is category]
        if not tokens:
            continue
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
