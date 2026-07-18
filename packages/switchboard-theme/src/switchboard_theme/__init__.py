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
"""

from switchboard_theme.api import THEMES, font_bytes, font_head, head
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
    "MODES",
    "REGISTRY",
    "THEMES",
    "Category",
    "Derived",
    "Fixed",
    "Themed",
    "Token",
    "ValueType",
    "font_bytes",
    "font_head",
    "head",
]
