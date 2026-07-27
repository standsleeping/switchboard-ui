"""Sufficiency: a conforming control fits every slot the structure grants.

This is the philosophy's sufficiency criterion ("when every structural slot
satisfies the contract, every conforming themed component fits") made executable.
The other guards are *necessary* conditions (no margin, no stray padding, no
cross-layer leak, a one-way contract); this one is the *sufficiency* condition,
the capstone, and the guard that would have caught the original button-in-rail
spillover.

It proves sufficiency two ways, both stdlib (no browser): topology completeness
(a control placed in every region renders into that region's cell, so the stress
scenario is real) and contract arithmetic (resolving the theme's ``--sb-fit-*``
expressions to pixels, every rail floors to at least the control's outer block
and every side rail is at least the control's outer inline). The empirical
counterpart (rendering a button into all nine regions and measuring zero overflow
in both schemes) is run by hand against the showcase; the numbers here match it.
"""

import ast
import re

import switchboard_theme as themes
from switchboard_ui import render_document
from switchboard_ui.assets import read_asset
from switchboard_ui.model import REGIONS, Island, Region
from switchboard_ui.presets import _LEFT_WIDTH, _RIGHT_WIDTH, workbench

from .htmlprobe import elements

_REM_PX = 16.0  # 1rem at the browser default root font-size

_VAR = re.compile(r"var\(\s*(--[\w-]+)\s*\)")
_REM = re.compile(r"(?<![\w.])(\d*\.?\d+)rem\b")
_PX = re.compile(r"(?<![\w.])(\d*\.?\d+)px\b")
_DEF = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")


def _definitions(css: str) -> dict[str, str]:
    """Every ``--token: value`` pair declared in the sheet, value unresolved."""
    return {name: value.strip() for name, value in _DEF.findall(css)}


def _eval(expr: str) -> float:
    """Evaluate a pure arithmetic expression (``+ - * /`` over numbers) safely."""
    node = ast.parse(expr, mode="eval").body
    return _node(node)


def _node(node: ast.expr) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_node(node.operand)
    if isinstance(node, ast.BinOp):
        left, right = _node(node.left), _node(node.right)
        match node.op:
            case ast.Add():
                return left + right
            case ast.Sub():
                return left - right
            case ast.Mult():
                return left * right
            case ast.Div():
                return left / right
    raise ValueError(f"unsupported expression node: {ast.dump(node)}")


def _to_px(
    value: str, defs: dict[str, str], seen: frozenset[str] = frozenset()
) -> float:
    """Resolve a length/number CSS value to pixels (rem at ``_REM_PX``, calc inlined)."""
    value = _VAR.sub(lambda m: f"({_resolve(m.group(1), defs, seen)})", value)
    value = value.replace("calc(", "(")
    value = _REM.sub(lambda m: f"({m.group(1)}*{_REM_PX})", value)
    value = _PX.sub(lambda m: m.group(1), value)
    return _eval(value)


def _resolve(token: str, defs: dict[str, str], seen: frozenset[str]) -> float:
    """Resolve a token reference to pixels, guarding against cycles."""
    if token in seen:
        raise ValueError(f"cyclic contract token: {token}")
    return _to_px(defs[token], defs, seen | {token})


def test_a_control_in_every_region_renders_into_its_cell() -> None:
    """A control placed in each of the nine regions lands in that region's cell."""
    regions: dict[Region, tuple[Island, ...]] = {
        r: (Island(name=f"ctl-{r}", initial="<button>Btn</button>"),) for r in REGIONS
    }
    html = render_document(workbench(regions), extra_head=themes.head("default"))
    cell_classes = {
        attrs.get("class", "")
        for tag, attrs in elements(html)
        if tag == "div" and "sb-frame-column" in attrs.get("class", "")
    }
    for region in REGIONS:
        assert any(f"sb-{region}" in cls for cls in cell_classes), (
            f"region {region} has no rendered cell"
        )
    assert html.count("<button>Btn</button>") == len(REGIONS)


def test_a_control_fits_every_rail_and_side_slot() -> None:
    """Resolving the contract, every rail floor >= the control block and every side >= the control inline.

    This is the projection check: structure grants at least what the theme's
    control obligation requires, so a conforming control never overflows its slot.
    """
    defs = _definitions(read_asset("switchboard_theme", "default.css"))
    control_block = _resolve("--sb-fit-control-block", defs, frozenset())
    rail_block = _resolve("--sb-fit-rail-block", defs, frozenset())
    control_inline = _resolve("--sb-fit-control-inline", defs, frozenset())

    assert rail_block >= control_block, (
        f"a rail floors to {rail_block}px but the control needs {control_block}px"
    )
    for width in (_LEFT_WIDTH, _RIGHT_WIDTH):
        granted = _to_px(width, defs)
        assert granted >= control_inline, (
            f"a side rail grants {granted}px but the control needs {control_inline}px"
        )
