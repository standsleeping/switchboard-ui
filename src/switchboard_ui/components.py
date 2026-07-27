"""Interactive components: descriptor factories for the canonical island set.

A component is three parts that ship together: a descriptor factory here (the
Python side), a mount adapter under ``static/<component>.js`` (the browser side),
and structural CSS under ``static/<component>.css`` (geometry keyed to the
component's ``.sb-*`` hooks). The factory returns an :class:`Island`; the host
opts the adapter and CSS in exactly as the demo wires its adapters. All
appearance comes from the theme's ``--sb-*`` tokens, so a component carries no
baked visual opinion and re-skins by swapping tokens.

The set spans interactive controls (the segmented toggle, color input/picker,
popover, modal, slider, value field) and display surfaces (the live preview, the
:func:`table`, the :func:`code_block`, the :func:`breadcrumb`, and the
:func:`collapsible` section). A display surface is the same shape
minus the behavior: a :func:`table` ships no adapter at all (it is inert markup
plus structure plus paint), while a :func:`code_block` ships one only for its
copy action. Both own their horizontal scroll on their own content element, so a
wide table or a long code line never pushes the page (the scroll-containment
contract).

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

import colorsys
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
# from assistive tech; the theme colors it.
_SEPARATOR = element(
    "span", {"class": "sb-segmented-sep", "aria-hidden": "true"}, ["·"]
)


def _control_props(topic: str, listen: str | None) -> dict[str, Json]:
    """The props shared by every value control: its publish topic, plus the
    optional ``listen`` topic it follows.

    A control that listens applies an incoming value in place and never
    republishes it: an applied value is synced state, not user input, so two
    controls may follow each other without echoing. The empty string is rejected
    here so every control fails the same way at the authoring boundary.
    """
    if listen == "":
        raise ValueError("listen must be a non-empty topic (or None)")
    props: dict[str, Json] = {"topic": topic}
    if listen is not None:
        props["listen"] = listen
    return props


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
    listen: str | None = None,
) -> Island:
    """A segmented toggle: pick one of ``options``, publish its value on ``topic``.

    ``options`` is an ordered sequence of ``(value, label)`` pairs; ``value`` is
    the initially-selected option's value and must be one of them; ``label`` names
    the group for assistive tech (a radio group's required accessible name).
    Selecting an option publishes its value on ``topic``. ``listen`` names an
    optional topic the control follows: a value published there moves the
    selection in place — without stealing focus and without republishing, so
    another island can drive this one over the bus with no echo. Raises
    :class:`ValueError` at the authoring boundary if ``options`` is empty,
    ``value`` is not among them, or ``label`` is blank — so a bad call fails
    where it is written, not at render or in the browser.
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
        props=_control_props(topic, listen),
        publishes=(topic,),
        subscribes=(listen,) if listen else (),
        initial=initial,
    )


def segmented_scripts() -> tuple[str, ...]:
    """The segmented adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("segmented.js"),)


def segmented_styles() -> str:
    """The segmented structural CSS, for the host to inline in ``extra_head``."""
    return read_static("segmented.css")


# A six-digit hex color (``#rrggbb``); the palette the theme-builder edits is all
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


def color_input(
    *, topic: str, value: str, label: str, listen: str | None = None
) -> Island:
    """A themed color input: a swatch plus a hex field that publishes ``value``.

    A tokenised replacement for the native ``<input type="color">`` (whose picker
    popover is UA-painted and cannot be themed). ``value`` is the initial color
    as a six-digit hex (``#rrggbb``); ``label`` is the field's accessible name.
    Editing the field to a valid hex repaints the swatch and publishes the color
    on ``topic``. ``listen`` names an optional topic the control follows: a valid
    hex published there updates the field and swatch in place, without
    republishing. Raises :class:`ValueError` at the authoring boundary if
    ``value`` is not a six-digit hex or ``label`` is blank, so a bad call fails
    where it is written, not at render or in the browser.
    """
    if not _HEX.match(value):
        msg = f"color_input value {value!r} is not a six-digit hex color (#rrggbb)"
        raise ValueError(msg)
    if not label:
        raise ValueError("color_input requires a non-empty label (the field's name)")
    swatch = element(
        "span",
        {
            "class": "sb-color-input-swatch",
            "aria-hidden": "true",
            # The live color as a per-instance value, not an inline paint
            # declaration: the theme paints `background: var(--sb-swatch)` from it,
            # so paint stays the theme's and only the value crosses the boundary.
            "style": f"--sb-swatch:{value}",
        },
    )
    initial = element(
        "div", {"class": "sb-color-input"}, [swatch, _hex_field(value, label)]
    )
    return Island(
        name="color-input",
        props=_control_props(topic, listen),
        publishes=(topic,),
        subscribes=(listen,) if listen else (),
        initial=initial,
    )


def color_input_scripts() -> tuple[str, ...]:
    """The color-input adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("color-input.js"),)


def color_input_styles() -> str:
    """The color-input structural CSS, for the host to inline in ``extra_head``."""
    return read_static("color-input.css")


