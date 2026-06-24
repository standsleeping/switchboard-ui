/* Value-field adapter: a text field that publishes its value as the user types.
 *
 * The field is server-rendered (present and sized at first paint); this adapter
 * only publishes. On every `input` it publishes the field's raw string on the
 * island's topic — a theme-state ValueBinding writes that straight onto the bound
 * token, so the preview repaints live. It validates nothing: any string is a
 * candidate CSS value, and the preview is the feedback. The control never builds
 * or resizes itself, so first-paint geometry holds. */
window.switchboard.register("value-field", function (el, props, bus) {
  var topic = props.topic;
  var field = el.querySelector(".sb-value-field-text");

  function onInput() {
    bus.publish(topic, field.value);
  }

  field.addEventListener("input", onInput);

  return function teardown() {
    field.removeEventListener("input", onInput);
  };
});
