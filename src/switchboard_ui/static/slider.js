/* Slider adapter: a native range that publishes its value as the user drags.
 *
 * The range is server-rendered with min/max/step/value, so it is present and the
 * thumb is correctly placed at first paint; this adapter only publishes. On every
 * `input` (the live drag stream) it coerces the value to a number — integer or
 * float per the `integer` prop the factory derived from the bounds — publishes it
 * on the island's topic, and mirrors it into the optional readout. Native range
 * already clamps to the bounds and snaps to the step and carries the full slider
 * keyboard model, so there is nothing to validate and no keyboard to re-implement. */
window.switchboard.register("slider", function (el, props, bus) {
  var topic = props.topic;
  var toNumber = props.integer
    ? function (v) {
        return parseInt(v, 10);
      }
    : parseFloat;
  var input = el.querySelector(".sb-slider-input");
  var readout = el.querySelector(".sb-slider-value");

  function onInput() {
    if (readout) readout.textContent = input.value;
    bus.publish(topic, toNumber(input.value));
  }

  input.addEventListener("input", onInput);

  return function teardown() {
    input.removeEventListener("input", onInput);
  };
});
