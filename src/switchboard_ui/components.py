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

from collections.abc import Sequence

from switchboard_ui.assets import read_static
from switchboard_ui.html import element, escape_text
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
