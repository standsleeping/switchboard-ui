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
 * is never clipped by the frame's overflow.
 *
 * Positioning is the runtime's one imperative geometry computation: CSS cannot
 * yet anchor a top-layer panel to its trigger in every target browser (CSS
 * anchor positioning is the declarative replacement; this hand placement stands
 * in until it is supported everywhere the toolkit runs). Hand placement means
 * the written position is derived state that goes stale, so the adapter must
 * subscribe to everything that can invalidate it. The ledger:
 *
 *   open                  -> position() on the panel's "toggle" event
 *   viewport resize       -> window "resize" listener
 *   panel growth in place -> ResizeObserver on the panel (a density switch
 *                            reprojects the controls inside it)
 *   trigger scrolled away -> capture-phase window "scroll" listener (scroll
 *                            does not bubble, but capture sees every scroll
 *                            container's events)
 *   trigger moved by pure reflow, nothing above firing (a sibling insertion
 *   that shifts the trigger without scrolling or resizing anything)
 *                         -> NOT covered; accepted residue. Reposition-on-open
 *                            bounds the error to one open panel's lifetime.
 *
 * A new way the trigger or panel can move gets a row here: either the
 * subscription that covers it, or an explicit entry under accepted residue. */
window.switchboard.register("popover", function (el, props, bus) {
  var topic = props.topic || null;
  var trigger = el.querySelector(".sb-popover-trigger");
  var panel = el.querySelector(".sb-popover-panel");

  // Clearance between the panel and the viewport edge, so a clamped panel never
  // sits flush against it (a flush edge hides the panel's own border and reads
  // as truncation). A structural constant of the positioning logic, like the
  // flip threshold — not paint.
  var GUTTER = 8;

  function position() {
    var r = trigger.getBoundingClientRect();
    // Reset the UA popover centering (inset:0; margin:auto) and place by hand.
    panel.style.position = "fixed";
    panel.style.margin = "0";
    panel.style.inset = "auto";
    var pw = panel.offsetWidth;
    var ph = panel.offsetHeight;
    var vw = document.documentElement.clientWidth;
    var vh = document.documentElement.clientHeight;
    var top = r.bottom;
    if (top + ph > vh - GUTTER && r.top - ph >= GUTTER) top = r.top - ph; // flip above
    var left = r.left;
    if (left + pw > vw - GUTTER) left = Math.max(GUTTER, vw - GUTTER - pw); // clamp
    panel.style.top = Math.max(GUTTER, top) + "px";
    panel.style.left = Math.max(GUTTER, left) + "px";
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
  // Capture-phase, so a scroll inside any ancestor scroll container (not just
  // the window) re-anchors the panel to wherever its trigger moved.
  window.addEventListener("scroll", onResize, true);

  // Reposition when the open panel itself changes size: its content can grow
  // under it (a density switch reprojects every control), and a panel placed
  // for its old size would extend past the viewport clamp.
  var observer = new ResizeObserver(onResize);
  observer.observe(panel);

  return function teardown() {
    panel.removeEventListener("toggle", onToggle);
    window.removeEventListener("resize", onResize);
    window.removeEventListener("scroll", onResize, true);
    observer.disconnect();
    if (panel.matches(":popover-open")) panel.hidePopover();
  };
});
