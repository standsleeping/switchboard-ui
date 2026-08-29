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


def test_layout_css_declares_only_geometry_and_permitted_resets() -> None:
    """Every declaration is geometry, or a permitted reset of a user-agent default.

    The guard reads values, not just property names. Guarding names alone would
    either ban the reset layer outright (forcing a documented exception per
    generated element) or admit a whole mechanism the layer delegates: with a
    bare `padding` allowance, `padding: var(--sb-space-md)` would sail through.
    Reading the value states the rule exactly — clear a user-agent default, never
    use box-spacing for spacing or name a paint property.
    """
    css = read_static("layout.css")
    assert ownership.declared_properties(css), "nothing parsed; the path is wrong"
    offenders = ownership.non_structural_declarations(css)
    assert not offenders, f"layout.css declares non-structural values: {offenders}"


def test_box_spacing_in_layout_css_is_only_ever_a_zero_reset() -> None:
    """Margin and padding may zero a user-agent default and nothing else.

    Rhythm between siblings is the parent's `gap`; a box's inset is the theme's.
    Neutralizing the user agent's own inset is neither of those, so it is
    permitted at exactly the value that neutralizes it.
    """
    offenders = [
        (selector.strip(), name, value)
        for selector, body in ownership.rules(read_static("layout.css"))
        for name, value in ownership.declarations(body)
        if name.split("-", 1)[0] in {"margin", "padding"}
        if not ownership.is_ua_reset(name, value)
    ]
    assert not offenders, (
        f"layout.css carries non-zero box-spacing {offenders}; structure may zero "
        "a user-agent default, never use it for spacing (rhythm is `gap`)"
    )


def test_layout_css_selects_only_sb_classes() -> None:
    """The layer styles only its own .sb-* elements, never the host's body/:root."""
    foreign = [
        s
        for s in ownership.selectors(read_static("layout.css"))
        if not s.startswith(".sb-")
    ]
    assert not foreign, f"layout.css selects non-sb elements: {foreign}"


