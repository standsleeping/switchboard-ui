/* Demo island adapter: a readout.
 * Subscribes to count:changed and shows the latest value. */
window.switchboard.register("readout", function (el, props, bus) {
  var out = document.createElement("div");
  out.className = "sb-demo-readout";
  out.textContent = "waiting for a click...";
  el.appendChild(out);

  var off = bus.subscribe("count:changed", function (n) {
    out.textContent = "latest count: " + n;
  });

  return function teardown() {
    off();
    out.remove();
  };
});
