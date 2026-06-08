"""The theme delivery helper: a ``<style>`` block for ``extra_head``.

A theme is a single CSS file shipped under this subpackage's ``static/``.
:func:`head` reads it and wraps it for inline injection, validating the name
where it is supplied (not deep inside rendering) so an unknown theme fails at the
call that names it.
"""

from switchboard_ui.assets import read_asset

# The themes that ship; a name is validated against this set at the call site.
THEMES = ("default",)

_PACKAGE = "switchboard_ui.themes"


def head(name: str = "default") -> str:
    """Return the inline ``<style>`` block for ``name``, for ``extra_head``.

    Raises :class:`ValueError` for an unknown theme, naming it, at the point the
    name is supplied rather than during rendering.
    """
    if name not in THEMES:
        raise ValueError(f"unknown theme {name!r}; available: {', '.join(THEMES)}")
    return f"<style>{read_asset(_PACKAGE, f'{name}.css')}</style>"
