/* Pre-paint restoration of a shared nav rail's scroll position.
 *
 * Emitted inline by `nav(scroll_key=...)`, immediately *before* the nav markup.
 * It is inline and parser-blocking on purpose: the position has to be applied
 * before this document paints the rail, and every deferred alternative paints
 * the rail at zero first and then corrects it, which the reader sees as a jump.
 *
 * Why before the nav rather than after it, which reads more naturally: a
 * document arrives in chunks, and the parser can finish the nav, yield at a
 * chunk boundary, and let the browser paint before it reaches the next byte.
 * Placed after the nav, that paints the *complete* rail at the top and then
 * snaps it down — measured, one frame, on a fixture chunked at 2KB. Placed
 * before, the script starts running while the rail is still empty, so there is
 * no complete-and-wrong frame to see.
 *
 * The cost of being early is that the rail has no scroll range yet: writing 445
 * to an empty container clamps to 0. So it re-applies on every animation frame
 * until the target sticks or the document finishes loading. Each write lands on
 * whatever range exists at that moment, so the rail scrolls down as its content
 * arrives and is never painted complete-but-unscrolled.
 *
 * It stops the moment the reader takes over. A reader who scrolls during load
 * has said where they want to be, and continuing to re-apply a stored offset
 * would drag them back — the same class of defect as the reset it fixes.
 *
 * Everything is guarded: storage throws in a private or blocked context, and a
 * failure here must cost the enhancement and nothing else. The links are real
 * links; the nav is fully readable with none of this running. */
(function () {
  var script = document.currentScript;
  if (!script) return;
  var key = script.getAttribute("data-scroll-key");
  if (!key) return;

  var stored;
  try {
    stored = sessionStorage.getItem("sb-nav-scroll:" + key);
  } catch (e) {
    return;
  }
  if (stored === null) return;

  var target = parseFloat(stored);
  // Reject NaN, Infinity, and negatives: a corrupted value must move nothing.
  if (!isFinite(target) || target <= 0) return;

  var owner = script.parentElement;
  while (owner && owner !== document.documentElement) {
    var overflow = getComputedStyle(owner).overflowY;
    if (overflow === "auto" || overflow === "scroll") break;
    owner = owner.parentElement;
  }
  if (!owner || owner === document.documentElement) return;

  // While restoration is in flight the rail's position is this script's, not
  // the reader's. The saving adapter watches for this marker and holds off, so
  // a navigation that happens mid-restore cannot persist an offset the reader
  // never chose — which would silently overwrite the very position being
  // restored, and lose their place for good.
  owner.setAttribute("data-sb-restoring", "");

  var done = false;
  function stop() {
    done = true;
    owner.removeAttribute("data-sb-restoring");
    window.removeEventListener("wheel", stop);
    window.removeEventListener("touchstart", stop);
    window.removeEventListener("keydown", stop);
  }
  window.addEventListener("wheel", stop, { passive: true });
  window.addEventListener("touchstart", stop, { passive: true });
  window.addEventListener("keydown", stop);

  // A frame budget, so a pathological page cannot leave this looping forever.
  var frames = 300;

  function apply() {
    if (done) return;
    owner.scrollTop = target;

    // The furthest the target can reach in the range that exists right now. A
    // rail still filling in has less range than it will end up with, so landing
    // short is expected and is not a reason to give up.
    var range = owner.scrollHeight - owner.clientHeight;
    var reachable = range > 0 ? Math.min(target, range) : 0;
    // Sub-pixel tolerance: a fractional device pixel ratio makes scrollTop land
    // a hair off an integer target, which is settled for every purpose here.
    var settled = Math.abs(owner.scrollTop - reachable) < 1;

    // Stop only once the write has actually taken *and* the document has
    // finished growing. Stopping on readyState alone loses a race that a fast
    // cached history navigation reliably wins: the document can reach
    // "complete" before the first frame callback runs, so the single write
    // lands on a container that has not been laid out yet, clamps to zero, and
    // the rail stays at the top for good.
    if (settled && document.readyState === "complete") {
      stop();
      return;
    }
    if (--frames <= 0) {
      stop();
      return;
    }
    requestAnimationFrame(apply);
  }
  apply();
})();
