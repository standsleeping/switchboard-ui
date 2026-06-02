"""Tests for the HTML builder."""

from switchboard_ui.html import attributes, element, escape_attr, escape_text


def test_escape_text_escapes_markup_not_quotes() -> None:
    """Character data escapes angle brackets and ampersands, leaves quotes."""
    assert escape_text('a < b & c "d"') == 'a &lt; b &amp; c "d"'


def test_escape_attr_escapes_quotes() -> None:
    """Attribute values additionally escape double quotes."""
    assert escape_attr('he said "hi" <b>') == "he said &quot;hi&quot; &lt;b&gt;"


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
