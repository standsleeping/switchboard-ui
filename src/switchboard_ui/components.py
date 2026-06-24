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
from dataclasses import dataclass
from typing import Literal, assert_never

from switchboard_ui.assets import read_static
from switchboard_ui.html import attributes, classes, element, escape_text
from switchboard_ui.model import Island, Json
from switchboard_ui.render import render_island

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


def _hex_field(value: str, label: str) -> str:
    """The hex ``<input>`` shared by the color input and the color picker."""
    return (
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
    initial = element(
        "div", {"class": "sb-color-input"}, [swatch, _hex_field(value, label)]
    )
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
    trigger_class: str = "",
    trigger_label: str | None = None,
    trigger_style: str = "",
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
    bus echo of ``{"open": bool}``.

    ``trigger_class`` adds classes to the trigger button (e.g. to style it as a
    chip), and ``trigger_label`` gives the trigger its own accessible name — which
    a content-less chip trigger needs, and which lets ``trigger`` be empty. Raises
    :class:`ValueError` at the authoring boundary if ``label`` is blank,
    ``panel_id`` is not a valid HTML id, ``panel`` is empty, or ``trigger`` is
    empty without a ``trigger_label``.
    """
    if not label:
        raise ValueError("popover requires a non-empty label (the panel's name)")
    if not _ID.match(panel_id):
        raise ValueError(f"popover panel_id {panel_id!r} is not a valid HTML id")
    if not trigger and not trigger_label:
        raise ValueError("popover requires trigger content or a trigger_label")
    if not panel:
        raise ValueError("popover requires panel content")
    trigger_el = element(
        "button",
        {
            "class": classes("sb-popover-trigger", trigger_class),
            "type": "button",
            "popovertarget": panel_id,
            "aria-haspopup": haspopup,
            "aria-controls": panel_id,
            "aria-expanded": "false",
            "aria-label": trigger_label,
            "style": trigger_style or None,
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


def _picker_panel(label: str) -> str:
    """The picker's popover panel: a saturation/value area over a hue slider.

    Both surfaces are ``role="slider"`` so pointer and keyboard both drive them;
    their handle positions and spectrum gradients are the adapter's (the spectrum
    is functional data-viz set inline, the one sanctioned exception to the
    token-only rule). The hex field carries the precise value and is the
    accessible backbone; the spectrum is the visual affordance.
    """
    area = element(
        "div",
        {
            "class": "sb-color-picker-area",
            "role": "slider",
            "tabindex": "0",
            "aria-roledescription": "saturation and brightness",
            "aria-label": f"{label} saturation and brightness",
            "aria-valuetext": "saturation, brightness",
        },
        [
            element(
                "span", {"class": "sb-color-picker-area-handle", "aria-hidden": "true"}
            )
        ],
    )
    hue = element(
        "div",
        {
            "class": "sb-color-picker-hue",
            "role": "slider",
            "tabindex": "0",
            "aria-label": f"{label} hue",
            "aria-orientation": "horizontal",
            "aria-valuemin": "0",
            "aria-valuemax": "360",
            "aria-valuenow": "0",
            "aria-valuetext": "hue",
        },
        [
            element(
                "span", {"class": "sb-color-picker-hue-thumb", "aria-hidden": "true"}
            )
        ],
    )
    return element("div", {"class": "sb-color-picker-controls"}, [area, hue])


def color_picker(*, topic: str, value: str, label: str) -> Island:
    """A visual colour picker: a swatch that opens a spectrum popover, plus a hex field.

    Augments :func:`color_input`: the swatch becomes a popover trigger that
    reveals a saturation/value area and a hue slider; the inline hex field stays
    as the precise, fully-accessible control. The swatch, the spectrum, and the
    field stay in sync and all publish the chosen ``#rrggbb`` on ``topic``.
    ``value`` is the initial colour (six-digit hex) and ``label`` names the
    control. Raises :class:`ValueError` at the authoring boundary if ``value`` is
    not a six-digit hex or ``label`` is blank.
    """
    if not _HEX.match(value):
        msg = f"color_picker value {value!r} is not a six-digit hex colour (#rrggbb)"
        raise ValueError(msg)
    if not label:
        raise ValueError("color_picker requires a non-empty label (the control's name)")
    panel_id = "sb-cp-" + re.sub(r"[^A-Za-z0-9_-]", "-", topic)
    trigger = popover(
        trigger="",
        panel=_picker_panel(label),
        label=label,
        panel_id=panel_id,
        trigger_class="sb-color-picker-swatch",
        trigger_label=label,
        trigger_style=f"background:{value}",
    )
    initial = element(
        "div",
        {"class": "sb-color-picker"},
        [render_island(trigger), _hex_field(value, label)],
    )
    return Island(
        name="color-picker", props={"topic": topic}, publishes=(topic,), initial=initial
    )


def color_picker_scripts() -> tuple[str, ...]:
    """The color-picker adapter. The picker composes the popover, so a host also
    includes :func:`popover_scripts` (the two adapters, wired like two islands)."""
    return (read_static("color-picker.js"),)


def color_picker_styles() -> str:
    """The color-picker structural CSS. Pair with :func:`popover_styles` (the
    picker composes the popover), the way the adapters are paired."""
    return read_static("color-picker.css")


def _num(x: float) -> str:
    """Render a slider bound without a spurious trailing ``.0`` (``200``, not ``200.0``)."""
    return str(int(x)) if float(x).is_integer() else str(x)


def slider(
    *,
    topic: str,
    min: float,
    max: float,
    value: float,
    label: str,
    step: float = 1,
    readout: bool = True,
) -> Island:
    """A slider: drag a numeric value in ``[min, max]``, publishing it on ``topic``.

    A native range, restyled to the house look. ``value`` is the initial value
    (in range), ``step`` the increment, ``label`` the control's accessible name;
    ``readout`` shows the live value beside the track. Dragging publishes the
    value as a number — an ``int`` when ``min``/``max``/``step``/``value`` are all
    whole, else a ``float`` (decided here and carried as the ``integer`` prop).
    Raises :class:`ValueError` at the authoring boundary if ``min >= max``,
    ``step <= 0``, ``value`` is out of range, or ``label`` is blank.
    """
    if min >= max:
        raise ValueError(f"slider requires min < max, got min={min!r}, max={max!r}")
    if step <= 0:
        raise ValueError(f"slider step must be positive, got {step!r}")
    if not min <= value <= max:
        raise ValueError(f"slider value {value!r} is not in [{_num(min)}, {_num(max)}]")
    if not label:
        raise ValueError("slider requires a non-empty label (the control's name)")
    integer = all(float(x).is_integer() for x in (min, max, step, value))
    field = (
        "<input"
        + attributes(
            {
                "class": "sb-slider-input",
                "type": "range",
                "min": _num(min),
                "max": _num(max),
                "step": _num(step),
                "value": _num(value),
                "aria-label": label,
            }
        )
        + ">"
    )
    children = [field]
    if readout:
        children.append(
            element(
                "span",
                {"class": "sb-slider-value", "aria-hidden": "true"},
                [escape_text(_num(value))],
            )
        )
    initial = element("div", {"class": "sb-slider"}, children)
    return Island(
        name="slider",
        props={"topic": topic, "integer": integer},
        publishes=(topic,),
        initial=initial,
    )


def slider_scripts() -> tuple[str, ...]:
    """The slider adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("slider.js"),)


