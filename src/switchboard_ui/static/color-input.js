/* Color input adapter: a swatch plus a hex field that publishes the color.
 *
 * The swatch and field are server-rendered (present and sized at first paint);
 * this adapter only enhances the field. On every edit it validates the hex; a
 * valid value repaints the swatch by writing the per-instance --sb-swatch value
 * the theme paints `background` from (a value, not a theme token, and never an
 * inline paint declaration) and publishes on the island's topic, an invalid one
 * flags the field (aria-invalid) and publishes nothing. The control never builds
 * or resizes itself, so first-paint geometry holds.
 *
 * This replaces the native <input type="color"> deliberately: its picker popover
 * is UA-painted and cannot be tokenised (the no-UA-default rule).
 *
 * The optional `listen` prop names a topic the control follows: a valid hex
 * published there updates the field and swatch in place, without republishing —
 * synced state, not user input, so followers never echo. */
window.switchboard.register("color-input", function (el, props, bus) {
  var topic = props.topic;
  var field = el.querySelector(".sb-color-input-text");
  var swatch = el.querySelector(".sb-color-input-swatch");
  var HEX = /^#[0-9a-fA-F]{6}$/;

  function onInput() {
    var value = field.value.trim();
    var valid = HEX.test(value);
    field.setAttribute("aria-invalid", valid ? "false" : "true");
    if (!valid) return;
    swatch.style.setProperty("--sb-swatch", value);
    bus.publish(topic, value);
  }

  field.addEventListener("input", onInput);

  var off = null;
  if (props.listen) {
    off = bus.subscribe(props.listen, function (value) {
      if (typeof value !== "string" || !HEX.test(value)) return;
      field.value = value;
      field.setAttribute("aria-invalid", "false");
      swatch.style.setProperty("--sb-swatch", value);
    });
  }

  return function teardown() {
    field.removeEventListener("input", onInput);
    if (off) off();
  };
});
