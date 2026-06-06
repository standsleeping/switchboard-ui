/* Demo island adapter: a counter button.
 * Publishes count:changed onto the bus on every click. */
window.switchboard.register("counter", function (el, props, bus) {
  var n = props.start || 0;
  var btn = document.createElement("button");
  btn.className = "sb-demo-btn";

  function paint() {
    btn.textContent = "count: " + n;
  }

  paint();
  btn.addEventListener("click", function () {
    n += 1;
    paint();
    bus.publish("count:changed", n);
  });
  el.appendChild(btn);

  return function teardown() {
    btn.remove();
  };
});
