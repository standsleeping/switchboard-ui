"""The token reference page: rendered from the registry, exactly like the CSS.

``docs/reference/tokens.md`` is *generated* from :mod:`switchboard_theme.tokens`,
not hand-edited. Every token table on that page is projected from ``REGISTRY`` (and
the density table from ``MODES``), so a token cannot enter the registry without
appearing on the page: the two cannot drift apart. Each token's Role column is its
``doc`` field, which is why that field is required rather than a comment.

The page's prose is the part no registry can supply, so it lives here as literal
blocks in the order the sections appear.

Regenerate with ``just generate``; ``test_generated.py`` fails the build if the
committed page drifts from this source.
"""

from typing import assert_never

from switchboard_theme.tokens import (
    MODES,
    REGISTRY,
    Category,
    Derived,
    Fixed,
    Themed,
    Token,
    ValueType,
)


def _ticked(values: tuple[str, ...]) -> str:
    """A comma-separated list with every item in code ticks."""
    return ", ".join(f"`{value}`" for value in values)


def _table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> str:
    """A GitHub-flavoured markdown table."""
    head = "| " + " | ".join(headers) + " |"
    rule = "|" + "|".join("---" for _ in headers) + "|"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join((head, rule, body))


def _of(category: Category) -> tuple[Token, ...]:
    """Every registry token in one category, in registry order."""
    return tuple(token for token in REGISTRY if token.category is category)


def _default(token: Token) -> str:
    """The token's default as the page shows it: a Themed value as light-dark()."""
    match token.value:
        case Themed(light=light, dark=dark):
            return f"light-dark({light}, {dark})"
        case Fixed(value=value):
            return value
        case Derived(expr=expr):
            return expr
    assert_never(token.value)  # pragma: no cover


def _arms(token: Token) -> tuple[str, str]:
    """The two authored arms of a scheme-varying token."""
    match token.value:
        case Themed(light=light, dark=dark):
            return light, dark
        case _:  # pragma: no cover - every color token is authored per arm
            raise ValueError(f"{token.name} is not scheme-varying")


def _color_table() -> str:
    """Token, both arms, role: the color category authors a value per scheme."""
    rows: list[tuple[str, ...]] = []
    for token in _of(Category.COLOR):
        light, dark = _arms(token)
        rows.append((f"`{token.name}`", f"`{light}`", f"`{dark}`", token.doc))
    return _table(("Token", "Light", "Dark", "Role"), tuple(rows))


def _token_table(
    category: Category, *, value: str = "Default", role: str = "Role"
) -> str:
    """Token, value, role for one category; the two column labels vary by section."""
    rows = tuple(
        (f"`{token.name}`", f"`{_default(token)}`", token.doc)
        for token in _of(category)
    )
    return _table(("Token", value, role), rows)


def _density_table() -> str:
    """One row per mode, one column per cause token the modes reassign.

    The default row is read from the registry rather than restated, so the three
    rows are all the same fact seen at three densities.
    """
    causes = tuple(name for name, _ in MODES[0].overrides)
    defaults = {token.name: _default(token) for token in REGISTRY}
    rows: list[tuple[str, ...]] = [
        ("default (no attribute)", *(f"`{defaults[c]}`" for c in causes))
    ]
    for mode in MODES:
        overrides = dict(mode.overrides)
        rows.append(
            (
                f"`{mode.name}`",
                *(f"`{overrides.get(c, defaults[c])}`" for c in causes),
            )
        )
    return _table(("Mode", *(f"`{c}`" for c in causes)), tuple(rows))


