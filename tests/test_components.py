"""The segmented toggle factory, and the geometry-only contract for component CSS.

Two concerns. First, :func:`segmented` builds a correct mount descriptor: the
adapter name, the published topic, and an ``initial`` that is a complete,
accessible radio group at first paint — every option a server-rendered
``role="radio"``, exactly the chosen one checked, the checked one the single tab
stop (roving ``tabindex``), the group named for assistive tech, inert separators
between. Second, a component's structural CSS obeys the same contract as
``layout.css`` — geometry only, no box-spacing, no tokens but ``--sb-fit-*``, and
only ``.sb-*`` selectors — so paint never creeps into the structural layer. The
guard reuses the ``test_layout_css`` helpers and runs over every component sheet,
so a new component is covered the moment its CSS file lands.
"""

import re
from importlib.resources import files

import pytest

from switchboard_ui.components import segmented, segmented_scripts, segmented_styles
from switchboard_ui.model import Island
from tests.htmlprobe import find
from tests.test_layout_css import _LAYOUT_PROPERTIES, _declared_properties, _selectors

_OPTIONS = (("overview", "Overview"), ("api", "API"), ("examples", "Examples"))
_LABEL = "View"


def _make(value: str = "overview") -> Island:
    """A segmented island over the standard options, selecting ``value``."""
    return segmented(topic="view:changed", options=_OPTIONS, value=value, label=_LABEL)


def test_segmented_builds_a_segmented_island() -> None:
    """The factory names the segmented adapter and publishes the chosen topic."""
    island = _make()
    assert isinstance(island, Island)
    assert island.name == "segmented"
    assert island.publishes == ("view:changed",)
    assert island.props == {"topic": "view:changed"}


def test_segmented_is_a_named_radio_group() -> None:
    """The control is a radio group with an accessible name and radio options."""
    island = _make()
    (group,) = find(island.initial, "div", role="radiogroup")
    assert group["aria-label"] == _LABEL
    radios = find(island.initial, "button", role="radio")
    assert [r["data-value"] for r in radios] == ["overview", "api", "examples"]


def test_segmented_server_renders_every_option_label() -> None:
    """Each option's visible label is present at first paint."""
    island = _make()
    assert "Overview" in island.initial
    assert "API" in island.initial
    assert "Examples" in island.initial


def test_segmented_checks_only_the_chosen_option() -> None:
    """Exactly the option whose value is ``value`` carries aria-checked=true."""
    island = _make(value="api")
    checked = [
        r["data-value"]
        for r in find(island.initial, "button", role="radio")
        if r.get("aria-checked") == "true"
    ]
    assert checked == ["api"]


def test_segmented_makes_the_checked_option_the_only_tab_stop() -> None:
    """Roving tabindex: the checked option is focusable, the rest arrow-only."""
    radios = find(_make(value="api").initial, "button", role="radio")
    tabindex = {r["data-value"]: r["tabindex"] for r in radios}
    assert tabindex == {"overview": "-1", "api": "0", "examples": "-1"}


def test_segmented_separates_options() -> None:
    """Inert dot separators sit between options, one fewer than the options."""
    separators = find(_make().initial, "span", **{"class": "sb-segmented-sep"})
    assert len(separators) == len(_OPTIONS) - 1
    assert all(s.get("aria-hidden") == "true" for s in separators)


def test_segmented_rejects_empty_options() -> None:
    """An empty option set fails at the authoring boundary, not at render."""
    with pytest.raises(ValueError, match="at least one option"):
        segmented(topic="view:changed", options=(), value="overview", label=_LABEL)


def test_segmented_rejects_blank_label() -> None:
    """A radio group needs a name; a blank label fails where the call is written."""
    with pytest.raises(ValueError, match="non-empty label"):
        segmented(topic="view:changed", options=_OPTIONS, value="overview", label="")


def test_segmented_rejects_value_outside_options() -> None:
    """A selected value absent from the options fails where the call is written."""
    with pytest.raises(ValueError, match="not among options"):
        segmented(
            topic="view:changed", options=_OPTIONS, value="settings", label=_LABEL
        )


def test_segmented_scripts_returns_the_keyboard_radio_adapter() -> None:
    """The adapter ships, registers under the segmented name, and navigates by arrow key."""
    (adapter,) = segmented_scripts()
    assert 'register("segmented"' in adapter
    assert "ArrowRight" in adapter
    assert "aria-checked" in adapter


def test_segmented_styles_returns_the_structural_css() -> None:
    """The structural CSS ships and targets the component's hooks."""
    assert ".sb-segmented" in segmented_styles()


def _component_sheets() -> list[tuple[str, str]]:
    """``(name, css)`` for every component's structural CSS (not ``layout.css``)."""
    static = files("switchboard_ui") / "static"
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in static.iterdir()
        if path.name.endswith(".css") and path.name != "layout.css"
    ]


def test_component_css_declares_only_geometry() -> None:
    """A component sheet declares only layout properties — no paint, no box-spacing."""
    for name, css in _component_sheets():
        non_layout = _declared_properties(css) - _LAYOUT_PROPERTIES
        assert not non_layout, (
            f"{name} declares non-layout properties: {sorted(non_layout)}"
        )


def test_component_css_selects_only_sb_classes() -> None:
    """A component sheet styles only its own ``.sb-*`` hooks, never host elements."""
    for name, css in _component_sheets():
        foreign = [s for s in _selectors(css) if not s.startswith(".sb-")]
        assert not foreign, f"{name} selects non-sb elements: {foreign}"


def test_component_css_carries_no_paint_tokens_or_magic_numbers() -> None:
    """A component sheet stays token-free (only ``--sb-fit-*``) with no bare length."""
    for name, css in _component_sheets():
        body = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        assert "light-dark(" not in body, (
            f"{name} consumes theming (a cause, not structure)"
        )
        tokens = re.findall(r"var\(\s*(--[\w-]+)", body)
        non_contract = sorted({t for t in tokens if not t.startswith("--sb-fit-")})
        assert not non_contract, f"{name} references non-contract tokens {non_contract}"
        stripped = re.sub(r"var\([^)]*\)", "", body)
        bodies = " ".join(re.findall(r"\{([^{}]*)\}", stripped))
        lengths = re.findall(r"(\d*\.?\d+)(px|rem|em|cm|mm|pt|pc|in)\b", bodies)
        magic = sorted({f"{n}{unit}" for n, unit in lengths if float(n) != 0})
        assert not magic, (
            f"{name} has bare absolute lengths {magic}; use a token or keyword"
        )
