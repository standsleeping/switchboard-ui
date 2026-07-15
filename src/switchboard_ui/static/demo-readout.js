/* Demo island adapter: a readout.
 * Subscribes to count:changed and shows the latest value.
 *
 * The readout is server-rendered into the island's initial HTML (including its
 * waiting message), so it is present at first paint; this adapter enhances it
 * in place. It never builds or resizes the markup. */
window.switchboard.register("readout", function (el, props, bus) {
  var out = el.querySelector(".sb-demo-readout");

  var off = bus.subscribe("count:changed", function (n) {
    out.textContent = "latest count: " + n;
  });

  return function teardown() {
    off();
  };
});
