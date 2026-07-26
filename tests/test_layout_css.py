"""The packaged stylesheet is structural layout only, with no visual style.

The CSS controls geometry (size, position, flow) and nothing else. The static
guards below keep it honest, so the layout layer cannot: name an appearance
property, use box-spacing for spacing, smuggle a design token into a geometry
value, reach outside its own `.sb-*` elements, or let a policy depend on the
order rules happen to appear in.

  1. property names are geometry-only (the allowlist);
  2. `padding` is banned outright and `margin` may only ever be a zero reset;
  3. property values carry no tokens or theming (only the contract obligations);
  4. selectors target only `.sb-*`, never the host's `html` / `:root`;
  5. every overflow policy and root mode has exactly one rule declaring it;
  6. the scrollbar's gutter may be reserved, but the bar is never styled;
  7. no dimension uses a unit that changes during a scroll.

The CSS reader and the geometry-only allowlist live in :mod:`switchboard_ui.ownership`,
the single engine the structural and theme guards share; this module is the
structural sheet's queries against it.
"""

import re

from switchboard_ui import model, ownership
from switchboard_ui.assets import read_static


def test_layout_css_declares_only_layout_properties() -> None:
    """Every property in layout.css is a geometry property, never appearance."""
    declared = ownership.declared_properties(read_static("layout.css"))
    assert declared, "no properties parsed; the regex or file path is wrong"
    non_layout = declared - ownership.LAYOUT_PROPERTIES
    assert not non_layout, (
        f"layout.css declares non-layout properties: {sorted(non_layout)}"
    )


def test_layout_css_bans_padding_outright() -> None:
    """A box's inset is a density decision the theme owns, never structure's."""
    declared = ownership.declared_properties(read_static("layout.css"))
    padding = {p for p in declared if p.split("-", 1)[0] == "padding"}
    assert not padding, f"layout.css uses banned padding: {sorted(padding)}"


def test_layout_css_margin_is_only_ever_a_zero_reset() -> None:
    """Margin may zero a user-agent default; it may never carry a spacing value.

    The rule bans `margin` as a *spacing mechanism*, because rhythm between
    siblings belongs to the parent's `gap`. Removing the user agent's default
    body inset is not a use of that mechanism; it is the reset layer the rule
    presupposes. So the guard reads values rather than property names: any
    non-zero margin fails, which states the rule instead of approximating it and
    generalizes to a future zero reset without a second exception.
    """
    offenders = [
        (selector.strip(), value)
        for selector, body in ownership.rules(read_static("layout.css"))
        for name, value in ownership.declarations(body)
        if name.split("-", 1)[0] == "margin"
        if value.strip() not in {"0", "0px"}
    ]
    assert not offenders, (
        f"layout.css carries non-zero margin {offenders}; structure may zero a "
        "user-agent default, never use margin for spacing (rhythm is `gap`)"
    )


def test_layout_css_selects_only_sb_classes() -> None:
    """The layer styles only its own .sb-* elements, never the host's body/:root."""
    foreign = [
        s
        for s in ownership.selectors(read_static("layout.css"))
        if not s.startswith(".sb-")
    ]
    assert not foreign, f"layout.css selects non-sb elements: {foreign}"


def test_layout_css_admits_only_contract_tokens() -> None:
    """Structure may consume contract obligations (--sb-fit-*), no other token, never theming.

    The three-way split: the layout layer stays free of paint tokens and of
    light/dark theming (those are *causes*, the theme's to own), but it may
    consume the projected *obligations* the theme publishes as ``--sb-fit-*``
    (a rail floors itself to ``--sb-fit-rail-block`` rather than guessing a
    fixed height). ``test_contract.py`` enforces that the flow is one-way.
    """
    css = read_static("layout.css")
    assert "light-dark(" not in css  # theming is a cause, never consumed by structure
    non_contract = sorted(
        {
            t
            for t in ownership.referenced_tokens(css)
            if not t.startswith(ownership.CONTRACT_TOKEN_PREFIX)
        }
    )
    assert not non_contract, (
        f"layout.css references non-contract tokens {non_contract}; "
        "structure may consume only --sb-fit-* obligations"
    )


