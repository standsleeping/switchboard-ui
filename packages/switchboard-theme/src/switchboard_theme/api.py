"""The theme delivery helpers: inline head blocks plus the packaged typeface.

A theme is a single CSS file shipped under this distribution's ``static/``.
:func:`head` reads it and wraps it for inline injection, validating the name
where it is supplied (not deep inside rendering) so an unknown theme fails at the
call that names it. The asset readers live in the mechanism (``switchboard-ui``),
the one dependency this distribution takes; each reader is generic over package
name, so it serves the theme's own ``static/`` without the mechanism knowing.

The typeface (Recursive, a variable font; ``static/recursive.woff2``, OFL) is a
binary, so it cannot ride the inline ``<style>`` seam. Delivery splits in two:
the host serves :func:`font_bytes` at a URL of its choosing and injects
:func:`font_head` naming that URL. A page without either degrades to the family
tokens' system fallback stacks.
"""

from switchboard_ui.assets import read_asset, read_asset_bytes

# The themes that ship; a name is validated against this set at the call site.
THEMES = ("default",)

_PACKAGE = "switchboard_theme"

_FONT_ASSET = "recursive.woff2"


def head(name: str = "default") -> str:
    """Return the inline ``<style>`` block for ``name``, for ``extra_head``.

    Raises :class:`ValueError` for an unknown theme, naming it, at the point the
    name is supplied rather than during rendering.
    """
    if name not in THEMES:
        raise ValueError(f"unknown theme {name!r}; available: {', '.join(THEMES)}")
    return f"<style>{read_asset(_PACKAGE, f'{name}.css')}</style>"


def font_bytes() -> bytes:
    """Return the packaged typeface, for the host to serve at a URL it owns."""
    return read_asset_bytes(_PACKAGE, _FONT_ASSET)


def font_head(src: str) -> str:
    """Return the inline ``@font-face`` block for ``extra_head``.

    ``src`` is the URL where the host serves :func:`font_bytes`. The descriptor
    spans the face's full weight range; slant and the unregistered axes are
    driven by ``font-variation-settings`` in the token CSS, so the face is
    declared upright.
    """
    return (
        "<style>@font-face {\n"
        '  font-family: "Recursive";\n'
        f'  src: url("{src}") format("woff2");\n'
        "  font-weight: 300 1000;\n"
        "  font-style: normal;\n"
        "  font-display: swap;\n"
        "}</style>"
    )
