"""The shared engine for the ownership guards: read CSS and inline styles, hold the structural policy.

Every spatial or visual decision in switchboard has one owning layer, and a family
of build-time guards holds the code to that contract: the structural sheets declare
only geometry, the theme paints only where it is allowed, a state repaints but never
reshapes, a seam is drawn once, a factory carries values not paint. Those guards all
need the same thing first — to read rules, declarations, and selector subjects out of
a stylesheet, or property declarations out of an inline ``style`` attribute. This
module is the single implementation they share, so the parser lives in one place
instead of being copied into each guard.

It also holds the *structural* ownership policy: the geometry-only property allowlist
the structural sheets must stay within, the one contract-token family structure may
consume, and the custom-property prefix an inline ``style`` may carry. The paint-side
policy (which selectors may inset, which properties a state may not touch, which
seams a tile may not double) lives next to the theme, since that is the layer it
governs; this module is the structural side plus the parsing every guard runs on.

It is dependency-free (stdlib only) and deliberately small: a regex-level reader of
the project's own generated and hand-written sheets, whose shape it controls, not a
general CSS parser. It is internal: not part of the public API, no host imports it.
"""

import re
from collections.abc import Iterable

# --- the parsing engine ------------------------------------------------------

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_COMBINATOR = re.compile(r"\s*[>+~]\s*|\s+")
# An inline `style` attribute as the renderer emits it: space-prefixed, its value
# double-quoted with any inner quote already escaped (so the value holds no `"`).
_INLINE_STYLE = re.compile(r'\sstyle="([^"]*)"')


def _without_comments(css: str) -> str:
    """The stylesheet with ``/* ... */`` comments removed."""
    return _COMMENT.sub("", css)


def rules(css: str) -> list[tuple[str, str]]:
    """``(selector-list, body)`` for each flat rule block, comments stripped."""
    return _RULE.findall(_without_comments(css))


def declarations(body: str) -> list[tuple[str, str]]:
    """``(property, value)`` pairs in a declaration body.

    Works on a rule body and on an inline ``style`` value alike — both are
    ``;``-separated declaration lists. Property names are lower-cased; values are
    stripped but kept verbatim (a guard that compares a value lower-cases its own).
    """
    out: list[tuple[str, str]] = []
    for declaration in body.split(";"):
        name, separator, value = declaration.partition(":")
        if separator:
            out.append((name.strip().lower(), value.strip()))
    return out


def properties(body: str) -> list[str]:
    """The property names declared in one declaration body."""
    return [name for name, _ in declarations(body)]


def declared_properties(css: str) -> set[str]:
    """Every property declared anywhere in a stylesheet (selectors excluded)."""
    found: set[str] = set()
    for _, body in rules(css):
        found.update(properties(body))
    return found


def selectors(css: str) -> list[str]:
    """Every selector in the sheet, comma-separated lists split out."""
    out: list[str] = []
    for selector_list, _ in rules(css):
        for selector in selector_list.split(","):
            selector = selector.strip()
            if selector:
                out.append(selector)
    return out


def rule_body(css: str, selector: str) -> str:
    """The declaration body of the rule whose selector is exactly ``selector``."""
    match = re.search(re.escape(selector) + r"\s*\{([^{}]*)\}", _without_comments(css))
    return match.group(1) if match else ""


def _last_compound(selector: str) -> str:
    """The rightmost compound selector (after the last combinator or descendant space)."""
    return _COMBINATOR.split(selector.strip())[-1]


def subject(selector: str) -> str:
    """The rightmost compound selector, stripped of pseudos and attributes.

    ``.a .b:hover[x]`` → ``.b``. Names the kind of thing a rule's last compound
    targets, so a guard can ask what the declaration lands on.
    """
    return re.split(r"::|:|\[", _last_compound(selector))[0]


def subject_classes(selector: str) -> set[str]:
    """The class names in the rightmost compound selector."""
    return set(re.findall(r"\.([_a-zA-Z][\w-]*)", _last_compound(selector)))