_HEAD = """\
<!-- GENERATED from switchboard_theme/reference.py; do not edit here.

Every table below is projected from the typed token registry in tokens.py (the
source of truth) and the prose lives in reference.py. Edit those and run `just
generate`; test_generated.py fails the build if this page drifts. -->

# Theme tokens

The theme is configured entirely through CSS custom properties, the `--sb-*` tokens. They are defined in a typed registry, `switchboard_theme.tokens`, from which both the shipped `static/default.css` and this page are rendered. A host re-themes by overriding any token; the structural layer never reads a token except the `--sb-fit-*` contract. This page lists every token and its default.

## Naming

Every token name is `--sb-<category>-<role>`. The `<category>` is one of a closed set; the `<role>` is everything after it and may itself contain hyphens (`bg-raised`, `accent-fg`, `control-block`).

A scheme-varying token expands to three properties: the two authored arms `--sb-<category>-<role>-light` and `--sb-<category>-<role>-dark`, plus the composed `--sb-<category>-<role>` defined as `light-dark(var(…-light), var(…-dark))`. The composition is generated, never hand-written. The OS color scheme (or a `color-scheme` pinned on a subtree) chooses the arm.

## The registry

`switchboard_theme.tokens` is the single source of truth. `default.css` is rendered from it by `render_css()`, this page by `render_reference()`, and both carry a "do not edit here" header. `test_generated.py` fails the build if either artifact drifts from the registry."""


_COLOR_NOTE = """\
The default surface reads flat: `bg-raised` is only a faint step from `bg`, present as the hook a host needs for a real raised surface. Meaning is carried by text and weight rather than color, so `success` / `warning` / `info` are not defined until a component needs them; `danger` ships because forms need an error state, and the `diag-*` pair ships scoped to before/after code annotation."""


_TYPE_NOTE = """\
Type tokens stay generic (family, size, weight, line-height, tracking), so the toolkit is not coupled to one typeface; the default theme names one. Both family tokens lead with Recursive, a single variable font whose axes carry the role distinction: the `--sb-font-axis-*` tokens hold the MONO (proportional `0` to monospace `1`) and CASL (linear `0` to casual `1`) positions for the UI and prose arms, and the theme's paint sets `font-variation-settings` from them wherever it sets a family. Weight is never driven through the axis tokens: `font-weight` maps to the registered `wght` axis on its own, so the weight tokens keep working against the variable face and synthesize against the fallbacks.

The display four (`size-display`, `weight-display`, `line-height-display`, `tracking-tight`) are consumed together wherever a page title is set, so an `h1` reads as display type rather than as a bolder body line. `--sb-font-measure` caps running text at a comfortable line length; it is a property of the type, not of the layout, which is why it sits here rather than beside the content column's cap in the `--sb-fit-*` contract.

### Typeface delivery

The face ships in the theme distribution as `static/recursive.woff2` (licensed under the SIL Open Font License; the license text ships beside it). A binary cannot ride the inline `<style>` seam, so delivery is the host's: serve `switchboard_theme.font_bytes()` at a URL you own and prepend `switchboard_theme.font_head(url)` to `extra_head`. A page without the font block degrades to the system stacks in the family tokens."""


_SPACE_NOTE = """\
`--sb-space-inset` is a separate semantic token, not a step on the scale: it is the inset a control applies to its own content, and density moves it without disturbing the scale steps. It happens to share `0.75rem` with `md` at the default density.

The scale itself spans two ranges. `2xs` through `xl` are the chrome range, the gaps and insets of controls, rails and table cells; `2xl` and `3xl` are the document range, where a reading column needs more room than a control-sized gap."""


_RADIUS_NOTE = """\
Components use `--sb-radius-base`, which is `0`, so the default look is square. A host rounds the whole UI by setting `--sb-radius-base`, or reaches for a step where differential rounding is wanted."""


_BORDER_NOTE = """\
Border *color* is not in this category: it is `--sb-color-border`, over in color. A token's category is its value type, so the width and the color of one hairline live apart."""


_SHADOW_NOTE = """\
The default look has no shadows: components use `--sb-shadow-base`, which is `none`. `--sb-shadow-sm` is a themed step a host opts into; its color varies by scheme, so it carries arms. A shadow stays in the `shadow` category even when its color varies, because the category names the dominant value type and scheme variance rides the arm axis."""


_FIT_INTRO = """\
The `--sb-fit-*` tokens are `Derived` or `Fixed` obligations projected from the cause tokens above. They are the only theme values the structural layer is allowed to read (see [Ownership](../explanation/ownership.md)). Structure consumes a fit token as a floor; it never defines one."""