def test_every_overflow_policy_has_exactly_one_role_rule() -> None:
    """Each policy in the model maps to one class here, declaring that one value.

    The base ``.sb-frame`` declares no overflow at all: the policy arrives on
    every frame as its own class, emitted from the frame's own value. Nothing
    depends on rule order, so reordering this sheet cannot change which element
    scrolls — the defect the old equal-specificity tie between ``.sb-frame`` and
    ``.sb-scroll`` made possible.
    """
    css = read_static("layout.css")
    assert "overflow" not in ownership.rule_body(css, ".sb-frame"), (
        ".sb-frame must not declare overflow; the policy class carries it"
    )
    for policy in model.OVERFLOWS:
        body = ownership.rule_body(css, f".sb-overflow-{policy}")
        declared = dict(ownership.declarations(body))
        assert declared.get("overflow") == policy, (
            f".sb-overflow-{policy} must declare overflow: {policy}, got {body!r}"
        )


def test_auto_overflow_reserves_a_stable_scrollbar_gutter() -> None:
    """The one auto-overflow role reserves the classic bar's width.

    Reserving is geometry, not bar styling: the platform still paints, sizes, and
    themes the bar. A gutter exists only where a classic scrollbar exists, so
    this is inert under overlay scrollbars and turns an intermittent inline shift
    into a constant inset under classic ones.
    """
    body = ownership.rule_body(read_static("layout.css"), ".sb-overflow-auto")
    assert dict(ownership.declarations(body)).get("scrollbar-gutter") == "stable"


def test_the_layer_never_styles_the_scrollbar_itself() -> None:
    """Reservation is permitted; hiding, tinting, or resizing the bar is not."""
    css = read_static("layout.css")
    declared = ownership.declared_properties(css)
    assert "scrollbar-width" not in declared
    assert "scrollbar-color" not in declared
    assert "::-webkit-scrollbar" not in css


def test_each_root_mode_has_one_rule_and_only_viewport_positions() -> None:
    """Root sizing belongs to the root mode, and only the locked mode positions.

    A flow root is content-sized with a floor; a viewport root is the one rule in
    the sheet that positions anything. If flow ever gained a `position`, a page
    that declared itself a document would silently stop scrolling as one.
    """
    css = read_static("layout.css")
    flow = dict(ownership.declarations(ownership.rule_body(css, ".sb-root-flow")))
    viewport = dict(
        ownership.declarations(ownership.rule_body(css, ".sb-root-viewport"))
    )
    assert "position" not in flow, "a flow root must not position"
    assert flow.get("min-block-size") == "100svb", (
        "a flow root floors to the small viewport unit, which cannot change mid-scroll"
    )
    assert viewport.get("position") == "fixed"
    assert viewport.get("inset") == "0"
    positioning = [
        selector.strip()
        for selector, body in ownership.rules(css)
        if dict(ownership.declarations(body)).get("position") == "fixed"
    ]
    assert positioning == [".sb-root-viewport"], (
        f"only the viewport root may fix-position; also found {positioning}"
    )


def test_structure_never_uses_the_dynamic_viewport_unit() -> None:
    """`dvb`/`dvh` change as mobile chrome collapses: a mid-scroll geometry change.

    The dynamic viewport units are *defined* to resize during a scroll, which is
    the defect class this layer exists to eliminate. The small viewport unit is
    the always-visible area and is stable, so structural caps and floors use it.
    """
    dynamic = [
        (selector.strip(), name, value)
        for selector, body in ownership.rules(read_static("layout.css"))
        for name, value in ownership.declarations(body)
        if re.search(r"\d(dvb|dvh|dvw|dvi)\b", value)
    ]
    assert not dynamic, (
        f"layout.css uses a dynamic viewport unit in {dynamic}; use the small "
        "unit (svb), which cannot change while the user scrolls"
    )


def test_structure_has_no_magic_number_lengths() -> None:
    """layout.css carries no bare absolute length: every dimension is a token, keyword, 0, or %.

    Philosophy §16: a structural dimension must be an owned number. The only
    lengths that may appear are inside a ``var(--sb-fit-*)`` obligation (owned by
    the theme's projection) or the trivial ``0``; a bare ``40px`` is the rail-height
    mistake the contract layer fixed. The complementary theme guard ("the theme
    never positions or transforms") lives in the theme's ``test_forbidden.py``.
    """
    magic = sorted(ownership.magic_lengths(read_static("layout.css")))
    assert not magic, (
        f"layout.css has bare absolute lengths {magic}; a structural dimension must be a "
        "token, keyword, 0, or %, never an un-owned number (use a --sb-fit-* obligation)"
    )
