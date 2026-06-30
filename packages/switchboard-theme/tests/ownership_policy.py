"""The theme's paint-side ownership policy: what the theme may attach, and where.

The structural engine (:mod:`switchboard_ui.ownership`) reads CSS; this module is
the paint-side policy that engine is run against. It is the single place to ask what
the theme is *allowed* to do — which properties a state rule may not reshape, which
tiled hooks a seam may not double, which techniques the theme never uses — instead of
each rule living in whichever guard happened to need it. The four theme guards
(``test_theme_css``, ``test_state``, ``test_seams``, ``test_forbidden``) are queries
against this policy plus the shared reader. The one paint permission that is *not*
here is the inset rule: padding may land on any control or content surface (an open
set), so its guard reads the mechanism's closed ``STRUCTURAL_HOOKS`` denylist of
no-inset hooks rather than a list of paddable controls.

The split between this module and ``switchboard_ui.ownership`` follows the layer
boundary it enforces: the structural policy (the layout-property allowlist, the
no-inset structural hooks) governs switchboard's own structural vocabulary and lives
with the mechanism; this paint policy governs the theme and lives with the theme. The
reader they both run on is shared.
"""

# Inset (padding) permission is not a list here: a box's inset belongs to a control
# or content surface, an open set that grows with the components, so the padding
# guard reads the mechanism's closed denylist of structural hooks
# (`switchboard_ui.ownership.STRUCTURAL_HOOKS`) instead — padding may land anywhere
# except a layout / mount / region hook. See `test_theme_css.py`.

# --- state-stable geometry ---------------------------------------------------

# Selector fragments that mark a rule as state-dependent. ``:focus`` also catches
# ``:focus-visible`` / ``:focus-within`` by substring.
STATE_MARKERS: tuple[str, ...] = (
    ":hover",
    ":focus",
    ":active",
    ":disabled",
    ":enabled",
    ":checked",
    ":target",
    ":visited",
    ":indeterminate",
    "[aria-",
    "[data-state",
    "[disabled",
    "[checked",
    "[open",
)

# Properties that change a box's outer size or position. A state rule may declare
# none of these; paint (color, background, outline, box-shadow) is unrestricted.
GEOMETRY_EXACT: frozenset[str] = frozenset(
    {
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
        "position",
        "top",
        "right",
        "bottom",
        "left",
        "gap",
        "row-gap",
        "column-gap",
        "font-size",
        "line-height",
    }
)
GEOMETRY_PREFIX: tuple[str, ...] = ("padding", "margin", "inset", "flex")


def is_geometry(prop: str) -> bool:
    """Whether ``prop`` changes a box's outer size or position."""
    if prop in GEOMETRY_EXACT:
        return True
    if any(prop == p or prop.startswith(p + "-") for p in GEOMETRY_PREFIX):
        return True
    return prop == "border" or (prop.startswith("border") and prop.endswith("width"))


def is_state_selector(selectors: str) -> bool:
    """Whether a selector list targets an interactive state."""
    return any(marker in selectors for marker in STATE_MARKERS)


# --- single-owned seams ------------------------------------------------------

# Tiled cells and row containers share edges. `.sb-root` (the outer frame) and
# `.sb-island` (a mount point, not a tiled region) are deliberately absent.
REGION_HOOKS: frozenset[str] = frozenset(
    f"sb-{row}-{column}"
    for row in ("head", "body", "foot")
    for column in ("l", "c", "r")
)
TILED_HOOKS: frozenset[str] = REGION_HOOKS | {
    "sb-frame",
    "sb-rail",
    "sb-head-row",
    "sb-body-row",
    "sb-foot-row",
}


# --- forbidden techniques ----------------------------------------------------


def is_forbidden(prop: str) -> bool:
    """Whether ``prop`` is a technique the theme never uses (it never positions or transforms)."""
    return prop == "position" or prop == "transform" or prop.startswith("transform-")
