(function () {
  "use strict";

  window.switchboard.register("vanilla-counter", function (el, props, bus) {
    var count = props.start || 0;
    var pad = document.createElement("div");
    var button = document.createElement("button");

    pad.className = "sb-demo-pad";
    button.className = "sb-demo-btn";
    button.type = "button";

    function paint() {
      button.textContent = "count: " + count;
    }

    button.addEventListener("click", function () {
      count += 1;
      paint();
      bus.publish("vanilla:count", count);
    });

    paint();
    pad.appendChild(button);
    el.replaceChildren(pad);

    return function teardown() {
      pad.remove();
    };
  });

  window.switchboard.register("vanilla-readout", function (el, props, bus) {
    var out = document.createElement("div");
    out.className = "sb-demo-readout";
    out.textContent = "waiting for a click...";
    el.replaceChildren(out);

    var off = bus.subscribe("vanilla:count", function (count) {
      out.textContent = "latest count: " + count;
    });

    return function teardown() {
      off();
      out.remove();
    };
  });
})();
