"""The mechanism never imports the theme: the seam is a build failure, not a convention.

``themes`` may import the mechanism (to read assets, to know hook names); no
mechanism module may import ``switchboard_ui.themes``. This walks every mechanism
module and asserts the boundary with the AST, so crossing it fails the build.
"""

import ast
from pathlib import Path

import switchboard_ui

_PKG_ROOT = Path(switchboard_ui.__file__).resolve().parent
_THEME_PKG = "switchboard_ui.themes"


def _mechanism_modules() -> list[Path]:
    """Every package module except those inside the themes subpackage."""
    themes_dir = _PKG_ROOT / "themes"
    return [p for p in _PKG_ROOT.rglob("*.py") if themes_dir not in p.parents]


def _imports_theme(tree: ast.AST) -> bool:
    """Whether an AST imports the theme subpackage by any spelling."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == _THEME_PKG or alias.name.startswith(_THEME_PKG + ".")
                for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == _THEME_PKG or module.startswith(_THEME_PKG + "."):
                return True
            # `from switchboard_ui import themes`
            if module == "switchboard_ui" and any(
                alias.name == "themes" for alias in node.names
            ):
                return True
    return False


def test_no_mechanism_module_imports_the_theme() -> None:
    """No module outside switchboard_ui.themes imports the theme subpackage."""
    offenders = [
        str(path.relative_to(_PKG_ROOT))
        for path in _mechanism_modules()
        if _imports_theme(ast.parse(path.read_text(encoding="utf-8")))
    ]
    assert not offenders, f"mechanism modules import the theme: {offenders}"
