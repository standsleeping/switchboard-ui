"""Tests for the HTML builder."""

from switchboard_ui.html import attributes, classes, element, escape_attr, escape_text


def test_escape_text_escapes_markup_not_quotes() -> None:
    """Character data escapes angle brackets and ampersands, leaves quotes."""
    assert escape_text('a < b & c "d"') == 'a &lt; b &amp; c "d"'


def test_escape_attr_escapes_quotes() -> None:
    """Attribute values additionally escape double quotes."""
    assert escape_attr('he said "hi" <b>') == "he said &quot;hi&quot; &lt;b&gt;"


def test_classes_joins_present_tokens() -> None:
    """Non-empty class tokens join with single spaces."""
    assert classes("sb-island", "brand") == "sb-island brand"


def test_classes_drops_empty_tokens() -> None:
    """An empty token is filtered, so an absent class adds no stray space."""
    assert classes("sb-frame", "", "sb-root") == "sb-frame sb-root"


def test_classes_of_nothing_is_empty() -> None:
    """No tokens yields an empty string."""
    assert classes() == ""


def test_attributes_renders_present_and_omits_none() -> None:
    """A None value drops the attribute; present values are escaped."""
    rendered = attributes({"class": "x", "data-v": 'a"b', "hidden": None})
    assert rendered == ' class="x" data-v="a&quot;b"'


def test_element_wraps_children() -> None:
    """element joins raw-HTML children inside the tag."""
    assert element("div", {"id": "z"}, ["<b>hi</b>"]) == '<div id="z"><b>hi</b></div>'


def test_element_defaults_to_no_attrs_no_children() -> None:
    """Omitting attrs and children yields an empty tag."""
    assert element("span") == "<span></span>"


def test_empty_element_has_no_inner_whitespace_so_css_empty_can_collapse_it() -> None:
    """An empty element renders with nothing between its tags.

    layout.css collapses omitted region cells with `.sb-frame:empty { display: none }`,
    and the CSS `:empty` pseudo-class does not match an element that contains even
    whitespace. So every empty frame the renderer emits must carry no inner text;
    this pins that guarantee at its source, `element`, where the children join with
    no separator.
    """
    assert element("div", {"class": "sb-frame sb-frame-column"}) == (
        '<div class="sb-frame sb-frame-column"></div>'
    )
