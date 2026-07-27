"""The mode switch: host-ready islands for the theme's two shipped mode axes.

The theme ships two mode axes — color scheme (``auto`` follows the OS;
``light`` / ``dark`` pin one arm) and density (``comfortable`` is the registry
default; ``compact`` / ``spacious`` are the reassignment modes) — read from
``data-scheme`` / ``data-density`` on the root. This module ships the standard
control surface for them, so a host places it rather than inventing its own:

- :func:`mode_switch` — a quiet ``Modes`` trigger in the head rail opening an
  anchored popover holding one segmented toggle per axis. A popover rather than
  inline toggles: the presets' head-r cell shares its fixed width
  with the inspector column below (the columns of all three rows align), and six
  labelled options do not fit it; the panel renders in the top layer, so the set
  can grow without widening any rail.
- :func:`mode_state` — one invisible applier island that subscribes both
  toggles, stamps the chosen values on the root (where the theme's pinning and
  density rules read them), and persists the choice in localStorage —
  persistence is this island's own concern, the bus stays ephemeral. On boot the
  applier publishes the persisted values on sync topics the toggles listen to,
  so the controls match a restored state without republishing.
- :func:`mode_stamp_head` — a tiny head script that stamps the persisted
  attributes before first paint, so a pinned scheme never flashes the OS scheme
  first.

Each part rides the standard host seams: the islands are placed in the layout,
the adapter travels ``extra_scripts``, and the stamp and chrome CSS travel
``extra_head`` — the same opt-in every component asks of a host.
"""

from switchboard_ui import Island, render_island
from switchboard_ui.components import popover, segmented
from switchboard_ui.html import element, escape_text

# The mode axes' bus wiring. Each toggle publishes user input on its ``:changed``
# topic; the applier publishes restored state on the ``:sync`` topic the toggle
# listens to (synced state, not input, so there is no echo).
SCHEME_TOPIC = "scheme:changed"
DENSITY_TOPIC = "density:changed"
_SCHEME_SYNC = "scheme:sync"
_DENSITY_SYNC = "density:sync"


def mode_switch() -> Island:
    """The modes control for the head rail: a quiet ``Modes`` trigger opening an
    anchored panel with one toggle per mode axis.

    The toggles cover the theme's two shipped mode axes: the color scheme
    (``auto`` follows the OS; ``light`` / ``dark`` pin one arm) and the density
    mode (``comfortable`` is the registry default; ``compact`` / ``spacious``
    are the reassignment modes). Each publishes on its topic and follows its
    sync topic, so the applier can restore a persisted choice into the control
    without republishing. The toggles are ordinary islands nested in the panel's
    HTML; the runtime mounts them wherever they appear.
    """
    scheme = segmented(
        topic=SCHEME_TOPIC,
        options=(("light", "Light"), ("dark", "Dark"), ("auto", "Auto")),
        value="auto",
        label="Color scheme",
        listen=_SCHEME_SYNC,
    )
    density = segmented(
        topic=DENSITY_TOPIC,
        options=(
            ("compact", "Compact"),
            ("comfortable", "Comfortable"),
            ("spacious", "Spacious"),
        ),
        value="comfortable",
        label="Density",
        listen=_DENSITY_SYNC,
    )
    panel = element(
        "div",
        {"class": "sb-modes-panel"},
        [
            element("div", {"class": "sb-modes-group"}, [escape_text("Scheme")]),
            render_island(scheme),
            element("div", {"class": "sb-modes-group"}, [escape_text("Density")]),
            render_island(density),
        ],
    )
    return popover(
        trigger=escape_text("Modes"),
        panel=panel,
        label="Modes",
        panel_id="sb-modes",
        trigger_class="sb-modes-trigger",
    )


def mode_state() -> Island:
    """The invisible applier island: apply and persist the chosen modes.

    Subscribes both toggles' topics, stamps the chosen value onto the root's
    ``data-scheme`` / ``data-density`` (where the theme's scheme-pinning and
    density rules read them; a default value removes the attribute), and persists
    the choice in localStorage. On boot it publishes the persisted values on the
    sync topics, so the server-rendered toggles move to the restored state.
    Place it *after* the toggles in document order: the runtime mounts islands in
    that order, and a sync published before the toggles subscribe is lost (the
    bus is ephemeral, holding no last value for late subscribers).
    """
    return Island(
        name="mode-state",
        publishes=(_SCHEME_SYNC, _DENSITY_SYNC),
        subscribes=(SCHEME_TOPIC, DENSITY_TOPIC),
    )


