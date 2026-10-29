"""Opt-in visual style for switchboard-ui, shipped as a separate distribution.

The mechanism (``switchboard-ui``) ships structure-only ``layout.css`` plus
unpainted hooks (``sb-frame`` / ``sb-root`` / ``sb-island`` / ``sb-<region>`` and
any ``class_``); this distribution *paints* those hooks with its own ``--sb-*``
token namespace. The dependency is one-directional and now a packaging fact:
``switchboard-theme`` depends on ``switchboard-ui`` (to read its assets the same
way), and ``switchboard-ui`` declares no dependency on the theme, so the
mechanism cannot import it. The renderer never learns a theme exists.

Delivery reuses the ``extra_head`` injection seam that island behavior already
uses through ``extra_scripts``; the host wires a theme into a page itself:

    from switchboard_ui import render_document
    import switchboard_theme

    render_document(doc, extra_head=switchboard_theme.head("default"))

The typeface travels the same seam: the host serves ``font_bytes()`` at a URL it
owns and prepends ``font_head(url)`` to ``extra_head``; without it the family
tokens fall back to the system stacks.

The theme's two shipped mode axes (color scheme and density) come with a
standard control surface (:mod:`switchboard_theme.modes`): the ``Modes`` popover,
the invisible applier island, and the pre-paint stamp, each riding the same host
seams as any component.

Paint for the layout's own regions travels a third module
(:mod:`switchboard_theme.chrome`), because the shipped sheet may not dress a
structural hook: :func:`content_column_styles` is the document-shaped center
column, opted in through ``extra_head`` like any other chrome.

The icon set travels a fourth module (:mod:`switchboard_theme.icons`): a closed vocabulary of glyphs shipped as SVG files under ``static/icons/``, rendered inline by :func:`icon`, sized by :func:`icon_styles` through ``extra_head``, and offered to client code as the ES module :func:`icon_module` returns, which the host serves at a URL it owns.
"""

from switchboard_theme.api import THEMES, font_bytes, font_head, head
from switchboard_theme.chrome import content_column_styles
from switchboard_theme.icons import (
    CATEGORY_GUIDANCE,
    ICON_CATEGORIES,
    ICON_NAMES,
    ICONS,
    IconCategory,
    IconEntry,
    IconName,
    icon,
    icon_module,
    icon_styles,
)
from switchboard_theme.modes import (
    DENSITY_TOPIC,
    SCHEME_TOPIC,
    mode_stamp_head,
    mode_state,
    mode_switch,
    mode_switch_scripts,
    mode_switch_styles,
)
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

# The typed registry is the theme-builder's surface: it iterates REGISTRY to
# generate one control per editable token, grouped by Category, choosing the
# control by ValueType and the binding by value kind (Themed arms vs Fixed).
__all__ = [
    "CATEGORY_GUIDANCE",
    "DENSITY_TOPIC",
    "ICONS",
    "ICON_CATEGORIES",
    "ICON_NAMES",
    "MODES",
    "REGISTRY",
    "SCHEME_TOPIC",
    "THEMES",
    "Category",
    "Derived",
    "Fixed",
    "IconCategory",
    "IconEntry",
    "IconName",
    "Themed",
    "Token",
    "ValueType",
    "content_column_styles",
    "font_bytes",
    "font_head",
    "head",
    "icon",
    "icon_module",
    "icon_styles",
    "mode_stamp_head",
    "mode_state",
    "mode_switch",
    "mode_switch_scripts",
    "mode_switch_styles",
]