def declares(props: Iterable[str], prop: str) -> bool:
    """Whether ``prop`` or any ``prop-*`` longhand is among ``props``."""
    return any(p == prop or p.startswith(prop + "-") for p in props)


def referenced_tokens(css: str) -> list[str]:
    """Every ``var(--token)`` custom property referenced in the sheet."""
    return re.findall(r"var\(\s*(--[\w-]+)", _without_comments(css))


def magic_lengths(css: str) -> set[str]:
    """The bare non-zero absolute lengths in the sheet (a token's contents are owned).

    ``var(...)`` contents are stripped first (they are owned numbers, not magic), so
    only a length written directly into a declaration — the un-owned-dimension
    mistake — is returned.
    """
    stripped = re.sub(r"var\([^)]*\)", "", _without_comments(css))
    bodies = " ".join(body for _, body in _RULE.findall(stripped))
    lengths = re.findall(r"(\d*\.?\d+)(px|rem|em|cm|mm|pt|pc|in)\b", bodies)
    return {f"{number}{unit}" for number, unit in lengths if float(number) != 0}


def inline_styles(html: str) -> list[str]:
    """Every inline ``style`` attribute value in a rendered HTML fragment."""
    return _INLINE_STYLE.findall(html)


# --- structural ownership policy ---------------------------------------------

# The only properties the structural layer may declare: those that determine size,
# position, and flow. Box-spacing is absent — rhythm between siblings is the
# parent's `gap` and a box's inset is a density decision the theme owns — and so
# is appearance (color, background, border, font, shadow): a structural sheet
# that names one fails the guard. The narrow exception is the reset layer below,
# which is guarded by value rather than by name.
LAYOUT_PROPERTIES: frozenset[str] = frozenset(
    {
        "display",
        # flexbox (sibling distribution lives here, via `gap`)
        "flex",
        "flex-direction",
        "flex-grow",
        "flex-shrink",
        "flex-basis",
        "flex-wrap",
        "flex-flow",
        "gap",
        "row-gap",
        "column-gap",
        # grid
        "grid",
        "grid-template",
        "grid-template-rows",
        "grid-template-columns",
        "grid-template-areas",
        "grid-auto-rows",
        "grid-auto-columns",
        "grid-auto-flow",
        "grid-row",
        "grid-column",
        "grid-area",
        # alignment & distribution
        "align-items",
        "align-self",
        "align-content",
        "justify-items",
        "justify-self",
        "justify-content",
        "place-items",
        "place-self",
        "place-content",
        "order",
        # sizing (physical and logical)
        "width",
        "height",
        "min-width",
        "max-width",
        "min-height",
        "max-height",
        "inline-size",
        "block-size",
        "min-inline-size",
        "max-inline-size",
        "min-block-size",
        "max-block-size",
        "box-sizing",
        "aspect-ratio",
        # overflow / scroll
        "overflow",
        "overflow-x",
        "overflow-y",
        "overflow-inline",
        "overflow-block",
        # Reserving the classic scrollbar's width is geometry, not bar styling:
        # the platform still paints, sizes, and themes the bar. Hiding, tinting,
        # and resizing it remain absent from this list and always will be.
        "scrollbar-gutter",
        # positioning
        "position",
        "top",
        "right",
        "bottom",
        "left",
        "inset",
        "inset-block",
        "inset-block-start",
        "inset-block-end",
        "inset-inline",
        "inset-inline-start",
        "inset-inline-end",
        "z-index",
        # anchor positioning (declarative placement of a top-layer panel
        # relative to its trigger; the popover's placement contract)
        "anchor-name",
        "position-anchor",
        "position-try-fallbacks",
    }
)

