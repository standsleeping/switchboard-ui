/* Popover adapter: a native [popover] disclosure, anchored to its trigger.
 *
 * The trigger and panel are server-rendered; the trigger's `popovertarget` wires
 * open/close natively (and `popover="auto"` gives light-dismiss + Esc for free),
 * so the control works before this adapter mounts. The adapter only ENHANCES: it
 * reacts to the panel's `toggle` event to (1) keep the trigger's aria-expanded in
 * sync, (2) position the panel under the trigger (inline styles — runtime data,
 * the only place positioning lives), (3) move focus into the panel on open and
 * restore it to the trigger on close, and (4) echo open/close on the bus. It
 * never builds or resizes the panel. The panel renders in the top layer, so it
 * is never clipped by the frame's overflow. */
window.switchboard.register("popover", function (el, props, bus) {
  var topic = props.topic || null;
  var trigger = el.querySelector(".sb-popover-trigger");
  var panel = el.querySelector(".sb-popover-panel");

  function position() {
    var r = trigger.getBoundingClientRect();
    // Reset the UA popover centring (inset:0; margin:auto) and place by hand.
    panel.style.position = "fixed";
    panel.style.margin = "0";
    panel.style.inset = "auto";
    var pw = panel.offsetWidth;
    var ph = panel.offsetHeight;
    var vw = document.documentElement.clientWidth;
    var vh = document.documentElement.clientHeight;
    var top = r.bottom;
    if (top + ph > vh && r.top - ph >= 0) top = r.top - ph; // flip above
    var left = r.left;
    if (left + pw > vw) left = Math.max(0, vw - pw); // clamp to the right edge
    panel.style.top = Math.max(0, top) + "px";
    panel.style.left = Math.max(0, left) + "px";
  }

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
      position();
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

  function onResize() {
    if (panel.matches(":popover-open")) position();
  }

  panel.addEventListener("toggle", onToggle);
  window.addEventListener("resize", onResize);

  return function teardown() {
    panel.removeEventListener("toggle", onToggle);
    window.removeEventListener("resize", onResize);
    if (panel.matches(":popover-open")) panel.hidePopover();
  };
});
