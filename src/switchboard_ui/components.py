"""Interactive components: descriptor factories for the canonical island set.

A component is three parts that ship together: a descriptor factory here (the
Python side), a mount adapter under ``static/<component>.js`` (the browser side),
and structural CSS under ``static/<component>.css`` (geometry keyed to the
component's ``.sb-*`` hooks). The factory returns an :class:`Island`; the host
opts the adapter and CSS in exactly as the demo wires its adapters. All
appearance comes from the theme's ``--sb-*`` tokens, so a component carries no
baked visual opinion and re-skins by swapping tokens.

The segmented toggle is the first: a single-select control (visually a row of
mono options, the selected one underlined with the accent) that publishes the
chosen value on a bus topic. It carries no content panel of its own — it emits a
value and some other island reacts — so its semantics are a **radio group**
(``role="radiogroup"`` of ``role="radio"`` options), not tabs (tabs must own a
``tabpanel`` via ``aria-controls``, which this control has nothing to point at).

Its options are server-rendered into ``initial`` so the control is present,
correctly sized, and correctly focus-ordered (roving ``tabindex``) at first
paint, before the adapter enhances it. The adapter wires pointer and keyboard
interaction (click, and the radio-group arrow / Home / End navigation with
selection following focus); it never builds or resizes the control.

Tokens the segmented paint consumes (documentation, not yet a manifest):
``--sb-space-sm`` (gap and inset), ``--sb-color-muted`` / ``--sb-color-fg`` (idle
and selected label), ``--sb-color-accent`` (the underline), ``--sb-color-subtle``
(the separators), ``--sb-border-width-accent`` (the underline width).
"""

import re
from collections.abc import Sequence
from typing import Literal

from switchboard_ui.assets import read_static
from switchboard_ui.html import attributes, element, escape_text
from switchboard_ui.model import Island

_ADAPTER = "segmented"

# An inert separator between options (a dot), ignored by the adapter and hidden
# from assistive tech; the theme colours it.
_SEPARATOR = element(
    "span", {"class": "sb-segmented-sep", "aria-hidden": "true"}, ["·"]
)


def _option(value: str, label: str, *, checked: bool) -> str:
    """One radio option, server-rendered so it is present and focus-ordered at first paint.

    The checked option is the group's single tab stop (``tabindex="0"``); the rest
    are reachable only by the arrow keys (``tabindex="-1"``, roving tabindex).
    """
    return element(
        "button",
        {
            "class": "sb-segmented-option",
            "type": "button",
            "role": "radio",
            "data-value": value,
            "aria-checked": "true" if checked else "false",
            "tabindex": "0" if checked else "-1",
        },
        [escape_text(label)],
    )


def segmented(
    *,
    topic: str,
    options: Sequence[tuple[str, str]],
    value: str,
    label: str,
) -> Island:
    """A segmented toggle: pick one of ``options``, publish its value on ``topic``.

    ``options`` is an ordered sequence of ``(value, label)`` pairs; ``value`` is
    the initially-selected option's value and must be one of them; ``label`` names
    the group for assistive tech (a radio group's required accessible name).
    Selecting an option publishes its value on ``topic``. Raises :class:`ValueError`
    at the authoring boundary if ``options`` is empty, ``value`` is not among them,
    or ``label`` is blank — so a bad call fails where it is written, not at render
    or in the browser.
    """
    if not options:
        raise ValueError("segmented requires at least one option")
    if not label:
        raise ValueError("segmented requires a non-empty label (the group's name)")
    values = [v for v, _ in options]
    if value not in values:
        msg = f"segmented value {value!r} is not among options {values!r}"
        raise ValueError(msg)
    items: list[str] = []
    for index, (opt_value, opt_label) in enumerate(options):
        if index:
            items.append(_SEPARATOR)
        items.append(_option(opt_value, opt_label, checked=opt_value == value))
    initial = element(
        "div",
        {"class": "sb-segmented", "role": "radiogroup", "aria-label": label},
        items,
    )
    return Island(
        name=_ADAPTER,
        props={"topic": topic},
        publishes=(topic,),
        initial=initial,
    )