# A valid element id, restricted to CSS-ident-safe characters: the id links the
# trigger to the panel via popovertarget and aria-controls, and the popover's id
# also becomes the tail of its per-instance anchor-name ident, so a character
# that is legal in an HTML id but not in a dashed-ident (a `:` or `.`) would
# silently break the anchor link. One validator holds both duties.
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")

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
    escapes ancestor clipping) and gives light-dismiss and Esc for free. The
    structural sheet anchors the panel to its trigger declaratively (CSS anchor
    positioning, linked through the per-instance anchor name the wrapper
    carries); the adapter adds focus management and an optional ``open_topic``
    bus echo of ``{"open": bool}``.

    ``trigger_class`` adds classes to the trigger button (e.g. to style it as a
    chip), and ``trigger_label`` gives the trigger its own accessible name — which
    a content-less chip trigger needs, and which lets ``trigger`` be empty. Raises
    :class:`ValueError` at the authoring boundary if ``label`` is blank,
    ``panel_id`` is not a valid id (letters, digits, hyphens, underscores),
    ``panel`` is empty, or ``trigger`` is empty without a ``trigger_label``.
    """
    if not label:
        raise ValueError("popover requires a non-empty label (the panel's name)")
    if not _ID.match(panel_id):
        raise ValueError(
            f"popover panel_id {panel_id!r} is not a valid id"
            " (letters, digits, hyphens, underscores)"
        )
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
    # The per-instance anchor name rides the wrapper as a custom-property value
    # (runtime data, like the swatch's --sb-swatch — a value, never a paint or
    # geometry declaration); trigger and panel inherit it, and the structural
    # sheet consumes it via anchor-name / position-anchor to link the two.
    initial = element(
        "div",
        {"class": "sb-popover", "style": f"--sb-anchor: --sb-anchor-{panel_id}"},
        [trigger_el, panel_el],
    )
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


def _picker_panel(label: str, value: str) -> str:
    """The picker's popover panel: a saturation/value area over a hue slider.

    Both surfaces are ``role="slider"`` so pointer and keyboard both drive them;
    their handle positions and spectrum gradients are the adapter's (the spectrum
    is functional data-viz set inline, the one sanctioned exception to the
    token-only rule). The hex field carries the precise value and is the
    accessible backbone; the spectrum is the visual affordance.

    The initial ARIA values are computed from ``value`` here, so the rendered
    markup is correct before the adapter mounts (never a placeholder the adapter
    must fix). The SV area is two-dimensional, but ``role="slider"`` requires a
    single ``aria-valuenow``: it carries brightness (the up/down keyboard axis),
    and ``aria-valuetext`` carries both readings in full.
    """
    hue_deg, saturation, brightness = _hsv(value)
    area = element(
        "div",
        {
            "class": "sb-color-picker-area",
            "role": "slider",
            "tabindex": "0",
            "aria-roledescription": "saturation and brightness",
            "aria-label": f"{label} saturation and brightness",
            "aria-valuemin": "0",
            "aria-valuemax": "100",
            "aria-valuenow": str(brightness),
            "aria-valuetext": f"{saturation}% saturation, {brightness}% brightness",
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
            "aria-valuenow": str(hue_deg),
            "aria-valuetext": f"{hue_deg} degrees",
        },
        [
            element(
                "span", {"class": "sb-color-picker-hue-thumb", "aria-hidden": "true"}
            )
        ],
    )
    return element("div", {"class": "sb-color-picker-controls"}, [area, hue])


def _hsv(hex_value: str) -> tuple[int, int, int]:
    """A six-digit hex color as rounded HSV readings: (degrees, %, %)."""
    r, g, b = (int(hex_value[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return round(h * 360), round(s * 100), round(v * 100)


def color_picker(
    *, topic: str, value: str, label: str, listen: str | None = None
) -> Island:
    """A visual color picker: a swatch that opens a spectrum popover, plus a hex field.

    Augments :func:`color_input`: the swatch becomes a popover trigger that
    reveals a saturation/value area and a hue slider; the inline hex field stays
    as the precise, fully-accessible control. The swatch, the spectrum, and the
    field stay in sync and all publish the chosen ``#rrggbb`` on ``topic``.
    ``value`` is the initial color (six-digit hex) and ``label`` names the
    control. ``listen`` names an optional topic the picker follows: a valid hex
    published there resyncs the swatch, spectrum, and field in place, without
    republishing. Raises :class:`ValueError` at the authoring boundary if
    ``value`` is not a six-digit hex or ``label`` is blank.
    """
    if not _HEX.match(value):
        msg = f"color_picker value {value!r} is not a six-digit hex color (#rrggbb)"
        raise ValueError(msg)
    if not label:
        raise ValueError("color_picker requires a non-empty label (the control's name)")
    panel_id = "sb-cp-" + re.sub(r"[^A-Za-z0-9_-]", "-", topic)
    trigger = popover(
        trigger="",
        panel=_picker_panel(label, value),
        label=label,
        panel_id=panel_id,
        trigger_class="sb-color-picker-swatch",
        trigger_label=label,
        # The live color as a per-instance --sb-swatch value (not inline paint);
        # the theme paints the swatch background from it.
        trigger_style=f"--sb-swatch:{value}",
    )
    initial = element(
        "div",
        {"class": "sb-color-picker"},
        [render_island(trigger), _hex_field(value, label)],
    )
    return Island(
        name="color-picker",
        props=_control_props(topic, listen),
        publishes=(topic,),
        subscribes=(listen,) if listen else (),
        initial=initial,
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
    listen: str | None = None,
) -> Island:
    """A slider: drag a numeric value in ``[min, max]``, publishing it on ``topic``.

    A native range, restyled to the house look. ``value`` is the initial value
    (in range), ``step`` the increment, ``label`` the control's accessible name;
    ``readout`` shows the live value beside the track. Dragging publishes the
    value as a number — an ``int`` when ``min``/``max``/``step``/``value`` are all
    whole, else a ``float`` (decided here and carried as the ``integer`` prop).
    ``listen`` names an optional topic the slider follows: a number published
    there moves the thumb and readout in place, without republishing. Raises
    :class:`ValueError` at the authoring boundary if ``min >= max``,
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
        props={**_control_props(topic, listen), "integer": integer},
        publishes=(topic,),
        subscribes=(listen,) if listen else (),
        initial=initial,
    )