UA_RESETS: dict[str, frozenset[str]] = {
    "margin": frozenset({"0", "0px"}),
    "padding": frozenset({"0", "0px"}),
    "list-style": frozenset({"none"}),
}
"""The reset layer: user-agent defaults a structural sheet may neutralize, and
the only values that count as neutralizing them.

The delegation rules the structural layer obeys — rhythm is the parent's `gap`,
insets are the theme's, appearance is never structure's — all presuppose a
baseline with no user-agent presentation in it. Removing that presentation is not
a *use* of the mechanism those rules delegate; a generated ``<body>`` with
``margin: 0`` is not doing spacing, and a generated ``<ul>`` with ``padding: 0``
and ``list-style: none`` is not insetting or painting. It is clearing the ground
those rules describe.

Which is why the entry is a property *and* its permitted values. Guarding the
name alone would either ban the reset (forcing an exception per element) or admit
the whole mechanism (``padding: var(--sb-space-md)`` would sail through). Guarding
the value states the rule exactly, and it generalizes: a future generated element
with its own user-agent default gets a row here rather than a special case.

The package may only reset elements it generated and named. It never reaches for
a bare ``ul`` or ``body`` selector in the host's document.
"""


def is_ua_reset(prop: str, value: str) -> bool:
    """Whether ``prop: value`` neutralizes a user-agent default rather than using it."""
    permitted = UA_RESETS.get(prop)
    return permitted is not None and value.strip().lower() in permitted


def non_structural_declarations(css: str) -> list[tuple[str, str, str]]:
    """Every ``(selector, property, value)`` a structural sheet may not declare.

    A declaration is admissible if its property is a geometry property, or if it
    is a permitted reset of a user-agent default. Everything else is a breach:
    paint in a structural sheet, or box-spacing used as spacing.
    """
    return [
        (selector.strip(), name, value)
        for selector, body in rules(css)
        for name, value in declarations(body)
        if name not in LAYOUT_PROPERTIES
        if not is_ua_reset(name, value)
    ]


CONTRACT_TOKEN_PREFIX = "--sb-fit-"
"""The one token family structure may consume: the Component Geometry Contract
obligations the theme publishes. Structure consumes obligations (a rail floors
itself to ``--sb-fit-rail-block``), never paint causes."""

STRUCTURAL_LINK_TOKENS: frozenset[str] = frozenset({"--sb-anchor"})
"""Per-instance link values structure may consume beside the contract: identity
data a factory carries inline (the popover's anchor name) for the structural
sheet to read via ``var()``. A link relates two elements; it causes no paint and
holds no theme value, so consuming one is not a cause-reading breach."""

INLINE_VALUE_PREFIX = "--sb-"
"""The prefix an inline ``style`` declaration must carry. A factory may carry a
per-instance ``--sb-*`` custom-property *value* on an element (a swatch's color);
the property that paints from it is the theme's. Anything else in an inline
``style`` is paint or geometry leaking through a channel the ``.css`` guards never
see."""

STRUCTURAL_HOOKS: frozenset[str] = frozenset(
    {
        "sb-document",
        "sb-frame",
        "sb-frame-row",
        "sb-frame-column",
        "sb-overflow-visible",
        "sb-overflow-clip",
        "sb-overflow-auto",
        "sb-island",
        "sb-root",
        "sb-root-flow",
        "sb-root-viewport",
        "sb-rail",
        "sb-sticky-rail",
        "sb-flow-body",
        "sb-head-row",
        "sb-body-row",
        "sb-foot-row",
    }
    | {
        f"sb-{row}-{column}"
        for row in ("head", "body", "foot")
        for column in ("l", "c", "r")
    }
)
"""The mechanism's layout / mount / region hooks: the classes the theme may never
inset. A box's inset belongs to a control or content surface — an *open* set that
grows with every component — so the padding guard reads this *closed* denylist of
structural hooks (the mechanism's own vocabulary) rather than a hand-maintained
allowlist of every paddable control. Padding that lands on one of these is the
ownership breach; which control happens to inset is the author's taste, not the
guard's concern."""
