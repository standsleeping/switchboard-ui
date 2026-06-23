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
"""

from switchboard_theme.api import THEMES, head

__all__ = ["THEMES", "head"]