def slider_styles() -> str:
    """The slider structural CSS, for the host to inline in ``extra_head``."""
    return read_static("slider.css")


def value_field(*, topic: str, value: str, label: str) -> Island:
    """A labelled text field that publishes its value on ``topic``.

    The general single-line editor for a scheme-invariant token whose value is a
    CSS string: a length (``0.75rem``), a number (``400``), a font family, a
    shadow. ``value`` is the initial text, ``label`` the field's accessible name.
    Editing it publishes the raw string on ``topic`` — a :func:`theme_state`
    :class:`ValueBinding` writes that string straight onto the bound token, so the
    preview repaints. Unlike :func:`color_input` it validates nothing: any string
    is a candidate CSS value and the live preview is the feedback. Raises
    :class:`ValueError` at the authoring boundary if ``label`` is blank.
    """
    if not label:
        raise ValueError("value_field requires a non-empty label (the field's name)")
    field = (
        "<input"
        + attributes(
            {
                "class": "sb-value-field-text",
                "type": "text",
                "value": value,
                "spellcheck": "false",
                "autocomplete": "off",
                "aria-label": label,
            }
        )
        + ">"
    )
    initial = element("div", {"class": "sb-value-field"}, [field])
    return Island(
        name="value-field", props={"topic": topic}, publishes=(topic,), initial=initial
    )


