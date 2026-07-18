"""The component layer carries no paint through inline ``style`` — only ``--sb-*`` values.

A factory may legitimately carry a per-instance *value* on a rendered element (a
user-chosen color the theme paints from), but never a *declaration* of paint or
geometry: a ``background`` / ``color`` / ``border`` belongs to the theme, a
``flex`` / ``position`` to the structural layer. So every inline ``style`` a
factory renders must declare only ``--sb-*`` custom properties; the theme owns the
property that reads them (``.sb-color-input-swatch { background: var(--sb-swatch) }``).

This watches a channel the ``.css`` guards cannot see. ``test_layout_css`` and
``test_theme_css`` parse stylesheets, so a ``background`` written into a ``style=``
attribute from Python would slip past them entirely — exactly the leak the swatch
factories used to carry. The color swatch is the live example: its color is a
per-instance value, carried as ``--sb-swatch`` and painted by the theme, never an
inline paint declaration. (The structural ``flex`` sizing the render layer applies
to slots is a separate, sanctioned channel on the mount wrapper, outside the
factory's ``initial``; it is the render layer's geometry to own, not paint.)
"""

from switchboard_ui import ownership
from switchboard_ui.components import (
    Cell,
    ValueBinding,
    breadcrumb,
    code_block,
    collapsible,
    color_input,
    color_picker,
    modal,
    popover,
    preview,
    segmented,
    slider,
    table,
    theme_export,
    value_field,
)
from switchboard_ui.model import Island


def _specimens() -> list[tuple[str, str]]:
    """A representative rendered ``initial`` for every factory that emits markup.

    One specimen per factory, so the whole component layer is watched: a new
    factory that smuggles paint into an inline ``style`` is caught the moment its
    specimen lands here.
    """
    islands: dict[str, Island] = {
        "segmented": segmented(
            topic="t", options=(("a", "A"), ("b", "B")), value="a", label="View"
        ),
        "color_input": color_input(topic="t", value="#5b4bd6", label="Accent"),
        "color_picker": color_picker(topic="t", value="#5b4bd6", label="Accent"),
        "popover": popover(
            trigger="<span>open</span>", panel="<p>x</p>", label="P", panel_id="p"
        ),
        "slider": slider(topic="t", min=0, max=10, value=4, label="N"),
        "value_field": value_field(topic="t", value="0.5rem", label="Radius"),
        "preview-light": preview(scope_id="p", scheme="light"),
        "preview-dark": preview(scope_id="p", scheme="dark"),
        "table": table(
            columns=("Doc",), rows=((Cell('<a href="/x">X</a>'),),), label="Docs"
        ),
        "code_block": code_block(code="x = 1", label="Example", language="python"),
        "modal": modal(
            trigger="Open", body="<p>x</p>", label="D", dialog_id="d", title="Dialog"
        ),
        "breadcrumb": breadcrumb(trail=(("Home", "/"),), current="Page"),
        "collapsible": collapsible(title="Items", body="<p>x</p>", count=2),
        "theme_export": theme_export(
            scope="[data-sb-scope]",
            bindings=(ValueBinding(topic="t", token="--sb-radius-base"),),
        ),
    }
    return [(name, island.initial) for name, island in islands.items()]


def test_factories_carry_only_custom_properties_inline() -> None:
    """Every inline ``style`` a factory renders declares only ``--sb-*`` values.

    A non-custom-property — a ``background``, a ``color``, a ``flex`` — is a paint
    or geometry declaration the factory does not own; it belongs to the theme or
    the structural layer, reached through a token or a hook, not an inline style.
    """
    for name, html in _specimens():
        for style in ownership.inline_styles(html):
            for prop in ownership.properties(style):
                assert prop.startswith(ownership.INLINE_VALUE_PREFIX), (
                    f"{name} carries inline paint/geometry {prop!r} in style "
                    f"{style!r}; a factory may carry only --sb-* values inline "
                    f"(the theme owns the property that reads them)"
                )


def test_the_guard_sees_the_swatch_value_channel() -> None:
    """The guard actually inspects inline styles: the swatch carries its --sb-swatch value.

    A guard that found nothing to check would pass vacuously. The color swatches
    are the one factory output that carries an inline ``style`` at all, so their
    presence proves the reader reaches the channel it is meant to watch.
    """
    initial = color_input(topic="t", value="#5b4bd6", label="A").initial
    assert ownership.inline_styles(initial) == ["--sb-swatch:#5b4bd6"]
