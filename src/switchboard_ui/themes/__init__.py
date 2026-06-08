"""Opt-in visual style, kept physically separate from the mechanism.

The mechanism ships structure-only ``layout.css`` plus unpainted hooks
(``sb-frame`` / ``sb-root`` / ``sb-island`` / ``sb-<region>`` and any ``class_``);
this subpackage *paints* those hooks with its own ``--sb-*`` token namespace. The
dependency is one-directional and enforced by a test: ``themes`` may import the
mechanism (to read its assets the same way), but no mechanism module may import
``themes``. The renderer never learns a theme exists.

Delivery reuses the ``extra_head`` injection seam that island behavior already
uses through ``extra_scripts``; the host wires a theme into a page itself:

    from switchboard_ui import render_document, themes

    render_document(doc, extra_head=themes.head("default"))
"""

from switchboard_ui.themes.api import THEMES, head

__all__ = ["THEMES", "head"]