def test_layout_css_admits_only_contract_tokens_and_its_own_facts() -> None:
    """Structure consumes obligations (--sb-fit-*) and facts it declares itself, nothing else.

    The three-way split: the layout layer stays free of paint tokens and of
    light/dark theming (those are *causes*, the theme's to own), but it may
    consume the projected *obligations* the theme publishes as ``--sb-fit-*``
    (a rail floors itself to ``--sb-fit-rail-block`` rather than guessing a
    fixed height), and the geometry *facts* it publishes itself as
    ``--sb-chrome-*`` — each of which must be declared in this sheet, so no
    fact is consumed dangling. ``test_contract.py`` enforces that each family
    flows one way.
    """
    css = read_static("layout.css")
    assert "light-dark(" not in css  # theming is a cause, never consumed by structure
    declared_facts = {
        name
        for _, body in ownership.rules(css)
        for name, _ in ownership.declarations(body)
        if name.startswith(ownership.FACT_TOKEN_PREFIX)
    }
    offenders = sorted(
        {
            t
            for t in ownership.referenced_tokens(css)
            if not t.startswith(ownership.CONTRACT_TOKEN_PREFIX)
            if t not in declared_facts
        }
    )
    assert not offenders, (
        f"layout.css references tokens {offenders} that are neither --sb-fit-* "
        "obligations nor --sb-chrome-* facts the sheet declares"
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


def test_a_rail_distributes_its_cells_to_its_ends() -> None:
    """A rail's centre is its only flexible cell, and an omitted centre collapses.

    Two fixed cells with nothing between them would sit flush at the row's
    start; distribution puts the trailing cell at the row's end, and is inert
    whenever the centre renders, because a flexible centre takes every free
    pixel first.
    """
    body = ownership.rule_body(read_static("layout.css"), ".sb-rail")
    assert dict(ownership.declarations(body)).get("justify-content") == "space-between"


def test_a_frame_holding_no_island_collapses() -> None:
    """An empty cell and a rail of empty cells both take no space.

    `:empty` carries the cell; `:not(:has(.sb-island))` carries the rail, which
    is never empty itself (its three cells are there, collapsed) but would
    otherwise keep its floor under its seam as a band of nothing. The two are
    separate rules, never one selector list: an invalid selector drops the
    whole list it appears in, so a shared list would cost an engine without
    `:has()` the cell collapse too.
    """
    css = read_static("layout.css")
    collapsing_lists = [
        {selector.strip() for selector in selectors.split(",")}
        for selectors, body in ownership.rules(css)
        if dict(ownership.declarations(body)).get("display") == "none"
    ]
    assert {".sb-frame:empty"} in collapsing_lists
    assert {".sb-frame:not(:has(.sb-island))"} in collapsing_lists


def test_the_layer_never_styles_the_scrollbar_itself() -> None:
    """Reservation is permitted; hiding, tinting, or resizing the bar is not."""
    css = read_static("layout.css")
    declared = ownership.declared_properties(css)
    assert "scrollbar-width" not in declared
    assert "scrollbar-color" not in declared
    assert "::-webkit-scrollbar" not in css


def test_the_layer_never_animates_scrolling() -> None:
    """`scroll-behavior` is never declared: every jump the layer causes is instant.

    Instant is also the accessible default: a reader who asks the platform to
    reduce motion needs nothing disabled here, because nothing animates.
    """
    assert "scroll-behavior" not in ownership.declared_properties(
        read_static("layout.css")
    )


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


def test_the_chrome_depth_counts_only_rails_that_render() -> None:
    """Each end's chrome depth is the rail's floor if it renders, else zero.

    The conditions state the facts; every consumer (the sticky rail here, the
    theme's anchor clearance) composes the same two values. The gate is the
    same test the collapse rule uses — an island within the rail — so a page
    with no head rail starts its side rails at the viewport's top rather than
    a floor below it.
    """
    css = read_static("layout.css")
    defaults = dict(ownership.declarations(ownership.rule_body(css, ".sb-root-flow")))
    assert defaults.get("--sb-chrome-block-start") == "0px"
    assert defaults.get("--sb-chrome-block-end") == "0px"
    with_head = dict(
        ownership.declarations(
            ownership.rule_body(css, ".sb-root-flow:has(> .sb-head-row .sb-island)")
        )
    )
    assert with_head == {"--sb-chrome-block-start": "var(--sb-fit-rail-block, 0px)"}
    with_foot = dict(
        ownership.declarations(
            ownership.rule_body(css, ".sb-root-flow:has(> .sb-foot-row .sb-island)")
        )
    )
    assert with_foot == {"--sb-chrome-block-end": "var(--sb-fit-rail-block, 0px)"}


def test_the_sticky_rail_never_stretches_and_fills_the_window() -> None:
    """A sticky rail aligns to the start and is sized to the window between the chrome.

    Without ``align-self: flex-start`` the flex row stretches the rail to the
    article's height, leaving nothing to stick. The size is the viewport less
    the chrome depth at each end, so a part pinned at the rail's end sits at
    the bottom of the screen in every scroll state and a taller rail scrolls
    within itself.
    """
    css = read_static("layout.css")
    rail = dict(ownership.declarations(ownership.rule_body(css, ".sb-sticky-rail")))
    assert rail.get("position") == "sticky"
    assert rail.get("inset-block-start") == "var(--sb-chrome-block-start)"
    assert rail.get("align-self") == "flex-start"
    assert rail.get("block-size") == (
        "calc(100svb - var(--sb-chrome-block-start) - var(--sb-chrome-block-end))"
    )


def test_the_flowing_documents_chrome_rails_stay() -> None:
    """The head rail sticks to the top and the foot rail to the bottom of the viewport.

    The page still scrolls (the shape's defining property); only the chrome
    holds still, which is what lets a side rail be measured against it. Both
    sit above the article, which the tree paints later.
    """
    css = read_static("layout.css")
    head = dict(
        ownership.declarations(ownership.rule_body(css, ".sb-root-flow > .sb-head-row"))
    )
    foot = dict(
        ownership.declarations(ownership.rule_body(css, ".sb-root-flow > .sb-foot-row"))
    )
    assert head.get("position") == "sticky" and head.get("inset-block-start") == "0"
    assert foot.get("position") == "sticky" and foot.get("inset-block-end") == "0"
    assert head.get("z-index") == "1" and foot.get("z-index") == "1"


def test_the_flow_body_row_grows_without_a_zero_basis() -> None:
    """The flowing body row takes slack but is sized by its own content.

    ``1 1 auto``, never ``1 1 0``: a zero basis contributes nothing to an
    auto-height column's intrinsic size, so the row would be sized from leftover
    viewport space and a long article crushed into it. The growth is also what
    keeps a short article's column seams running the full page height.
    """
    body = dict(
        ownership.declarations(
            ownership.rule_body(read_static("layout.css"), ".sb-flow-body")
        )
    )
    assert body.get("flex") == "1 1 auto"


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