def value_field_scripts() -> tuple[str, ...]:
    """The value-field adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("value-field.js"),)


def value_field_styles() -> str:
    """The value-field structural CSS, for the host to inline in ``extra_head``."""
    return read_static("value-field.css")


def _preview_sample() -> str:
    """A representative sample of surfaces, to exercise the token adjacencies live."""
    heading = element("p", {"class": "sb-preview-heading"}, [escape_text("Heading")])
    prose = element(
        "p",
        {"class": "sb-preview-prose"},
        [escape_text("Body text in the prose family, sized and coloured by tokens.")],
    )
    button = element("button", {"type": "button"}, [escape_text("Primary")])
    swatch = element(
        "span",
        {
            "class": "sb-preview-swatch",
            "aria-hidden": "true",
            "style": "background:var(--sb-color-accent)",
        },
    )
    header = element(
        "tr",
        {},
        [
            element("th", {}, [escape_text("Token")]),
            element("th", {}, [escape_text("Role")]),
        ],
    )
    body = [
        element(
            "tr",
            {},
            [
                element("td", {}, [escape_text(name)]),
                element("td", {}, [escape_text(role)]),
            ],
        )
        for name, role in (("accent", "interactive"), ("fg", "text"))
    ]
    table = element(
        "table",
        {"class": "sb-preview-table"},
        [element("thead", {}, [header]), element("tbody", {}, body)],
    )
    return element(
        "div", {"class": "sb-preview-sample"}, [heading, prose, button, swatch, table]
    )


def preview(*, scope_id: str, scheme: Literal["light", "dark"] | None = None) -> Island:
    """A live preview surface: a sample of components that repaints as tokens change.

    Renders a representative sample inside a scope wrapper carrying ``scope_id``
    (as ``data-sb-scope``); a sibling :func:`theme_state` island writes token
    overrides onto that wrapper, and everything inside repaints because it reads
    ``var(--sb-*)``. ``scheme`` pins the pane to one colour scheme (a side-by-side
    light/dark builder renders two). The preview is a static display surface — no
    adapter — so it is also a plain gallery specimen. Raises :class:`ValueError`
    at the authoring boundary if ``scope_id`` is blank.
    """
    if not scope_id:
        raise ValueError("preview requires a non-empty scope_id")
    scope = element(
        "div",
        {
            "class": classes(
                "sb-preview-scope", f"sb-preview-{scheme}" if scheme else ""
            ),
            "data-sb-scope": scope_id,
        },
        [_preview_sample()],
    )
    return Island(
        name="preview", initial=element("div", {"class": "sb-preview"}, [scope])
    )


def preview_styles() -> str:
    """The preview structural CSS, for the host to inline in ``extra_head``."""
    return read_static("preview.css")


@dataclass(frozen=True)
class ArmBinding:
    """Bind a topic to one scheme arm of a scheme-varying token.

    A scheme-varying token (a colour) is authored per ``-light`` / ``-dark`` arm,
    composed with ``light-dark()``. This binding edits *one* arm: publishing a
    value writes ``<token>-<arm>`` onto the scope and re-declares the
    ``light-dark()`` composition there, so the scoped subtree repaints in that
    arm's scheme. Two arm bindings on the same topic (one per arm) move both arms
    in lockstep; distinct topics edit each arm independently.
    """

    topic: str
    token: str
    arm: Literal["light", "dark"]


@dataclass(frozen=True)
class ValueBinding:
    """Bind a topic to a scheme-invariant token, set directly (no arms).

    Lengths, numbers, and font families do not vary by scheme, so publishing a
    value writes it straight onto the token (``setProperty(token, value)``) with no
    composition.
    """

    topic: str
    token: str


Binding = ArmBinding | ValueBinding
"""One token edit the theme-state island applies: an arm edit or a direct value."""


def _binding_payload(binding: Binding) -> dict[str, Json]:
    """Serialize a binding to the ``kind``-tagged dict the adapter dispatches on."""
    match binding:
        case ArmBinding(topic=topic, token=token, arm=arm):
            return {"kind": "arm", "topic": topic, "token": token, "arm": arm}
        case ValueBinding(topic=topic, token=token):
            return {"kind": "value", "topic": topic, "token": token}
    assert_never(binding)  # pragma: no cover


def theme_state(*, scope: str, bindings: Sequence[Binding]) -> Island:
    """The apply-edit island: write bound token edits onto a scoped element.

    ``scope`` is a CSS selector for the override target(s) (e.g. a preview's
    ``[data-sb-scope]`` wrapper); ``bindings`` lists the token edits to apply.
    Each is an :class:`ArmBinding` (one scheme arm of a colour) or a
    :class:`ValueBinding` (a scheme-invariant length/number/family). When a bound
    topic publishes a value, the adapter writes it onto every scoped element, so
    the scoped subtree repaints. The token names come from the trusted bindings,
    never from a published value, so a value can only ever be a CSS value. The
    island has no markup of its own. Raises :class:`ValueError` at the authoring
    boundary if ``scope`` is blank or ``bindings`` is empty.
    """
    if not scope:
        raise ValueError("theme_state requires a non-empty scope selector")
    if not bindings:
        raise ValueError("theme_state requires at least one binding")
    # A topic appears once in the declared subscription set even when two arm
    # bindings share it (the static-analysis surface lists each topic once); the
    # adapter still wires one handler per binding at runtime.
    topics = tuple(dict.fromkeys(b.topic for b in bindings))
    return Island(
        name="theme-state",
        props={"scope": scope, "bindings": [_binding_payload(b) for b in bindings]},
        subscribes=topics,
    )


def theme_state_scripts() -> tuple[str, ...]:
    """The theme-state adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("theme-state.js"),)


