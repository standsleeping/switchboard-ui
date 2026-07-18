/* Segmented toggle adapter: a radio group that publishes the chosen value.
 *
 * The option buttons are server-rendered (present, sized, and focus-ordered at
 * first paint); this adapter only *enhances* them. It never builds or resizes
 * the control, so first-paint geometry is preserved.
 *
 * Radio-group semantics (WAI-ARIA): exactly one option is checked, and it is the
 * group's single tab stop (roving tabindex). Selection follows focus — the arrow
 * keys move to the previous / next option (wrapping) and check it, Home / End
 * jump to the first / last, and a click or native Space / Enter checks the
 * pressed option. Every selection moves aria-checked, moves the tab stop, and
 * publishes the value on the island's topic.
 *
 * The optional `listen` prop names a topic the group follows: a value published
 * there moves the selection in place — no focus steal, no republish. An applied
 * value is synced state, not user input, so two controls may follow each other
 * without echoing. */
window.switchboard.register("segmented", function (el, props, bus) {
  var topic = props.topic;
  var radios = Array.prototype.slice.call(
    el.querySelectorAll(".sb-segmented-option")
  );

  function checkedIndex() {
    for (var i = 0; i < radios.length; i++) {
      if (radios[i].getAttribute("aria-checked") === "true") return i;
    }
    return 0;
  }

  function check(radio) {
    radios.forEach(function (r) {
      var on = r === radio;
      r.setAttribute("aria-checked", on ? "true" : "false");
      r.tabIndex = on ? 0 : -1;
    });
  }

  function select(radio) {
    check(radio);
    radio.focus();
    bus.publish(topic, radio.dataset.value);
  }

  function onClick(e) {
    select(e.currentTarget);
  }

  function onKeydown(e) {
    var last = radios.length - 1;
    var i = checkedIndex();
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      select(radios[i === last ? 0 : i + 1]);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      select(radios[i === 0 ? last : i - 1]);
    } else if (e.key === "Home") {
      select(radios[0]);
    } else if (e.key === "End") {
      select(radios[last]);
    } else {
      return; // not a navigation key; let the event proceed
    }
    e.preventDefault();
  }

  radios.forEach(function (r) {
    r.addEventListener("click", onClick);
    r.addEventListener("keydown", onKeydown);
  });

  var off = null;
  if (props.listen) {
    off = bus.subscribe(props.listen, function (value) {
      if (typeof value !== "string") return;
      for (var i = 0; i < radios.length; i++) {
        if (radios[i].dataset.value === value) {
          check(radios[i]);
          return;
        }
      }
    });
  }

  return function teardown() {
    radios.forEach(function (r) {
      r.removeEventListener("click", onClick);
      r.removeEventListener("keydown", onKeydown);
    });
    if (off) off();
  };
});