def slider_scripts() -> tuple[str, ...]:
    """The slider adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("slider.js"),)


def slider_styles() -> str:
    """The slider structural CSS, for the host to inline in ``extra_head``."""
    return read_static("slider.css")


def value_field(
    *, topic: str, value: str, label: str, listen: str | None = None
) -> Island:
    """A labelled text field that publishes its value on ``topic``.

    The general single-line editor for a scheme-invariant token whose value is a
    CSS string: a length (``0.75rem``), a number (``400``), a font family, a
    shadow. ``value`` is the initial text, ``label`` the field's accessible name.
    Editing it publishes the raw string on ``topic`` — a :func:`theme_state`
    :class:`ValueBinding` writes that string straight onto the bound token, so the
    preview repaints. Unlike :func:`color_input` it validates nothing: any string
    is a candidate CSS value and the live preview is the feedback. ``listen``
    names an optional topic the field follows: a string published there replaces
    the field's text in place, without republishing. Raises :class:`ValueError`
    at the authoring boundary if ``label`` is blank.
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
        name="value-field",
        props=_control_props(topic, listen),
        publishes=(topic,),
        subscribes=(listen,) if listen else (),
        initial=initial,
    )


def value_field_scripts() -> tuple[str, ...]:
    """The value-field adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("value-field.js"),)


def value_field_styles() -> str:
    """The value-field structural CSS, for the host to inline in ``extra_head``."""
    return read_static("value-field.css")


def preview_items() -> tuple[str, ...]:
    """The preview sample's surfaces, each as a standalone html fragment.

    The same representative surfaces :func:`preview` renders together, exposed
    individually so a host can lay them out per item — the theme builder renders
    each item in a light cell and a dark cell side by side. Each fragment paints
    from the (scope-overridable) tokens, so it repaints when a token changes.
    """
    heading = element("p", {"class": "sb-preview-heading"}, [escape_text("Heading")])
    prose = element(
        "p",
        {"class": "sb-preview-prose"},
        [escape_text("Body text in the prose family, sized and colored by tokens.")],
    )
    button = element("button", {"type": "button"}, [escape_text("Primary")])
    # The accent fill is static theme paint (.sb-preview-swatch), not declared
    # inline: the swatch carries the hook, the theme owns the color.
    swatch = element(
        "span",
        {
            "class": "sb-preview-swatch",
            "aria-hidden": "true",
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
    callout = element(
        "p",
        {"class": "sb-preview-callout"},
        [escape_text("A callout on the accent's tinted surface.")],
    )
    diff = element(
        "pre",
        {"class": "sb-preview-diff"},
        [
            element(
                "code",
                {"class": "sb-preview-diff-del"},
                [escape_text("- padding: 12px")],
            ),
            escape_text("\n"),
            element(
                "code",
                {"class": "sb-preview-diff-add"},
                [escape_text("+ padding: var(--sb-space-inset)")],
            ),
        ],
    )
    return (heading, prose, button, swatch, table, callout, diff)


def _preview_sample() -> str:
    """A representative sample of surfaces, to exercise the token adjacencies live."""
    return element("div", {"class": "sb-preview-sample"}, list(preview_items()))


def preview(*, scope_id: str, scheme: Literal["light", "dark"] | None = None) -> Island:
    """A live preview surface: a sample of components that repaints as tokens change.

    Renders a representative sample inside a scope wrapper carrying ``scope_id``
    (as ``data-sb-scope``); a sibling :func:`theme_state` island writes token
    overrides onto that wrapper, and everything inside repaints because it reads
    ``var(--sb-*)``. ``scheme`` pins the pane to one color scheme (a side-by-side
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

    A scheme-varying token (a color) is authored per ``-light`` / ``-dark`` arm,
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
    Each is an :class:`ArmBinding` (one scheme arm of a color) or a
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


@dataclass(frozen=True)
class Cell:
    """A table cell carrying trusted, already-rendered inline HTML.

    A plain ``str`` cell is escaped (the structured-data default); a ``Cell`` is
    emitted verbatim, for a cell whose content is inline markup the caller has
    already rendered safely (a link, inline code). The same trust model as
    :attr:`Island.initial` and :func:`modal`'s ``body``: the caller owns escaping
    the leaf text, so composed fragments are not double-escaped.
    """

    html: str


def _table_cell(cell: str | Cell) -> str:
    """One body ``<td>``: a plain string is escaped, a :class:`Cell` is trusted."""
    content = escape_text(cell) if isinstance(cell, str) else cell.html
    return element("td", {}, [content])


def table(
    *, columns: Sequence[str], rows: Sequence[Sequence[str | Cell]], label: str
) -> Island:
    """A data table: a header row of ``columns`` over ``rows`` of cells.

    The canonical structured-data surface — a real ``<table>``, not a card grid.
    ``columns`` are the header labels (one per column), always escaped plain text;
    ``rows`` are the body rows, each a sequence whose length must equal the column
    count. A cell is a plain ``str`` (escaped) or a :class:`Cell` (trusted inline
    HTML, for a link or inline code the caller has already rendered). ``label`` is
    the table's accessible name (its ``aria-label``). The table fills its column
    and becomes its own horizontal scroll container when the content is wider, so a
    wide table never pushes the page (the scroll-containment contract). It is a
    static display surface — no adapter, so it is also a plain gallery specimen.
    Raises :class:`ValueError` at the authoring boundary if ``columns`` is empty,
    ``label`` is blank, or any row's cell count does not match the column count — so
    a ragged table fails where it is written, not at render or in the browser.
    """
    if not columns:
        raise ValueError("table requires at least one column")
    if not label:
        raise ValueError("table requires a non-empty label (the table's name)")
    width = len(columns)
    for index, row in enumerate(rows):
        if len(row) != width:
            msg = f"table row {index} has {len(row)} cells, expected {width}"
            raise ValueError(msg)
    header = element(
        "tr", {}, [element("th", {"scope": "col"}, [escape_text(c)]) for c in columns]
    )
    body = [element("tr", {}, [_table_cell(cell) for cell in row]) for row in rows]
    grid = element(
        "table",
        {"class": "sb-table-grid", "aria-label": label},
        [element("thead", {}, [header]), element("tbody", {}, body)],
    )
    return Island(name="table", initial=element("div", {"class": "sb-table"}, [grid]))


def table_styles() -> str:
    """The table structural CSS, for the host to inline in ``extra_head``."""
    return read_static("table.css")


@dataclass(frozen=True)
class FilterControl:
    """One labelled control in a filter bar: a name beside the control island.

    ``control`` is any publishing island — a :func:`value_field` for a typed
    query, a :func:`segmented` for a small set of choices. The filter table lays
    it out and subscribes to its topic; it never builds the control, so which one
    a bar carries stays the host's choice.
    """

    label: str
    control: Island


MatchMode = Literal["substring", "exact"]
"""How a published value is matched against a row's key: contained in it
(a typed query) or equal to it (a chosen category)."""

# The reserved sort values. A control publishing anything else leaves the order
# alone, so a sort control can carry an "unsorted" option under any label.
SORT_VALUES: tuple[str, ...] = ("none", "asc", "desc")
"""The values a sort control publishes: restore the server's order, or sort by
the sort key ascending or descending."""


def filter_table(
    *,
    columns: Sequence[str],
    rows: Sequence[Sequence[str | Cell]],
    label: str,
    topic: str,
    keys: Sequence[str],
    controls: Sequence[FilterControl],
    match: MatchMode = "substring",
    all_value: str = "",
    sort_topic: str = "",
    sort_keys: Sequence[str] = (),
) -> Island:
    """A :func:`table` that narrows and reorders as controls publish on the bus.

    The whole table is server-rendered and every row stays in the DOM: the
    adapter hides the misses and reorders in place, so the page is complete
    without JavaScript and no request is made to filter. ``columns``, ``rows``,
    and ``label`` are the table's, with the same meanings.

    ``controls`` are the labelled controls rendered in the bar above the grid,
    with the running count at its far edge. ``topic`` is the topic the filtering
    control publishes on and ``keys`` are the per-row match keys, one per row in
    row order (a key may hold more than the row displays — the tags a listing
    does not show, say — so a search reaches them). ``match`` picks containment
    (lowercased and trimmed on both sides) or equality, and ``all_value`` is the
    published value that restores every row: the empty string for a typed query,
    a sentinel like ``"all"`` for a chosen category.

    ``sort_topic`` names an optional second topic whose control publishes one of
    :data:`SORT_VALUES`; ``sort_keys`` are the per-row keys it orders by (dates,
    names), again one per row. Sorting and filtering compose: a row's hidden
    state and its position are independent.

    Raises :class:`ValueError` at the authoring boundary if ``topic`` is blank,
    ``controls`` is empty or any control's label is blank, ``keys`` does not have
    one entry per row, or ``sort_topic`` is given without a matching
    ``sort_keys`` (and the reverse) — so a misaligned table fails where it is
    written, not silently filtering the wrong rows in the browser.
    """
    if not topic:
        raise ValueError("filter_table requires a non-empty topic")
    if not controls:
        raise ValueError("filter_table requires at least one control")
    for index, control in enumerate(controls):
        if not control.label:
            raise ValueError(f"filter_table control {index} has a blank label")
    if len(keys) != len(rows):
        msg = f"filter_table has {len(keys)} keys for {len(rows)} rows"
        raise ValueError(msg)
    if sort_topic and len(sort_keys) != len(rows):
        msg = f"filter_table has {len(sort_keys)} sort keys for {len(rows)} rows"
        raise ValueError(msg)
    if sort_keys and not sort_topic:
        raise ValueError("filter_table sort_keys need a sort_topic to order by")
    groups = [
        element(
            "div",
            {"class": "sb-filter-group"},
            [
                element(
                    "span", {"class": "sb-filter-label"}, [escape_text(control.label)]
                ),
                render_island(control.control),
            ],
        )
        for control in controls
    ]
    # The count is a live region: filtering is a visual change with no focus
    # move, so the readout is how a screen reader learns the result size.
    readout = element(
        "span",
        {"class": "sb-filter-count", "role": "status", "aria-live": "polite"},
        (),
    )
    bar = element("div", {"class": "sb-filter-bar"}, [*groups, readout])
    grid = table(columns=columns, rows=rows, label=label)
    props: dict[str, Json] = {
        "topic": topic,
        "keys": list(keys),
        "match": match,
        "allValue": all_value,
    }
    if sort_topic:
        props["sortTopic"] = sort_topic
        props["sortKeys"] = list(sort_keys)
    return Island(
        name="filter-table",
        props=props,
        subscribes=(topic, sort_topic) if sort_topic else (topic,),
        class_="sb-filter-table",
        initial=bar + render_island(grid),
    )


def filter_table_scripts() -> tuple[str, ...]:
    """The filter-table adapter, for the host to pass to ``extra_scripts``. The
    controls in the bar bring their own (:func:`value_field_scripts`,
    :func:`segmented_scripts`), the way two wired islands each bring theirs."""
    return (read_static("filter-table.js"),)


def filter_table_styles() -> str:
    """The filter-table structural CSS. Pair with :func:`table_styles` (the grid
    inside is the table component's), the way the adapters are paired."""
    return read_static("filter-table.css")


def code_block(
    *, code: str, label: str, language: str | None = None, copy: bool = True
) -> Island:
    """A code block: preformatted source with an optional copy action.

    Renders ``code`` as escaped, preformatted text in a mono surface that scrolls
    horizontally for long lines (it never wraps and never pushes the page).
    ``label`` is the block's accessible name (the ``aria-label`` of the group).
    ``language`` shows a small language tag in the block's chrome strip; it is
    cosmetic — the block does no syntax highlighting. ``copy`` adds a button that
    copies the source to the clipboard (its adapter mirrors :func:`theme_export`).
    A block with neither a ``language`` nor ``copy`` carries no chrome strip at all.
    Raises :class:`ValueError` at the authoring boundary if ``code`` or ``label``
    is empty, so a bad call fails where it is written.
    """
    if not code:
        raise ValueError("code_block requires non-empty code")
    if not label:
        raise ValueError("code_block requires a non-empty label (the block's name)")
    children: list[str] = []
    if language is not None or copy:
        chrome = [
            element("span", {"class": "sb-code-lang"}, [escape_text(language or "")])
        ]
        if copy:
            button = element(
                "button",
                {"type": "button", "class": "sb-code-copy"},
                [escape_text("Copy")],
            )
            status = element(
                "span",
                {"class": "sb-code-status", "role": "status", "aria-live": "polite"},
                (),
            )
            chrome.append(
                element("div", {"class": "sb-code-actions"}, [button, status])
            )
        children.append(element("div", {"class": "sb-code-chrome"}, chrome))
    code_el = element("code", {"class": "sb-code-text"}, [escape_text(code)])
    children.append(element("div", {"class": "sb-code-pre"}, [code_el]))
    initial = element(
        "div", {"class": "sb-code", "role": "group", "aria-label": label}, children
    )
    return Island(name="code-block", initial=initial)


def code_block_scripts() -> tuple[str, ...]:
    """The code-block adapter (the copy action), for the host's ``extra_scripts``."""
    return (read_static("code-block.js"),)


def code_block_styles() -> str:
    """The code-block structural CSS, for the host to inline in ``extra_head``."""
    return read_static("code-block.css")


def modal(
    *,
    trigger: str,
    body: str,
    label: str,
    dialog_id: str,
    title: str | None = None,
    trigger_class: str = "",
    trigger_label: str | None = None,
    open_topic: str | None = None,
) -> Island:
    """A modal dialog: a trigger that opens a centered, focus-trapping ``<dialog>``.

    The modal sibling of :func:`popover`. ``trigger`` is the open button's content
    and ``body`` the dialog's content (both raw-HTML fragments); ``label`` is the
    dialog's accessible name and ``dialog_id`` links the trigger (``aria-controls``)
    to the dialog. ``title`` shows a visible heading beside the close button.
    Opening uses the native ``dialog.showModal()`` — so the browser supplies the
    top layer, the ``::backdrop`` scrim, the focus trap, Esc-to-close, and an inert
    background; the adapter only wires the open button, the close button, and an
    optional ``open_topic`` bus echo of ``{"open": bool}``. Dismissal is the close
    button or Esc, deliberately not a backdrop click, so a modal is not lost by an
    accidental outside click. ``trigger_class`` / ``trigger_label`` style or name a
    chip trigger, as in :func:`popover`. Raises :class:`ValueError` at the authoring
    boundary if ``label`` is blank, ``dialog_id`` is not a valid id (letters,
    digits, hyphens, underscores), ``body`` is empty, or ``trigger`` is empty
    without a ``trigger_label``.
    """
    if not label:
        raise ValueError("modal requires a non-empty label (the dialog's name)")
    if not _ID.match(dialog_id):
        raise ValueError(
            f"modal dialog_id {dialog_id!r} is not a valid id"
            " (letters, digits, hyphens, underscores)"
        )
    if not trigger and not trigger_label:
        raise ValueError("modal requires trigger content or a trigger_label")
    if not body:
        raise ValueError("modal requires body content")
    trigger_el = element(
        "button",
        {
            "class": classes("sb-modal-trigger", trigger_class),
            "type": "button",
            "aria-haspopup": "dialog",
            "aria-controls": dialog_id,
            "aria-expanded": "false",
            "aria-label": trigger_label,
        },
        [trigger],
    )
    header_children: list[str] = []
    if title is not None:
        header_children.append(
            element(
                "div",
                {"class": "sb-modal-title", "role": "heading", "aria-level": "2"},
                [escape_text(title)],
            )
        )
    header_children.append(
        element(
            "button",
            {"class": "sb-modal-close", "type": "button", "aria-label": "Close"},
            [chr(0xD7)],  # the close glyph (multiplication sign), ASCII-safe source
        )
    )
    header = element("div", {"class": "sb-modal-header"}, header_children)
    body_el = element("div", {"class": "sb-modal-body"}, [body])
    dialog = element(
        "dialog",
        {"class": "sb-modal-dialog", "id": dialog_id, "aria-label": label},
        [header, body_el],
    )
    initial = element("div", {"class": "sb-modal"}, [trigger_el, dialog])
    return Island(
        name="modal",
        props={"topic": open_topic} if open_topic else {},
        publishes=(open_topic,) if open_topic else (),
        initial=initial,
    )


def modal_scripts() -> tuple[str, ...]:
    """The modal adapter, for the host to pass to ``extra_scripts``."""
    return (read_static("modal.js"),)


def modal_styles() -> str:
    """The modal structural CSS, for the host to inline in ``extra_head``."""
    return read_static("modal.css")


# A breadcrumb separator (a slash), between crumbs and hidden from assistive tech;
# the theme colors it.
_BREADCRUMB_SEP = element(
    "span", {"class": "sb-breadcrumb-sep", "aria-hidden": "true"}, ["/"]
)


def breadcrumb(
    *, trail: Sequence[tuple[str, str]], current: str, label: str = "Breadcrumb"
) -> Island:
    """A breadcrumb trail: ``trail`` ancestor links ending at the ``current`` page.

    ``trail`` is an ordered sequence of ``(label, href)`` ancestor links (it may be
    empty when the current page is the root); ``current`` is the current page,
    rendered as the trailing non-link crumb carrying ``aria-current="page"``.
    ``label`` names the navigation landmark for assistive tech. Inert separators sit
    between crumbs. It is a static navigation surface — no adapter, the links
    navigate natively. Raises :class:`ValueError` at the authoring boundary if
    ``current`` or ``label`` is blank, or any trail crumb has a blank label or href —
    so a malformed trail fails where it is written.
    """
    if not current:
        raise ValueError("breadcrumb requires a non-empty current page")
    if not label:
        raise ValueError("breadcrumb requires a non-empty label (the nav's name)")
    crumbs: list[str] = []
    for index, (crumb_label, href) in enumerate(trail):
        if not crumb_label:
            raise ValueError(f"breadcrumb trail crumb {index} has a blank label")
        if not href:
            raise ValueError(f"breadcrumb trail crumb {index} has a blank href")
        if index:
            crumbs.append(_BREADCRUMB_SEP)
        crumbs.append(
            element(
                "a",
                {"class": "sb-breadcrumb-link", "href": href},
                [escape_text(crumb_label)],
            )
        )
    if trail:
        crumbs.append(_BREADCRUMB_SEP)
    crumbs.append(
        element(
            "span",
            {"class": "sb-breadcrumb-current", "aria-current": "page"},
            [escape_text(current)],
        )
    )
    initial = element("nav", {"class": "sb-breadcrumb", "aria-label": label}, crumbs)
    return Island(name="breadcrumb", initial=initial)


def breadcrumb_styles() -> str:
    """The breadcrumb structural CSS, for the host to inline in ``extra_head``."""
    return read_static("breadcrumb.css")


def collapsible(
    *, title: str, body: str, count: int | None = None, open: bool = False
) -> Island:
    """A collapsible section: a ``<details>`` whose summary is ``title`` and a count.

    The disclosure is native (``<details>`` / ``<summary>``), so toggling, keyboard
    operation, and the open/closed state come for free — no adapter. ``title`` is the
    summary's heading; ``body`` is the content revealed when expanded; ``count``
    shows a badge of how many items the section groups (omitted when ``None``);
    ``open`` starts it expanded. Raises :class:`ValueError` at the authoring boundary
    if ``title`` is blank, ``body`` is empty, or ``count`` is negative.
    """
    if not title:
        raise ValueError("collapsible requires a non-empty title")
    if not body:
        raise ValueError("collapsible requires body content")
    if count is not None and count < 0:
        raise ValueError(f"collapsible count must be non-negative, got {count}")
    label = element(
        "span",
        {"class": "sb-collapsible-label"},
        [
            element("span", {"class": "sb-collapsible-marker", "aria-hidden": "true"}),
            element("span", {"class": "sb-collapsible-title"}, [escape_text(title)]),
        ],
    )
    summary_children = [label]
    if count is not None:
        summary_children.append(
            element(
                "span", {"class": "sb-collapsible-count"}, [escape_text(str(count))]
            )
        )
    summary = element("summary", {"class": "sb-collapsible-summary"}, summary_children)
    body_el = element("div", {"class": "sb-collapsible-body"}, [body])
    initial = element(
        "details",
        {"class": "sb-collapsible", "open": "" if open else None},
        [summary, body_el],
    )
    return Island(name="collapsible", initial=initial)


def collapsible_styles() -> str:
    """The collapsible structural CSS, for the host to inline in ``extra_head``."""
    return read_static("collapsible.css")


@dataclass(frozen=True)
class NavItem:
    """One nav row: a label linking to a route, with optional children.

    ``current`` marks the row as the current page (``aria-current="page"``, the
    theme's reserved accent channel recolored). ``meta`` is an optional short
    annotation at the row's far edge (a count, a status); empty renders nothing.

    ``children`` are the items nested under this one, to any depth. Nesting is
    the shape of the value, exactly as it is for :class:`~switchboard_ui.Frame`:
    a child belongs to the item it is written inside, not to whichever row
    happened to precede it. Reordering rows therefore cannot silently reparent
    them, and a grandchild is expressible.
    """

    label: str
    href: str
    current: bool = False
    meta: str = ""
    children: tuple["NavItem", ...] = ()


@dataclass(frozen=True)
class NavSection:
    """A run of nav items under an optional group heading.

    ``heading`` is a structural label over the run (uppercase in the theme);
    empty renders the items with no heading, for a leading ungrouped run.
    """

    items: tuple[NavItem, ...]
    heading: str = ""


def _nav_contains_current(item: NavItem) -> bool:
    """Whether ``item`` or any descendant is the current page."""
    return item.current or any(_nav_contains_current(c) for c in item.children)


def _nav_current_count(sections: Sequence[NavSection]) -> int:
    """How many items in the whole tree are marked current."""

    def count(item: NavItem) -> int:
        return int(item.current) + sum(count(c) for c in item.children)

    return sum(count(item) for section in sections for item in section.items)


def nav(*, sections: Sequence[NavSection], label: str, scroll_key: str = "") -> Island:
    """A sidebar nav: sections of items to any depth, the current page marked.

    The canonical left-rail navigation — a static island (no adapter, no
    pub/sub): the links navigate natively, and no click is intercepted. Each
    section renders its optional group heading over a semantic ``<ul>``; each
    item is an ``<li>`` holding an ``<a>`` whose label sits at the row's start
    and whose optional ``meta`` annotation sits at the far edge. An item with
    children renders a nested ``<ul>`` inside its own ``<li>``, so the document
    outline matches the navigation hierarchy for assistive technology.

    The current item carries ``aria-current="page"``; every row reserves the
    active-edge channel (the theme draws it transparent and recolors the current
    one), so marking the current page never shifts a row. Each ancestor of the
    current item carries ``data-current-ancestor``, computed here rather than in
    the browser, so revealing the current path costs no script and no reflow.

    Every branch renders expanded. Disclosure is a later, separate concern, and
    an ancestor that opened or closed a branch would move the row the reader just
    clicked and every row after it.

    ``label`` is the nav's accessible name (its ``aria-label``).

    ``scroll_key`` opts the nav into remembering its scroll position across
    native page loads, for a rail that is shared chrome on every page. A forward
    navigation builds a new document and therefore a new element scroll
    container, which the browser starts at zero; the page's own position it
    restores correctly, but an element's is the application's to keep. When the
    key is non-empty the factory emits a tiny inline restoration script directly
    after the nav — inline because the position must be applied before this
    document's first paint, or the reader watches the rail snap — and the nav
    adapter saves the position as it changes. The key namespaces the value, so
    two navs on one site keep separate positions. Left empty, none of this is
    emitted and the nav is entirely static.

    Raises :class:`ValueError` if ``label`` is blank, ``sections`` is empty, any
    item has a blank label or href, or more than one item is marked current — so
    a malformed nav fails where it is written. Validation errors name the item by
    its path through the tree (``section 1 > item 0 > item 2``), which is stable
    under reordering and unambiguous across sections.
    """
    if not label:
        raise ValueError("nav requires a non-empty label (the nav's name)")
    if not sections:
        raise ValueError("nav requires at least one section")
    marked = _nav_current_count(sections)
    if marked > 1:
        raise ValueError(
            f"nav has {marked} items marked current; exactly one page is current"
        )

    def row(item: NavItem, path: str) -> str:
        if not item.label:
            raise ValueError(f"nav {path} has a blank label")
        if not item.href:
            raise ValueError(f"nav {path} has a blank href")
        parts = [element("span", {"class": "sb-nav-label"}, [escape_text(item.label)])]
        if item.meta:
            parts.append(
                element("span", {"class": "sb-nav-meta"}, [escape_text(item.meta)])
            )
        anchor = element(
            "a",
            {
                "class": "sb-nav-item",
                "href": item.href,
                "aria-current": "page" if item.current else "false",
            },
            parts,
        )
        contents = [anchor]
        if item.children:
            contents.append(
                element(
                    "ul",
                    {"class": "sb-nav-list sb-nav-sublist"},
                    [
                        row(child, f"{path} > item {i}")
                        for i, child in enumerate(item.children)
                    ],
                )
            )
        # The ancestor hook marks the path to the current page, never the page
        # itself: the item carries `aria-current` for that.
        ancestor = any(_nav_contains_current(c) for c in item.children)
        return element(
            "li",
            {
                "class": "sb-nav-node",
                "data-current-ancestor": "" if ancestor else None,
            },
            contents,
        )

    blocks: list[str] = []
    for section_index, section in enumerate(sections):
        if section.heading:
            blocks.append(
                element(
                    "div",
                    {"class": "sb-nav-group"},
                    [escape_text(section.heading)],
                )
            )
        blocks.append(
            element(
                "ul",
                {"class": "sb-nav-list"},
                [
                    row(item, f"section {section_index} > item {i}")
                    for i, item in enumerate(section.items)
                ],
            )
        )
    initial = element("nav", {"class": "sb-nav", "aria-label": label}, blocks)
    if scroll_key:
        # Before the nav, not after it and not at the end of <body>. A document
        # arrives in chunks, so a script placed after the markup can be reached
        # only once the browser has already painted the finished rail at the top.
        # Starting before it means the rail is never painted complete-and-wrong.
        initial = (
            element(
                "script",
                {"data-scroll-key": scroll_key},
                [read_static("nav-restore.js")],
            )
            + initial
        )
    return Island(
        name="nav",
        props={"scrollKey": scroll_key} if scroll_key else {},
        initial=initial,
    )


def nav_styles() -> str:
    """The nav structural CSS, for the host to inline in ``extra_head``."""
    return read_static("nav.css")


def nav_scripts() -> tuple[str, ...]:
    """The nav adapter (rail scroll persistence), for the host's ``extra_scripts``.

    Only needed by a nav built with a ``scroll_key``; a nav without one carries
    no props, so the adapter mounts and returns immediately. The restoring half
    is not here — it ships inline with the nav markup, because it has to run
    before first paint.
    """
    return (read_static("nav.js"),)


def masthead(*, name: str, href: str = "/") -> Island:
    """The head rail's brand: the site's name linking home.

    The one piece of chrome every page carries in the same place — a static
    island (no adapter, no pub/sub): the link navigates natively. ``name`` is the
    site's name (the visible text) and ``href`` the route it links to. Raises
    :class:`ValueError` at the authoring boundary if either is blank.
    """
    if not name:
        raise ValueError("masthead requires a non-empty name (the site's name)")
    if not href:
        raise ValueError("masthead requires a non-empty href")
    brand = element("a", {"class": "sb-masthead", "href": href}, [escape_text(name)])
    return Island(name="masthead", initial=brand)


def masthead_styles() -> str:
    """The masthead structural CSS, for the host to inline in ``extra_head``."""
    return read_static("masthead.css")


def section_heading(*, title: str, meta: str = "", anchor: str = "") -> Island:
    """A section's heading row: its title beside an optional meta at the far edge.

    The underlined row that opens a content section — a static island. ``title``
    is the heading text (an ``h2``); ``meta`` is a short annotation pinned to the
    row's far edge (a count, a total), omitted when blank; ``anchor`` gives the
    row an ``id`` so an on-this-page rail can link to it. Raises
    :class:`ValueError` at the authoring boundary if ``title`` is blank or
    ``anchor`` is not a valid id (letters, digits, hyphens, underscores).
    """
    if not title:
        raise ValueError("section_heading requires a non-empty title")
    if anchor and not _ID.match(anchor):
        raise ValueError(
            f"section_heading anchor {anchor!r} is not a valid id"
            " (letters, digits, hyphens, underscores)"
        )
    children = [element("h2", {"class": "sb-section-title"}, [escape_text(title)])]
    if meta:
        children.append(
            element("span", {"class": "sb-section-meta"}, [escape_text(meta)])
        )
    initial = element(
        "div", {"class": "sb-section-heading", "id": anchor or None}, children
    )
    return Island(name="section-heading", initial=initial)


def section(*, title: str, body: str, meta: str = "", anchor: str = "") -> Island:
    """A titled content section: a :func:`section_heading` over its body.

    The page's unit of structure — a heading row and the content under it, in one
    column with a single rhythm between them, separated from its neighbours by
    the heading's rule rather than by a box. ``body`` is a raw-HTML fragment (a
    rendered island, a table, prose); ``title``, ``meta``, and ``anchor`` are the
    heading's, with the same meanings. Raises :class:`ValueError` at the authoring
    boundary if ``title`` is blank, ``body`` is empty, or ``anchor`` is not a
    valid id.
    """
    if not body:
        raise ValueError("section requires body content")
    heading = section_heading(title=title, meta=meta, anchor=anchor)
    return Island(
        name="section",
        class_="sb-section",
        initial=render_island(heading) + body,
    )


def section_styles() -> str:
    """The section structural CSS (the container and its heading row), for the
    host to inline in ``extra_head``. One sheet covers :func:`section` and
    :func:`section_heading`: a heading is the section's own first row."""
    return read_static("section.css")


def hero(*, title: str, description: str = "", eyebrow: str = "") -> Island:
    """A page's display heading: an optional eyebrow, the title, a description.

    The opening block of a landing or detail page — a static island. ``title`` is
    the page's name, set in the display type; ``description`` is the lead
    paragraph under it (the prose lead surface, capped at the reading measure),
    omitted when blank; ``eyebrow`` is a short structural label above the title (a
    category, a breadcrumb-like context), also omitted when blank. Raises
    :class:`ValueError` at the authoring boundary if ``title`` is blank.
    """
    if not title:
        raise ValueError("hero requires a non-empty title")
    parts = [
        element("div", {"class": "sb-hero-eyebrow"}, [escape_text(eyebrow)])
        if eyebrow
        else "",
        element("h1", {"class": "sb-hero-title"}, [escape_text(title)]),
        prose_lead(description) if description else "",
    ]
    initial = element("header", {"class": "sb-hero"}, [part for part in parts if part])
    return Island(name="hero", initial=initial)


def hero_styles() -> str:
    """The hero structural CSS, for the host to inline in ``extra_head``."""
    return read_static("hero.css")


def prose(*, html: str) -> Island:
    """A prose surface: rendered markup the theme paints as running text.

    The host's markdown renderer produces the markup; this wraps it in the one
    hook the theme paints — headings, measure-capped paragraphs, lists, code,
    tables, blockquotes, and links — so every page's prose reads the same without
    each host restating the rules. ``html`` is the rendered fragment, trusted raw
    HTML (the same trust model as :attr:`Island.initial`). Raises
    :class:`ValueError` at the authoring boundary if ``html`` is empty.
    """
    if not html:
        raise ValueError("prose requires rendered content")
    return Island(name="prose", initial=element("div", {"class": "sb-prose"}, [html]))


def prose_lead(text: str) -> str:
    """A lead paragraph as an HTML fragment: muted prose at the reading measure.

    The standalone form of what :func:`hero` sets under its title — a section's
    or a page's opening sentence. A fragment rather than an island because a lead
    is one line inside a larger composition (a hero, a section's heading run),
    never a mount point of its own. ``text`` is plain text and is escaped.
    """
    return element("p", {"class": "sb-prose-lead"}, [escape_text(text)])


def prose_styles() -> str:
    """The prose structural CSS, for the host to inline in ``extra_head``."""
    return read_static("prose.css")


@dataclass(frozen=True)
class TocEntry:
    """One on-this-page row: heading text linking to its in-page anchor.

    ``nested`` places the entry in an indented sublist under the preceding
    top-level entry (an h3 under its h2).
    """

    text: str
    anchor: str
    nested: bool = False


def toc(*, entries: Sequence[TocEntry], label: str = "On this page") -> Island:
    """An on-this-page rail: a page's headings as in-page anchor links.

    The structural twin of an inspector column — a static island: each link is
    an in-page anchor (``#<anchor>``) the scroll owner follows natively. A run
    of ``nested`` entries is grouped into a sublist that owns the nesting indent
    structurally, so the links themselves keep a square inset. ``label`` is the
    rail's heading and accessible name. An empty ``entries`` renders just the
    label (a page with no headings keeps its rail without inventing links).
    Raises :class:`ValueError` if ``label`` is blank, or any entry has blank
    text or a blank anchor.
    """
    if not label:
        raise ValueError("toc requires a non-empty label (the rail's name)")

    def link(entry: TocEntry, index: int) -> str:
        if not entry.text:
            raise ValueError(f"toc entry {index} has blank text")
        if not entry.anchor:
            raise ValueError(f"toc entry {index} has a blank anchor")
        cls = "sb-toc-link sb-toc-link-nested" if entry.nested else "sb-toc-link"
        return element(
            "a",
            {"class": cls, "href": f"#{entry.anchor}"},
            [escape_text(entry.text)],
        )

    rows: list[str] = []
    sublist: list[str] = []

    def flush_sublist() -> None:
        if sublist:
            rows.append(element("div", {"class": "sb-toc-sublist"}, list(sublist)))
            sublist.clear()

    for index, entry in enumerate(entries):
        if entry.nested:
            sublist.append(link(entry, index))
        else:
            flush_sublist()
            rows.append(link(entry, index))
    flush_sublist()

    children = [
        element("div", {"class": "sb-toc-label"}, [escape_text(label)]),
        element("div", {"class": "sb-toc-links"}, rows),
    ]
    initial = element("nav", {"class": "sb-toc", "aria-label": label}, children)
    return Island(name="toc", initial=initial)


def toc_styles() -> str:
    """The toc structural CSS, for the host to inline in ``extra_head``."""
    return read_static("toc.css")
