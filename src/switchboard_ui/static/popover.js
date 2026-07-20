/* Popover adapter: behavior for a native [popover] disclosure.
 *
 * The trigger and panel are server-rendered; the trigger's `popovertarget` wires
 * open/close natively (and `popover="auto"` gives light-dismiss + Esc for free),
 * so the control works before this adapter mounts. Placement is not this
 * adapter's concern: the structural sheet anchors the panel to its trigger with
 * CSS anchor positioning, and the engine keeps the position current through
 * scroll, viewport resize, and panel growth (popover.css holds that contract).
 * The adapter only ENHANCES behavior: it reacts to the panel's `toggle` event to
 * (1) keep the trigger's aria-expanded in sync, (2) move focus into the panel on
 * open and restore it to the trigger on close, and (3) echo open/close on the
 * bus. It never builds, positions, or resizes the panel. */
window.switchboard.register("popover", function (el, props, bus) {
  var topic = props.topic || null;
  var trigger = el.querySelector(".sb-popover-trigger");
  var panel = el.querySelector(".sb-popover-panel");

  function firstFocusable() {
    return (
      panel.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) || panel
    );
  }

  function onToggle(e) {
    var open = e.newState === "open";
    trigger.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      firstFocusable().focus();
    } else if (
      panel.contains(document.activeElement) ||
      document.activeElement === document.body
    ) {
      // Closed via Esc or the trigger (focus was inside or fell to body): bring
      // focus back to the trigger. If the user clicked another control, leave it.
      trigger.focus();
    }
    if (topic) bus.publish(topic, { open: open });
  }

  panel.addEventListener("toggle", onToggle);

  return function teardown() {
    panel.removeEventListener("toggle", onToggle);
    if (panel.matches(":popover-open")) panel.hidePopover();
  };
});
