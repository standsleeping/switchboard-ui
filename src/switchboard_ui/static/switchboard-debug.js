/* switchboard-ui debug overlay — an optional dev affordance, shipped as its own
 * module so the core runtime carries no diagnostics.
 *
 * Standalone: it touches only the DOM and the `window.switchboard` global, never
 * the runtime's bus or registry. It augments the global the runtime creates, so
 * it must load *after* switchboard.js (render_document emits it in that order).
 *
 * `switchboard.debug()` toggles a runtime-injected outline overlay over the
 * frame tree: an `outline` on every frame and island — outline, not border, so
 * it draws on top without resizing the boxes it measures — plus an override that
 * un-collapses empty cells so every region shows, not just the filled ones. The
 * injected <style> trails layout.css in the head, so equal-specificity rules win
 * without `!important`. The package ships zero visual style, so this is how you
 * see the structure without DevTools.
 *
 * Loading the page with `?debug` in the URL enables the overlay automatically,
 * so the structure is visible in development without knowing the console call. A
 * shipped URL won't carry the param, so production stays clean. */
(function () {
  "use strict";

  var DEBUG_STYLE_ID = "sb-debug-overlay";
  var DEBUG_CSS =
    ".sb-frame{outline:1px solid #c0392b}" +
    ".sb-island{outline:1px dashed #2980b9}" +
    ".sb-frame:empty{display:flex}";

  function debug(force) {
    var existing = document.getElementById(DEBUG_STYLE_ID);
    var on = force === undefined ? !existing : !!force;
    if (on && !existing) {
      var style = document.createElement("style");
      style.id = DEBUG_STYLE_ID;
      style.textContent = DEBUG_CSS;
      document.head.appendChild(style);
    } else if (!on && existing) {
      existing.remove();
    }
    return on;
  }

  // Augment the global the runtime created (guarded so the module never throws
  // if loaded alone, though it is meant to load after switchboard.js).
  (window.switchboard = window.switchboard || {}).debug = debug;

  // Auto-enable from the URL so structure is visible in dev without the console.
  if (new URLSearchParams(window.location.search).has("debug")) debug(true);
})();
