/* Color picker adapter: a saturation/value area + hue slider + hex field, synced.
 *
 * Augments the color input. The swatch (the popover trigger) and the spectrum
 * surfaces are server-rendered; this adapter wires the interaction. One HSV model
 * is the source of truth: the SV area sets saturation/value, the hue slider sets
 * hue, the hex field sets all three; each change repaints the swatch + the
 * spectrum and publishes the colour on the island's topic. It never builds or
 * resizes anything.
 *
 * The two spectrum gradients are functional DATA-VIZ: a full colour-space surface
 * cannot come from the token palette, so they are set inline as live data — the
 * one sanctioned exception to the no-UA-default / token-only rule (philosophy
 * §17). Everything else (borders, the handle ring, the gap) is the theme's. */
window.switchboard.register("color-picker", function (el, props, bus) {
  var topic = props.topic;
  var trigger = el.querySelector(".sb-color-picker-swatch");
  var field = el.querySelector(".sb-color-input-text");
  var area = el.querySelector(".sb-color-picker-area");
  var areaHandle = el.querySelector(".sb-color-picker-area-handle");
  var hue = el.querySelector(".sb-color-picker-hue");
  var hueThumb = el.querySelector(".sb-color-picker-hue-thumb");
  var panel = el.querySelector(".sb-popover-panel");
  var HEX = /^#[0-9a-fA-F]{6}$/;

  // --- colour maths --------------------------------------------------------
  function clamp(n, lo, hi) {
    return n < lo ? lo : n > hi ? hi : n;
  }
  function hsvToRgb(h, s, v) {
    var c = v * s;
    var x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    var m = v - c;
    var seg = Math.floor(h / 60) % 6;
    var rgb = [
      [c, x, 0],
      [x, c, 0],
      [0, c, x],
      [0, x, c],
      [x, 0, c],
      [c, 0, x],
    ][seg];
    return [
      Math.round((rgb[0] + m) * 255),
      Math.round((rgb[1] + m) * 255),
      Math.round((rgb[2] + m) * 255),
    ];
  }
  function rgbToHsv(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;
    var max = Math.max(r, g, b);
    var min = Math.min(r, g, b);
    var d = max - min;
    var h = 0;
    if (d !== 0) {
      if (max === r) h = 60 * ((((g - b) / d) % 6) + 6);
      else if (max === g) h = 60 * ((b - r) / d + 2);
      else h = 60 * ((r - g) / d + 4);
      h %= 360;
    }
    return { h: h, s: max === 0 ? 0 : d / max, v: max };
  }
  function hexToHsv(hex) {
    return rgbToHsv(
      parseInt(hex.slice(1, 3), 16),
      parseInt(hex.slice(3, 5), 16),
      parseInt(hex.slice(5, 7), 16)
    );
  }
  function hsvToHex(h, s, v) {
    return (
      "#" +
      hsvToRgb(h, s, v)
        .map(function (ch) {
          var t = clamp(ch, 0, 255).toString(16);
          return t.length === 1 ? "0" + t : t;
        })
        .join("")
    );
  }

  var st = hexToHsv(field.value);

  // --- spectrum gradients (the data-viz escape; set inline as live data) ----
  hue.style.background =
    "linear-gradient(to right, #f00 0%, #ff0 17%, #0f0 33%," +
    " #0ff 50%, #00f 67%, #f0f 83%, #f00 100%)";
  function paintArea() {
    area.style.background =
      "linear-gradient(to top, #000, rgba(0,0,0,0))," +
      " linear-gradient(to right, #fff, " +
      hsvToHex(st.h, 1, 1) +
      ")";
  }
  area.style.touchAction = "none";
  hue.style.touchAction = "none";

  // --- render --------------------------------------------------------------
  function placeHandles() {
    var ar = area.getBoundingClientRect();
    if (ar.width) {
      var half = areaHandle.offsetWidth / 2;
      areaHandle.style.left = st.s * ar.width - half + "px";
      areaHandle.style.top = (1 - st.v) * ar.height - half + "px";
    }
    var hr = hue.getBoundingClientRect();
    if (hr.width) {
      hueThumb.style.left = (st.h / 360) * hr.width - hueThumb.offsetWidth / 2 + "px";
    }
  }
  function syncVisuals() {
    var hex = hsvToHex(st.h, st.s, st.v);
    trigger.style.background = hex;
    area.setAttribute(
      "aria-valuetext",
      Math.round(st.s * 100) + "% saturation, " + Math.round(st.v * 100) + "% brightness"
    );
    hue.setAttribute("aria-valuenow", String(Math.round(st.h)));
    hue.setAttribute("aria-valuetext", Math.round(st.h) + " degrees");
    placeHandles();
    return hex;
  }
  function commitFromSpectrum() {
    var hex = syncVisuals();
    field.value = hex;
    field.setAttribute("aria-invalid", "false");
    bus.publish(topic, hex);
  }

  // --- pointer drag --------------------------------------------------------
  var svDown = false;
  var hueDown = false;
  function svFrom(e) {
    var r = area.getBoundingClientRect();
    st.s = clamp((e.clientX - r.left) / r.width, 0, 1);
    st.v = 1 - clamp((e.clientY - r.top) / r.height, 0, 1);
    commitFromSpectrum();
  }
  function hueFrom(e) {
    var r = hue.getBoundingClientRect();
    st.h = clamp((e.clientX - r.left) / r.width, 0, 1) * 360;
    paintArea();
    commitFromSpectrum();
  }
  function onSvDown(e) {
    svDown = true;
    area.setPointerCapture(e.pointerId);
    svFrom(e);
  }
  function onSvMove(e) {
    if (svDown) svFrom(e);
  }
  function onSvUp() {
    svDown = false;
  }
  function onHueDown(e) {
    hueDown = true;
    hue.setPointerCapture(e.pointerId);
    hueFrom(e);
  }
  function onHueMove(e) {
    if (hueDown) hueFrom(e);
  }
  function onHueUp() {
    hueDown = false;
  }

  // --- keyboard ------------------------------------------------------------
  function onSvKey(e) {
    var d = e.shiftKey ? 0.1 : 0.01;
    if (e.key === "ArrowLeft") st.s = clamp(st.s - d, 0, 1);
    else if (e.key === "ArrowRight") st.s = clamp(st.s + d, 0, 1);
    else if (e.key === "ArrowDown") st.v = clamp(st.v - d, 0, 1);
    else if (e.key === "ArrowUp") st.v = clamp(st.v + d, 0, 1);
    else if (e.key === "Home") st.s = 0;
    else if (e.key === "End") st.s = 1;
    else return;
    e.preventDefault();
    commitFromSpectrum();
  }
  function onHueKey(e) {
    var d = e.shiftKey ? 10 : 1;
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") st.h = clamp(st.h - d, 0, 360);
    else if (e.key === "ArrowRight" || e.key === "ArrowUp") st.h = clamp(st.h + d, 0, 360);
    else if (e.key === "Home") st.h = 0;
    else if (e.key === "End") st.h = 360;
    else return;
    e.preventDefault();
    paintArea();
    commitFromSpectrum();
  }

  // --- hex field (the precise, accessible control) -------------------------
  function onFieldInput() {
    var v = field.value.trim();
    var valid = HEX.test(v);
    field.setAttribute("aria-invalid", valid ? "false" : "true");
    if (!valid) return;
    st = hexToHsv(v);
    paintArea();
    syncVisuals(); // swatch, aria, handles — but not the field (the user owns it)
    bus.publish(topic, v);
  }

  // --- the panel is laid out only once shown; place the handles on open -----
  function onToggle(e) {
    if (e.newState === "open") placeHandles();
  }

  paintArea();
  syncVisuals();

  area.addEventListener("pointerdown", onSvDown);
  area.addEventListener("pointermove", onSvMove);
  area.addEventListener("pointerup", onSvUp);
  area.addEventListener("keydown", onSvKey);
  hue.addEventListener("pointerdown", onHueDown);
  hue.addEventListener("pointermove", onHueMove);
  hue.addEventListener("pointerup", onHueUp);
  hue.addEventListener("keydown", onHueKey);
  field.addEventListener("input", onFieldInput);
  panel.addEventListener("toggle", onToggle);

  return function teardown() {
    area.removeEventListener("pointerdown", onSvDown);
    area.removeEventListener("pointermove", onSvMove);
    area.removeEventListener("pointerup", onSvUp);
    area.removeEventListener("keydown", onSvKey);
    hue.removeEventListener("pointerdown", onHueDown);
    hue.removeEventListener("pointermove", onHueMove);
    hue.removeEventListener("pointerup", onHueUp);
    hue.removeEventListener("keydown", onHueKey);
    field.removeEventListener("input", onFieldInput);
    panel.removeEventListener("toggle", onToggle);
  };
});
