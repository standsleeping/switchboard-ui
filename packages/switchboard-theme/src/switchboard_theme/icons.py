"""The icon set: a closed vocabulary of glyphs, rendered inline on the server and in the browser.

The glyphs are Radix Icons (MIT, Copyright (c) 2022 WorkOS; the license text ships beside them as ``static/icons/radix-icons-MIT.txt``). Each is one file under ``static/icons/``, drawn on a 15 by 15 ``viewBox`` in ``currentColor`` and carrying no intrinsic width or height, so the CSS sizes it and the surrounding text colors it.

Those files plus the curated metadata in this module (each glyph's category and when to use it) are the one source. Two outputs are rendered from it:

- :func:`icon` renders a glyph as an inline ``<svg>`` string for server-rendered markup (an island's ``initial``, a table :class:`~switchboard_ui.components.Cell`, a button label).
- :func:`render_icon_module` renders the same set as an ES module for client code. The output is checked in as ``static/icons.js`` and served by the host from :func:`icon_module`; a test fails when it drifts from the files and the metadata.

A glyph is decorative: it is hidden from assistive tech and never takes focus. A control whose only content is a glyph names itself with its own ``aria-label``.

:func:`icon_styles` carries the glyph's CSS, opted in through ``extra_head`` like the theme's other chrome.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, get_args

from switchboard_ui.assets import read_asset
from switchboard_ui.html import attributes

IconName = Literal[
    "arrow-down",
    "arrow-left",
    "arrow-right",
    "arrow-up",
    "bell",
    "check",
    "chevron-down",
    "chevron-left",
    "chevron-right",
    "chevron-up",
    "code",
    "copy",
    "cross-1",
    "dots-horizontal",
    "dots-vertical",
    "exclamation-triangle",
    "external-link",
    "file-text",
    "gear",
    "hamburger-menu",
    "info-circled",
    "link-1",
    "magnifying-glass",
    "minus",
    "pencil-1",
    "plus",
    "question-mark-circled",
    "trash",
]
"""One glyph in the set. The type is closed, so a misspelled name fails type checking at the call."""

ICON_NAMES: tuple[IconName, ...] = get_args(IconName)
"""Every glyph name, alphabetical (the order of the files on disk)."""

IconCategory = Literal["direction", "action", "navigation", "status", "content"]
"""The role a glyph plays. The set is grouped by it, in this order."""

ICON_CATEGORIES: tuple[IconCategory, ...] = get_args(IconCategory)
"""Every category, in grouping order."""

CATEGORY_GUIDANCE: Mapping[IconCategory, str] = {
    "direction": "Disclosure and movement: where activating the control leads, or what it reveals.",
    "action": "Controls that change state. The control carries its own accessible name; the glyph never carries the meaning alone.",
    "navigation": "Persistent chrome in the rails and toolbars, not controls repeated on every row.",
    "status": "Status and meta information. Use sparingly: one glyph per meaning, never as ornament.",
    "content": "The kind of resource a row or a link points at.",
}
"""When to reach for each category, keyed in grouping order."""


@dataclass(frozen=True)
class IconEntry:
    """One glyph's curated metadata: its name, its category, and when to use it."""

    name: IconName
    category: IconCategory
    guidance: str


ICONS: tuple[IconEntry, ...] = (
    # direction
    IconEntry(
        "chevron-down",
        "direction",
        "The expand affordance of a collapsed section; opening it reveals the content below.",
    ),
    IconEntry(
        "chevron-up",
        "direction",
        "The collapse affordance of an open section; closing it hides the content.",
    ),
    IconEntry(
        "chevron-right",
        "direction",
        "Forward disclosure on a row into nested detail; also a breadcrumb separator.",
    ),
    IconEntry(
        "chevron-left",
        "direction",
        "Back disclosure, or the previous step of a paged flow.",
    ),
    IconEntry(
        "arrow-right",
        "direction",
        "Go on to the next step or destination; a stronger pull than the chevron.",
    ),
    IconEntry("arrow-left", "direction", "Return to the previous screen or context."),
    IconEntry("arrow-up", "direction", "Sort ascending, or jump back to the top."),
    IconEntry("arrow-down", "direction", "Sort descending, or download to the device."),
    # action
    IconEntry(
        "check",
        "action",
        "Confirmation, or the selected option in a list or option group.",
    ),
    IconEntry(
        "cross-1",
        "action",
        "Close, dismiss, or remove; the default glyph for a modal's or a notice's close control.",
    ),
    IconEntry("plus", "action", "Add an item to a collection, or expand a group."),
    IconEntry(
        "minus",
        "action",
        "Remove an item or collapse a group. Not for a destructive delete.",
    ),
    IconEntry("pencil-1", "action", "Edit the content in place."),
    IconEntry("trash", "action", "Destructive delete; always behind a confirmation."),
    IconEntry(
        "copy",
        "action",
        "Copy to the clipboard, with a brief confirmation after the click.",
    ),
    IconEntry(
        "external-link",
        "action",
        "The link opens in a new tab or leaves the site. Placed after the link text, never instead of it.",
    ),
    # navigation
    IconEntry(
        "hamburger-menu",
        "navigation",
        "Opens the primary navigation where a narrow viewport collapses it.",
    ),
    IconEntry(
        "dots-horizontal", "navigation", "The overflow menu of a toolbar or a rail."
    ),
    IconEntry(
        "dots-vertical",
        "navigation",
        "The overflow menu of a single row in a list or a table.",
    ),
    IconEntry(
        "magnifying-glass",
        "navigation",
        "Marks a search field, or the way into a search page.",
    ),
    # status
    IconEntry(
        "info-circled", "status", "A neutral note carrying supplementary context."
    ),
    IconEntry(
        "exclamation-triangle",
        "status",
        "A warning that needs attention without being destructive.",
    ),
    IconEntry(
        "question-mark-circled",
        "status",
        "Opens help: a definition, a tooltip, or the documentation.",
    ),
    IconEntry("bell", "status", "The notifications indicator."),
    IconEntry("gear", "status", "The way into settings or configuration."),
    # content
    IconEntry("file-text", "content", "A text document or an article."),
    IconEntry(
        "code",
        "content",
        "Source code: a code block, an inline code reference, or a developer surface.",
    ),
    IconEntry("link-1", "content", "An inline hyperlink, beside its link text."),
)
"""Every glyph's metadata, grouped by category in :data:`ICON_CATEGORIES` order and curated within each group (a chevron before the arrow it outranks)."""