# The applier: one axis table (attribute, storage key, default, allowed values,
# topics), boot-time restore + sync, and one subscriber per axis. The attribute
# names it touches are its own constants, never published values it did not
# validate, so a bus value can only ever become one of the named modes. Storage
# access is wrapped: a blocked localStorage degrades to per-page state.
_MODE_STATE_JS = """
window.switchboard.register("mode-state", function (el, props, bus) {
  var root = document.documentElement;
  var axes = [
    {
      attr: "scheme",
      key: "sb-scheme",
      fallback: "auto",
      modes: ["light", "dark"],
      changed: "scheme:changed",
      sync: "scheme:sync",
    },
    {
      attr: "density",
      key: "sb-density",
      fallback: "comfortable",
      modes: ["compact", "spacious"],
      changed: "density:changed",
      sync: "density:sync",
    },
  ];

  function read(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function write(key, value) {
    try {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    } catch (e) {}
  }

  function apply(axis, value) {
    if (axis.modes.indexOf(value) !== -1) {
      root.dataset[axis.attr] = value;
      write(axis.key, value);
    } else {
      delete root.dataset[axis.attr];
      write(axis.key, null);
    }
  }

  var offs = axes.map(function (axis) {
    var stored = read(axis.key);
    var value = axis.modes.indexOf(stored) !== -1 ? stored : axis.fallback;
    apply(axis, value);
    bus.publish(axis.sync, value);
    return bus.subscribe(axis.changed, function (next) {
      if (typeof next !== "string") return;
      apply(axis, next);
    });
  });

  return function teardown() {
    offs.forEach(function (off) {
      off();
    });
  };
});
"""


def mode_switch_scripts() -> tuple[str, ...]:
    """The applier adapter, for ``extra_scripts`` (the toggles use ``segmented``)."""
    return (_MODE_STATE_JS,)


# Stamps the persisted modes on the root before first paint, so a pinned scheme
# or density never flashes the default first. Validation matches the applier's:
# only the named modes are ever written. The applier re-derives the same state at
# boot; this script exists only to move the stamp ahead of paint.
_MODE_STAMP = """\
<script>
(function () {
  var data = document.documentElement.dataset;
  try {
    var scheme = localStorage.getItem("sb-scheme");
    if (scheme === "light" || scheme === "dark") data.scheme = scheme;
    var density = localStorage.getItem("sb-density");
    if (density === "compact" || density === "spacious") data.density = density;
  } catch (e) {}
})();
</script>"""


def mode_stamp_head() -> str:
    """The pre-paint mode stamp, for a host to place in ``extra_head``."""
    return _MODE_STAMP


# The mode switch's chrome (reading the theme's own --sb-* tokens). The head-r
# cell becomes a right-aligned row for the trigger, insetting itself as head-rail
# chrome does at the rail's other end. The trigger is a quiet text control, not
# an accent button (the class beats the theme's base `button` paint by
# specificity, the same override the theme's own quiet actions use), with a
# reserved-underline channel recolored while the panel is open. The panel is a
# column of labelled groups; the group labels are structural labels (uppercase,
# wide-tracked, small) over standalone toggles.
_MODE_CSS = """
.sb-head-r {
  flex-direction: row;
  align-items: center;
  justify-content: flex-end;
  padding: var(--sb-space-md);
}
.sb-modes-trigger {
  font: inherit;
  font-weight: var(--sb-font-weight-bold);
  min-width: 0;
  color: var(--sb-color-muted);
  background: none;
  border: none;
  border-block-end: var(--sb-border-width-accent) solid transparent;
  padding: 0;
  cursor: pointer;
}
.sb-modes-trigger:hover {
  color: var(--sb-color-fg);
}
.sb-modes-trigger[aria-expanded="true"] {
  color: var(--sb-color-accent);
  border-block-end-color: var(--sb-color-accent);
}
.sb-modes-trigger:focus-visible {
  outline: var(--sb-border-width-accent) solid var(--sb-color-accent);
  outline-offset: 2px;
}
.sb-modes-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sb-space-sm);
  padding: var(--sb-space-md);
}
.sb-modes-group {
  color: var(--sb-color-faint);
  font-size: var(--sb-font-size-sm);
  text-transform: uppercase;
  letter-spacing: var(--sb-font-tracking-wide);
}
"""


def mode_switch_styles() -> str:
    """The mode switch's chrome CSS, for a host to inline in ``extra_head``."""
    return f"<style>{_MODE_CSS}</style>"
