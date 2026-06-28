"""Shared showcase chrome: the surface switch across the three dogfood pages.

The gallery, the docs, and the theme builder are one site of distinct sections.
This module holds the one piece of chrome they share — a top-level switch that
moves between them — so the gallery and the docs (and the builder) place the same
control rather than each inventing its own. It is host chrome, a showcase-local
static island, not a core component.

The switch is a tab bar: mono links separated by dots, the active surface marked
with ``aria-current`` and a purple underline. Every link reserves the underline as
a transparent block-end border, recoloured only when active, so marking the active
surface never shifts the row (peer edge reservation).
"""

from typing import Literal

from switchboard_ui import Island
from switchboard_ui.html import element, escape_text

Surface = Literal["gallery", "docs", "builder"]

# The three dogfood surfaces, in nav order: the key the active page passes, the
# label, and the route each links to.
_SURFACES: tuple[tuple[Surface, str, str], ...] = (
    ("gallery", "Gallery", "/"),
    ("docs", "Docs", "/docs"),
    ("builder", "Builder", "/builder"),
)


def surface_switch(active: Surface) -> Island:
    """The top-level Gallery · Docs · Builder switch, the active surface marked.

    A static island (no adapter): the links navigate natively between the three
    surfaces. ``active`` names the current page so its link carries
    ``aria-current`` and the accent underline.
    """
    items: list[str] = []
    for index, (key, label, href) in enumerate(_SURFACES):
        if index:
            items.append(
                element(
                    "span", {"class": "sb-switch-sep", "aria-hidden": "true"}, ["·"]
                )
            )
        items.append(
            element(
                "a",
                {
                    "class": "sb-switch-link",
                    "href": href,
                    "aria-current": "page" if key == active else "false",
                },
                [escape_text(label)],
            )
        )
    nav = element("nav", {"class": "sb-switch", "aria-label": "Surfaces"}, items)
    return Island(name="surface-switch", initial=nav)


# The switch's own chrome (host CSS, reading the theme's --sb-* tokens). The active
# link's underline is reserved on every link as a transparent block-end border, so
# switching the active surface recolours rather than reflows.
_SWITCH_CSS = """
.sb-switch {
  display: flex;
  align-items: center;
  gap: var(--sb-space-sm);
  padding: var(--sb-space-md);
}
.sb-switch-link {
  color: var(--sb-color-muted);
  text-decoration: none;
  font-weight: var(--sb-font-weight-bold);
  border-block-end: var(--sb-border-width-accent) solid transparent;
}
.sb-switch-link:hover {
  color: var(--sb-color-fg);
}
.sb-switch-link[aria-current="page"] {
  color: var(--sb-color-accent);
  border-block-end-color: var(--sb-color-accent);
}
.sb-switch-link:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: 2px;
}
.sb-switch-sep {
  color: var(--sb-color-subtle);
}
"""


def surface_switch_styles() -> str:
    """The switch's structural CSS, for a host to inline in ``extra_head``."""
    return f"<style>{_SWITCH_CSS}</style>"
