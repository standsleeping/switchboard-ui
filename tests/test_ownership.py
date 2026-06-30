"""The shared ownership engine: a regex-level reader of CSS and inline styles.

These unit tests pin the parser the ownership guards run on — rule extraction,
declaration and selector parsing, the rightmost-subject helpers, token and
magic-length scanning, and inline-style extraction — plus the structural policy
constants. The guards (structural and theme) assert *contracts* over real sheets;
this module asserts the *engine* underneath them behaves, so a parser change that
would silently weaken every guard fails here first.
"""

from switchboard_ui import ownership

_SHEET = """
/* a comment { with braces } to strip */
.a, .b {
  display: flex;
  gap: var(--sb-space-sm);
}
.c:hover {
  color: red;
}
"""


def test_rules_strips_comments_and_pairs_selectors_with_bodies() -> None:
    """Each flat rule becomes ``(selector-list, body)`` with comments removed."""
    parsed = ownership.rules(_SHEET)
    assert [s.strip() for s, _ in parsed] == [".a, .b", ".c:hover"]
    assert "display: flex" in parsed[0][1]
    assert "with braces" not in "".join(b for _, b in parsed)


def test_declarations_pairs_name_and_value_and_skips_non_declarations() -> None:
    """``name: value`` pairs are parsed; a segment with no colon is skipped."""
    assert ownership.declarations("color: red; --sb-swatch:#fff; ; bare") == [
        ("color", "red"),
        ("--sb-swatch", "#fff"),
    ]


def test_declarations_lowercases_the_name_but_keeps_the_value_verbatim() -> None:
    """The property name is normalised; the value is left as written."""
    assert ownership.declarations("Background: Var(--X)") == [
        ("background", "Var(--X)")
    ]


def test_properties_returns_only_the_names() -> None:
    """``properties`` is the names from ``declarations``."""
    assert ownership.properties("gap: 0; display: flex") == ["gap", "display"]


def test_declared_properties_unions_across_every_rule() -> None:
    """Every property anywhere in the sheet, selectors excluded."""
    assert ownership.declared_properties(_SHEET) == {"display", "gap", "color"}


def test_selectors_splits_comma_lists_and_drops_empties() -> None:
    """Comma-separated selector lists split out; an empty fragment is dropped."""
    assert ownership.selectors(".a, .b {x:1} .c {y:2}") == [".a", ".b", ".c"]
    assert ownership.selectors(".a, {x:1}") == [".a"]  # trailing-comma empty dropped


def test_rule_body_returns_the_matching_body_or_empty() -> None:
    """An exact-selector lookup returns its body, or ``""`` when absent."""
    assert "display: flex" in ownership.rule_body(_SHEET, ".a, .b")
    assert ownership.rule_body(_SHEET, ".missing") == ""


def test_subject_is_the_rightmost_compound_without_pseudos_or_attributes() -> None:
    """The subject is the last compound, stripped of pseudo and attribute parts."""
    assert ownership.subject(".a .b:hover") == ".b"
    assert ownership.subject(".x > input[type='text']:focus-visible") == "input"
    assert ownership.subject("td") == "td"


def test_subject_classes_are_the_classes_of_the_rightmost_compound() -> None:
    """Only the last compound's classes count (ancestors are out of subject)."""
    assert ownership.subject_classes(".wrap .a.b") == {"a", "b"}
    assert ownership.subject_classes(".frame.root") == {"frame", "root"}
    assert ownership.subject_classes("button") == set()


def test_declares_matches_a_property_or_its_longhands() -> None:
    """``declares`` is true for the property itself or any ``prop-*`` longhand."""
    props = ["padding-inline", "color"]
    assert ownership.declares(props, "padding")
    assert ownership.declares(["margin"], "margin")
    assert not ownership.declares(props, "margin")


def test_referenced_tokens_lists_every_var_custom_property() -> None:
    """Every ``var(--token)`` reference is collected, in order."""
    assert ownership.referenced_tokens(_SHEET) == ["--sb-space-sm"]
    assert ownership.referenced_tokens("a{x: var( --sb-y )}") == ["--sb-y"]


def test_magic_lengths_flags_bare_lengths_but_not_token_contents_or_zero() -> None:
    """A length written directly is magic; one inside ``var(...)`` or a ``0`` is not."""
    assert ownership.magic_lengths("a{width: 40px}") == {"40px"}
    assert ownership.magic_lengths("a{gap: var(--sb-space-sm)}") == set()
    assert ownership.magic_lengths("a{inset: 0}") == set()
    assert ownership.magic_lengths("a{margin: 0px}") == set()  # zero is owned


def test_inline_styles_extracts_every_style_attribute_value() -> None:
    """Each element's inline ``style`` value is returned; other markup is ignored."""
    html = '<span class="x" style="--sb-swatch:#fff"></span><i>no style</i>'
    assert ownership.inline_styles(html) == ["--sb-swatch:#fff"]
    assert ownership.inline_styles("<b>plain</b>") == []


def test_structural_policy_constants_are_populated() -> None:
    """The structural policy exposes a non-empty allowlist and the prefix rules."""
    assert "display" in ownership.LAYOUT_PROPERTIES
    assert "background" not in ownership.LAYOUT_PROPERTIES
    assert ownership.CONTRACT_TOKEN_PREFIX == "--sb-fit-"
    assert ownership.INLINE_VALUE_PREFIX == "--sb-"


def test_structural_hooks_are_the_no_inset_layout_vocabulary() -> None:
    """The no-inset denylist holds the layout/mount/region hooks, not the controls.

    A control or content surface (the open set the theme may inset) is absent; the
    closed set of structural hooks — frames, the root, the mount point, the rail,
    the region cells — is present. The padding guard reads this set as a denylist.
    """
    assert {"sb-frame", "sb-root", "sb-island", "sb-rail"} <= ownership.STRUCTURAL_HOOKS
    assert {"sb-body-c", "sb-head-row"} <= ownership.STRUCTURAL_HOOKS
    assert "sb-color-input-text" not in ownership.STRUCTURAL_HOOKS  # a control insets
    assert "button" not in ownership.STRUCTURAL_HOOKS
