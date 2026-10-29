"""The icon set's ES module is generated; this guards it against drift.

``static/icons.js`` must equal what :func:`switchboard_theme.icons.render_icon_module` renders from the SVG files and the curated metadata, so those stay the single source and the module can never be hand-edited out of sync with them. If the first test fails, regenerate the module with the command in its message and commit the result.
"""

import json
import re

from switchboard_theme.icons import ICON_NAMES, ICONS, icon_module, render_icon_module

_REGENERATE = (
    'uv run python -c "import pathlib, switchboard_theme; '
    "from switchboard_theme.icons import render_icon_module; "
    "pathlib.Path(switchboard_theme.__file__).parent.joinpath('static', 'icons.js')"
    ".write_text(render_icon_module(), encoding='utf-8')\""
)


def test_committed_module_matches_the_set() -> None:
    """The committed icons.js is exactly what the files and metadata render (no drift)."""
    assert icon_module() == render_icon_module(), (
        "static/icons.js has drifted from static/icons/*.svg and the metadata in "
        f"icons.py; regenerate it from the repository root with `{_REGENERATE}` and "
        "commit the result. The SVGs and the metadata are the source, not the module"
    )


def _exported(module: str, name: str) -> object:
    """The JSON literal bound to ``export const <name>`` in the module."""
    match = re.search(rf"export const {name} = (.*?);\n", module, flags=re.DOTALL)
    assert match, f"the module does not export {name}"
    return json.loads(match.group(1))


def test_module_exports_the_set_and_its_metadata() -> None:
    """The module's data exports carry every name, alphabetical, with each glyph's metadata."""
    module = render_icon_module()
    assert _exported(module, "iconNames") == list(ICON_NAMES)
    assert _exported(module, "iconMeta") == {
        entry.name: {"category": entry.category, "guidance": entry.guidance}
        for entry in ICONS
    }
    assert "export function icon(name)" in module


def test_module_glyphs_carry_the_same_hook_and_decorative_attributes() -> None:
    """The browser renderer stamps the class and attributes the Python renderer does."""
    module = render_icon_module()
    assert "svg.classList.add('sb-icon');" in module
    assert "svg.setAttribute('aria-hidden', 'true');" in module
    assert "svg.setAttribute('focusable', 'false');" in module
