"""Declared escape hatches: an island steps outside the governed mount point only by saying so.

Philosophy §17 ("Escape Hatches"): a mature system needs exceptions, but every
exception must declare its authority. An island is governed by default (a mount
point the cell sizes and clips). A :class:`SpatialEscape` is the one sanctioned
way to deviate: it adds the structural role class that honors the chosen overflow
and records the exception in ``data-escape`` / ``data-paint-outset``, so the
escape is explicit and inspectable, never a silent overflow.
"""

from switchboard_ui.model import Island, SpatialEscape
from switchboard_ui.render import render_island

from .htmlprobe import elements


def _island_attrs(html: str) -> dict[str, str]:
    """The attributes of the rendered island mount ``<div>``."""
    return next(
        attrs
        for tag, attrs in elements(html)
        if tag == "div" and "sb-island" in attrs.get("class", "")
    )


def test_escape_defaults_are_conservative() -> None:
    """An undeclared escape clips and bleeds no paint (the governed defaults)."""
    escape = SpatialEscape()
    assert escape.overflow == "clip"
    assert escape.paint_outset == ""


def test_a_governed_island_declares_no_escape() -> None:
    """With no escape, the island is a bare mount point: no role class, no escape data."""
    attrs = _island_attrs(render_island(Island(name="x")))
    assert attrs["class"] == "sb-island"
    assert "data-escape" not in attrs
    assert "data-paint-outset" not in attrs


def test_a_scroll_escape_owns_its_scroll_and_declares_its_outset() -> None:
    """A scroll escape takes the scroll role and records its overflow and paint outset."""
    island = Island(
        name="x", escape=SpatialEscape(overflow="scroll", paint_outset="0.5rem")
    )
    attrs = _island_attrs(render_island(island))
    assert "sb-scroll" in attrs["class"].split()
    assert attrs["data-escape"] == "scroll"
    assert attrs["data-paint-outset"] == "0.5rem"


def test_a_clip_escape_clips_and_omits_an_empty_outset() -> None:
    """A clip escape takes the clip role; an empty paint outset is not rendered."""
    attrs = _island_attrs(
        render_island(Island(name="x", escape=SpatialEscape(overflow="clip")))
    )
    assert "sb-clip" in attrs["class"].split()
    assert attrs["data-escape"] == "clip"
    assert "data-paint-outset" not in attrs


def test_a_visible_escape_is_declared_without_a_role_class() -> None:
    """A visible (bleed) escape adds no class (it is the island's default) but is still declared."""
    attrs = _island_attrs(
        render_island(Island(name="x", escape=SpatialEscape(overflow="visible")))
    )
    assert attrs["class"] == "sb-island"
    assert attrs["data-escape"] == "visible"