def theme_export(*, scope: str, bindings: Sequence[Binding]) -> Island:
    """An export control: serialise a scope's current tokens to a ``tokens.css``.

    The read-back sibling of :func:`theme_state`. It renders a button that, on
    click, reads every bound token's current value off the ``scope`` (with
    ``getComputedStyle``, so an unedited token exports its inherited default) and
    assembles a ``:root`` block — an arm token as its two arms plus the
    ``light-dark()`` composition, a value token as one declaration — then copies it
    to the clipboard. ``bindings`` is the same list :func:`theme_state` applies, so
    the export covers exactly the editable set. The button carries no topic (it
    reads on demand, not over the bus). Raises :class:`ValueError` at the authoring
    boundary if ``scope`` is blank or ``bindings`` is empty.
    """
    if not scope:
        raise ValueError("theme_export requires a non-empty scope selector")
    if not bindings:
        raise ValueError("theme_export requires at least one binding")
    button = element(
        "button",
        {"type": "button", "class": "sb-export-button"},
        [escape_text("Copy tokens.css")],
    )
    status = element(
        "span",
        {"class": "sb-export-status", "role": "status", "aria-live": "polite"},
        (),
    )
    initial = element("div", {"class": "sb-export"}, [button, status])
    return Island(
        name="theme-export",
        props={"scope": scope, "bindings": [_binding_payload(b) for b in bindings]},
        initial=initial,
    )


def theme_export_scripts() -> tuple[str, ...]:
    """The theme-export adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("theme-export.js"),)


def theme_export_styles() -> str:
    """The theme-export structural CSS, for the host to inline in ``extra_head``."""
    return read_static("theme-export.css")
