/* Theme-export adapter: serialise the scope's current tokens to a tokens.css.
 *
 * The read-back direction of theme-state. On click it reads every bound token's
 * current value off the scope with getComputedStyle — which resolves the value
 * whether it was edited (an inline override on the scope) or not (inherited from
 * :root) — and assembles a `:root {}` block. An arm token emits its two arms plus
 * the fixed `light-dark()` composition line (the arm model); a value token emits
 * one declaration. A token appears once even though an arm token has two bindings.
 * The result is copied to the clipboard and logged, so it is recoverable either
 * way. Token names come from the trusted bindings, never from page input. */
window.switchboard.register("theme-export", function (el, props, bus) {
  var button = el.querySelector(".sb-export-button");
  var status = el.querySelector(".sb-export-status");

  function buildCss() {
    var scope = document.querySelector(props.scope);
    if (!scope) return "";
    var style = getComputedStyle(scope);
    var lines = [];
    var seen = {};
    (props.bindings || []).forEach(function (binding) {
      var token = binding.token;
      if (seen[token]) return;
      seen[token] = true;
      if (binding.kind === "arm") {
        var light = style.getPropertyValue(token + "-light").trim();
        var dark = style.getPropertyValue(token + "-dark").trim();
        lines.push("  " + token + "-light: " + light + ";");
        lines.push("  " + token + "-dark: " + dark + ";");
        lines.push(
          "  " + token + ": light-dark(var(" + token + "-light), var(" + token + "-dark));"
        );
      } else {
        lines.push("  " + token + ": " + style.getPropertyValue(token).trim() + ";");
      }
    });
    return ":root {\n" + lines.join("\n") + "\n}\n";
  }

  function onClick() {
    var css = buildCss();
    console.log("[theme-export]\n" + css);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(css).then(
        function () {
          status.textContent = "Copied tokens.css";
        },
        function () {
          status.textContent = "Copy failed (see console)";
        }
      );
    } else {
      status.textContent = "Clipboard unavailable (see console)";
    }
  }

  button.addEventListener("click", onClick);

  return function teardown() {
    button.removeEventListener("click", onClick);
  };
});
