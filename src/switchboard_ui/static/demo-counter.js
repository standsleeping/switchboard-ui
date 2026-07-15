/* Demo island adapter: a counter button.
 * Publishes count:changed onto the bus on every click.
 *
 * The button is server-rendered into the island's initial HTML, so it is
 * present and correctly sized at first paint; this adapter enhances it in
 * place. It never builds or resizes the markup. */
window.switchboard.register("counter", function (el, props, bus) {
  var n = props.start || 0;
  var btn = el.querySelector(".sb-demo-btn");

  function paint() {
    btn.textContent = "count: " + n;
  }

  function onClick() {
    n += 1;
    paint();
    bus.publish("count:changed", n);
  }

  btn.addEventListener("click", onClick);

  return function teardown() {
    btn.removeEventListener("click", onClick);
  };
});