_PACKAGE = "switchboard_theme"
_MODULE_ASSET = "icons.js"

# The class every rendered glyph carries, in both renderers: the hook the CSS sizes.
_ICON_CLASS = "sb-icon"

# The decorative attributes the Python renderer stamps on the root <svg>. The JS module stamps the same three at runtime.
_DECORATIVE = attributes(
    {"class": _ICON_CLASS, "aria-hidden": "true", "focusable": "false"}
)


def _markup(name: IconName) -> str:
    """The glyph's shipped SVG exactly as stored: no class and no ARIA attributes."""
    return read_asset(_PACKAGE, f"icons/{name}.svg").strip()


def icon(name: IconName) -> str:
    """An inline ``<svg>`` for the glyph ``name``, ready to embed in server-rendered markup.

    The root carries ``class="sb-icon"`` (the hook :func:`icon_styles` sizes), ``aria-hidden="true"``, and ``focusable="false"``, so the glyph is decorative: a control whose only content is a glyph names itself with its own ``aria-label``. The glyph paints in ``currentColor`` and sizes to ``1em``, so it follows the text around it.

    Raises :class:`ValueError` naming an unknown ``name`` (reachable only from untyped code, since :data:`IconName` is closed).
    """
    if name not in ICON_NAMES:
        raise ValueError(f"unknown icon {name!r}; the set is ICON_NAMES")
    return _markup(name).replace("<svg", f"<svg{_DECORATIVE}", 1)


# The glyph's own box: a 1em square that follows the font size around it, never squeezed by a flex row it sits in, and painted in the text color.
_ICON_CSS = """
.sb-icon {
  inline-size: 1em;
  block-size: 1em;
  flex-shrink: 0;
  fill: currentColor;
}
"""


def icon_styles() -> str:
    """The glyph's CSS, for a host to inline in ``extra_head``."""
    return f"<style>{_ICON_CSS}</style>"


def icon_module() -> str:
    """The shipped ES module (``static/icons.js``), for a host to serve at a URL it owns."""
    return read_asset(_PACKAGE, _MODULE_ASSET)


# The module's runtime half: fixed text apart from the class name, which is substituted from _ICON_CLASS so both renderers stamp the same hook.
_MODULE_RUNTIME = """\
const parser = typeof DOMParser !== 'undefined' ? new DOMParser() : null;

/**
 * Build an SVGElement for a glyph in the set, or return null for an unknown name so the caller can fall back to text.
 *
 * The element is decorative: it is hidden from assistive tech (aria-hidden="true") and never takes focus. A control whose glyph carries meaning names itself with its own aria-label.
 */
export function icon(name) {
  const markup = Object.hasOwn(MARKUP, name) ? MARKUP[name] : null;
  if (!markup || !parser) return null;
  const doc = parser.parseFromString(markup, 'image/svg+xml');
  const svg = doc.documentElement;
  if (!svg || svg.nodeName !== 'svg') return null;
  svg.classList.add('%(icon_class)s');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  return svg;
}
"""


def render_icon_module() -> str:
    """Render the icon set as an ES module: the generator behind ``static/icons.js``.

    The module exports ``iconNames`` (alphabetical), ``iconMeta`` (each name's category and guidance), ``iconCategories`` (each category's name and guidance, in grouping order), and ``icon(name)``, which returns a decorative ``SVGElement`` classed ``sb-icon`` or ``null`` for an unknown name.
    """
    markup = {name: _markup(name) for name in ICON_NAMES}
    meta = {
        entry.name: {"category": entry.category, "guidance": entry.guidance}
        for entry in ICONS
    }
    categories = [
        {"name": name, "guidance": CATEGORY_GUIDANCE[name]} for name in ICON_CATEGORIES
    ]
    return (
        "// Generated by switchboard_theme.icons (render_icon_module) from static/icons/*.svg and the metadata in icons.py. Edit those and run `just generate`; never edit this file.\n"
        "//\n"
        "// Radix Icons: MIT License, Copyright (c) 2022 WorkOS. The full text ships as static/icons/radix-icons-MIT.txt.\n"
        "\n"
        f"const MARKUP = {json.dumps(markup, indent=2, sort_keys=True)};\n"
        "\n"
        f"export const iconNames = {json.dumps(list(ICON_NAMES), indent=2)};\n"
        "\n"
        f"export const iconMeta = {json.dumps(meta, indent=2, sort_keys=True)};\n"
        "\n"
        f"export const iconCategories = {json.dumps(categories, indent=2)};\n"
        "\n"
        f"{_MODULE_RUNTIME % {'icon_class': _ICON_CLASS}}"
    )
