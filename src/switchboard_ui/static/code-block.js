/* Code-block adapter: copy the block's source to the clipboard.
 *
 * The lighter sibling of the theme-export adapter. On click it reads the code
 * element's textContent (the exact source rendered into <code>) and writes it to
 * the clipboard, reporting the outcome in the polite status node. A block built
 * without a copy button (code_block(copy=False)) has no .sb-code-copy, so the
 * adapter mounts, finds nothing to wire, and no-ops — a static block needs no JS.
 * The block carries no bus topics: copying is an on-demand action, not an event. */
window.switchboard.register("code-block", function (el, props, bus) {
  var button = el.querySelector(".sb-code-copy");
  var status = el.querySelector(".sb-code-status");
  var code = el.querySelector(".sb-code-text");
  if (!button || !code) return;

  function report(message) {
    if (status) status.textContent = message;
  }

  function onClick() {
    var text = code.textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () {
          report("Copied");
        },
        function () {
          report("Copy failed");
        }
      );
    } else {
      report("Clipboard unavailable");
    }
  }

  button.addEventListener("click", onClick);

  return function teardown() {
    button.removeEventListener("click", onClick);
  };
});