_FIT_NOTE = """\
`control-block` is the one computed root. Because `rail-block` and `color-hue` alias it, a rail row and the hue track are guaranteed the same height as a control and reproject together."""


_DENSITY_INTRO = """\
`MODES` renders one `:root[data-density="<name>"]` rule per mode. Each mode reassigns only the cause tokens; because `--sb-fit-control-block` is a `calc()` over them, the whole contract reprojects automatically."""


_DENSITY_NOTE = """\
Set `data-density` on `:root` to switch. Nothing else is overridden directly: the control inset is a dedicated token precisely so density can move it without touching the space scale, and everything sized off `control-block` follows."""


_TAIL = """\
## Scheme pinning

The scheme is the second mode axis, with the same attribute contract. By default the page follows the OS: `:root` declares `color-scheme: light dark`, and every scheme-varying token composes through `light-dark()`. Setting `data-scheme="light"` or `data-scheme="dark"` on `:root` pins `color-scheme` to that arm, which flips every composed token at once; removing the attribute returns to auto. Pinning flows only through `color-scheme`: no individual color is restated.

## Per-instance values

A few paint rules read a custom property that is not a registry token: the color-input and color-picker swatches paint `background: var(--sb-swatch)`. The factory carries that value per instance (the current color), so it never appears in `:root`. Auditing the registry against the CSS will show this `var()` with no matching definition; that is by design, not a missing token.

## See also

- [Ownership](../explanation/ownership.md): the floor-and-surface split (tokens are the surface), and the `--sb-fit-*` contract as the one channel from theme to structure.
- [The workbench preset](workbench.md): the structural CSS that consumes the fit tokens."""


def _registry_table() -> str:
    """The registry's own pieces. The two closed enums list themselves."""
    categories = _ticked(tuple(category.value for category in Category))
    value_types = _ticked(tuple(value_type.value for value_type in ValueType))
    return _table(
        ("Piece", "Role"),
        (
            (
                "`Category` (enum)",
                f"The closed namespace: {categories}. A new category is a deliberate"
                " edit, caught by the type checker; it cannot drift in as a stray"
                " prefix.",
            ),
            (
                "`ValueType` (enum)",
                f"What the value is and how the builder edits it: {value_types}.",
            ),
            (
                "`Themed(light, dark)`",
                "A scheme-varying value; renders the two arms plus the `light-dark()`"
                " composition.",
            ),
            ("`Fixed(value)`", "A single scheme-invariant declaration."),
            (
                "`Derived(expr)`",
                "A `calc()`/`var()` expression over other tokens (the `--sb-fit-*`"
                " contract).",
            ),
            (
                "`Token`",
                "A frozen record: `category`, `role`, `type`, `value`, `doc`. Its"
                " `name` property builds the `--sb-…` string and its `doc` is the Role"
                " column below, so a token arrives documented.",
            ),
            (
                "`REGISTRY`",
                "The ordered tuple of every token; both renderers group it by"
                " category.",
            ),
            ("`MODES`", "The density modes (see [Density](#density))."),
        ),
    )


def render_reference() -> str:
    """Render the full token reference page from the registry."""
    sections = (
        _HEAD,
        _registry_table(),
        "## Color",
        "Every color token is `Themed`: each row authors a `-light` and a `-dark`"
        " arm, and the public token is the `light-dark()` of the two.",
        _color_table(),
        _COLOR_NOTE,
        "## Type",
        _token_table(Category.FONT),
        _TYPE_NOTE,
        "## Space",
        _token_table(Category.SPACE),
        _SPACE_NOTE,
        "## Radius",
        _token_table(Category.RADIUS),
        _RADIUS_NOTE,
        "## Border width",
        _token_table(Category.BORDER_WIDTH),
        _BORDER_NOTE,
        "## Shadow",
        _token_table(Category.SHADOW),
        _SHADOW_NOTE,
        "## The component geometry contract",
        _FIT_INTRO,
        _token_table(Category.FIT, value="Value", role="Derived from"),
        _FIT_NOTE,
        "## Density",
        _DENSITY_INTRO,
        _density_table(),
        _DENSITY_NOTE,
        _TAIL,
    )
    return "\n\n".join(sections) + "\n"
