"""The theme delivery helper: a ``<style>`` block for ``extra_head``.

A theme is a single CSS file shipped under this distribution's ``static/``.
:func:`head` reads it and wraps it for inline injection, validating the name
where it is supplied (not deep inside rendering) so an unknown theme fails at the
call that names it. ``read_asset`` lives in the mechanism (``switchboard-ui``),
the one dependency this distribution takes; the reader is generic over package
name, so it serves the theme's own ``static/`` without the mechanism knowing.
"""

from switchboard_ui.assets import read_asset

# The themes that ship; a name is validated against this set at the call site.
THEMES = ("default",)

_PACKAGE = "switchboard_theme"


def head(name: str = "default") -> str:
    """Return the inline ``<style>`` block for ``name``, for ``extra_head``.

    Raises :class:`ValueError` for an unknown theme, naming it, at the point the
    name is supplied rather than during rendering.
    """
    if name not in THEMES:
        raise ValueError(f"unknown theme {name!r}; available: {', '.join(THEMES)}")
    return f"<style>{read_asset(_PACKAGE, f'{name}.css')}</style>"