def segmented_scripts() -> tuple[str, ...]:
    """The segmented adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("segmented.js"),)


def segmented_styles() -> str:
    """The segmented structural CSS, for the host to inline in ``extra_head``."""
    return read_static("segmented.css")


# A six-digit hex colour (``#rrggbb``); the palette the theme-builder edits is all
# six-digit, so the v0 field accepts exactly that.
_HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")


def color_input(*, topic: str, value: str, label: str) -> Island:
    """A themed colour input: a swatch plus a hex field that publishes ``value``.

    A tokenised replacement for the native ``<input type="color">`` (whose picker
    popover is UA-painted and cannot be themed). ``value`` is the initial colour
    as a six-digit hex (``#rrggbb``); ``label`` is the field's accessible name.
    Editing the field to a valid hex repaints the swatch and publishes the colour
    on ``topic``. Raises :class:`ValueError` at the authoring boundary if ``value``
    is not a six-digit hex or ``label`` is blank, so a bad call fails where it is
    written, not at render or in the browser.
    """
    if not _HEX.match(value):
        msg = f"color_input value {value!r} is not a six-digit hex colour (#rrggbb)"
        raise ValueError(msg)
    if not label:
        raise ValueError("color_input requires a non-empty label (the field's name)")
    swatch = element(
        "span",
        {
            "class": "sb-color-input-swatch",
            "aria-hidden": "true",
            "style": f"background:{value}",
        },
    )
    field = (
        "<input"
        + attributes(
            {
                "class": "sb-color-input-text",
                "type": "text",
                "value": value,
                "size": "8",
                "maxlength": "7",
                "spellcheck": "false",
                "autocomplete": "off",
                "aria-label": label,
                "aria-invalid": "false",
            }
        )
        + ">"
    )
    initial = element("div", {"class": "sb-color-input"}, [swatch, field])
    return Island(
        name="color-input", props={"topic": topic}, publishes=(topic,), initial=initial
    )


def color_input_scripts() -> tuple[str, ...]:
    """The color-input adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("color-input.js"),)


def color_input_styles() -> str:
    """The color-input structural CSS, for the host to inline in ``extra_head``."""
    return read_static("color-input.css")


# A valid HTML id: the panel id links the trigger to the panel via popovertarget
# and aria-controls, so a malformed value silently breaks the wiring.
_ID = re.compile(r"[A-Za-z][\w:.-]*\Z")

HasPopup = Literal["dialog", "menu", "listbox", "grid", "tree", "true"]
"""The `aria-haspopup` kind the trigger advertises (what the panel contains)."""


def popover(
    *,
    trigger: str,
    panel: str,
    label: str,
    panel_id: str,
    haspopup: HasPopup = "dialog",
    panel_role: str = "group",
    open_topic: str | None = None,
) -> Island:
    """A reusable popover: a trigger that reveals a floating panel anchored to it.

    A generic overlay primitive — supply the ``trigger`` content (e.g. a swatch)
    and the ``panel`` content (e.g. a picker) as raw-HTML fragments; ``label`` is
    the panel's accessible name and ``panel_id`` links the two (it lands in the
    panel ``id`` and the trigger's ``popovertarget`` / ``aria-controls``). The
    panel is a native ``[popover]``: the UA renders it in the top layer (so it
    escapes ancestor clipping) and gives light-dismiss and Esc for free; the
    adapter adds focus management, positioning, and an optional ``open_topic``
    bus echo of ``{"open": bool}``. Raises :class:`ValueError` at the authoring
    boundary if ``label`` is blank, ``panel_id`` is not a valid HTML id, or
    ``trigger`` / ``panel`` is empty.
    """
    if not label:
        raise ValueError("popover requires a non-empty label (the panel's name)")
    if not _ID.match(panel_id):
        raise ValueError(f"popover panel_id {panel_id!r} is not a valid HTML id")
    if not trigger:
        raise ValueError("popover requires trigger content")
    if not panel:
        raise ValueError("popover requires panel content")
    trigger_el = element(
        "button",
        {
            "class": "sb-popover-trigger",
            "type": "button",
            "popovertarget": panel_id,
            "aria-haspopup": haspopup,
            "aria-controls": panel_id,
            "aria-expanded": "false",
        },
        [trigger],
    )
    panel_el = element(
        "div",
        {
            "class": "sb-popover-panel",
            "id": panel_id,
            "popover": "auto",
            "role": panel_role,
            "aria-label": label,
        },
        [panel],
    )
    initial = element("div", {"class": "sb-popover"}, [trigger_el, panel_el])
    return Island(
        name="popover",
        props={"topic": open_topic} if open_topic else {},
        publishes=(open_topic,) if open_topic else (),
        initial=initial,
    )


def popover_scripts() -> tuple[str, ...]:
    """The popover adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("popover.js"),)


def popover_styles() -> str:
    """The popover structural CSS, for the host to inline in ``extra_head``."""
    return read_static("popover.css")
