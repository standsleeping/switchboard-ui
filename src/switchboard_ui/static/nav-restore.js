/* Pre-paint placement of a shared nav rail: restore where the reader was, or on
 * a first visit reveal where they are.
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
 * The cost of being early is that nothing it needs exists yet: the rail has no
 * scroll range, and the current item has not been parsed. So it re-runs on every
 * animation frame until its work sticks or the document finishes loading. Each
 * pass lands on whatever exists at that moment, so the rail settles into place
 * as its content arrives rather than being placed once and left wrong.
 *
 * Two jobs, and which one applies is decided by whether there is a stored offset:
 *
 *   Restore. A stored offset means the reader has been navigating this site and
 *   had the rail somewhere. Put it back, exactly.
 *
 *   Reveal. No stored offset means a first visit — a deep link, a search result,
 *   a shared URL. The rail opens at the top, and on a long rail the page the
 *   reader actually landed on can be far below the fold, so the nav says nothing
 *   about where they are. Scroll by the *smallest* amount that brings the
 *   current item into view. Minimal on purpose: anything more (centring it, say)
 *   moves rows the reader has no reason to expect to move, and an item already
 *   on screen is left exactly where it is.
 *
 * It stops the moment the reader takes over. A reader who scrolls during load
 * has said where they want to be, and continuing to place the rail would drag
 * them back — the same class of defect as the reset this fixes.
 *
 * Everything is guarded: storage throws in a private or blocked context, and a
 * failure here must cost the enhancement and nothing else. The links are real
 * links; the nav is fully readable with none of this running. */
(function () {
  var script = document.currentScript;
  if (!script) return;
  var key = script.getAttribute("data-scroll-key");
  if (!key) return;

  var stored = null;
  try {
    stored = sessionStorage.getItem("sb-nav-scroll:" + key);
  } catch (e) {
    /* storage unavailable: fall through to revealing the current item */
  }

  var target = stored === null ? NaN : parseFloat(stored);
  // Reject NaN, Infinity, and negatives: a corrupted value must not be trusted
  // as a position. Revealing the current item is still worth doing.
  var restoring = isFinite(target) && target > 0;

  var owner = script.parentElement;
  while (owner && owner !== document.documentElement) {
    var overflow = getComputedStyle(owner).overflowY;
    if (overflow === "auto" || overflow === "scroll") break;
    owner = owner.parentElement;
  }
  if (!owner || owner === document.documentElement) return;

  // While this is in flight the rail's position is this script's, not the
  // reader's. The saving adapter watches for this marker and holds off, so a
  // navigation that happens mid-placement cannot persist an offset the reader
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
  // The last position this script wrote, so it can tell its own work from
  // someone else's. Null until it has written anything.
  var placed = null;

  function restore() {
    owner.scrollTop = target;
    // The furthest the target can reach in the range that exists right now. A
    // rail still filling in has less range than it will end up with, so landing
    // short is expected and is not a reason to give up.
    var range = owner.scrollHeight - owner.clientHeight;
    var reachable = range > 0 ? Math.min(target, range) : 0;
    // Sub-pixel tolerance: a fractional device pixel ratio makes scrollTop land
    // a hair off an integer target, which is settled for every purpose here.
    return Math.abs(owner.scrollTop - reachable) < 1;
  }

  function reveal() {
    var current = owner.querySelector('[aria-current="page"]');
    // Not parsed yet. Not settled either, so the loop keeps looking.
    if (!current) return false;
    var view = owner.getBoundingClientRect();
    var item = current.getBoundingClientRect();
    // The nearest edge, and only that far: scroll up if the item sits above the
    // visible band, down if it sits below, and not at all if it is already in.
    if (item.top < view.top) {
      owner.scrollTop += item.top - view.top;
    } else if (item.bottom > view.bottom) {
      owner.scrollTop += item.bottom - view.bottom;
    }
    // Settled only if it actually landed in view. Finding the item is not
    // enough: a rail still filling in may not yet have the range to reach it,
    // and the write clamps short. Re-measured rather than assumed.
    item = current.getBoundingClientRect();
    return item.top >= view.top - 1 && item.bottom <= view.bottom + 1;
  }

  function apply() {
    if (done) return;

    if (!restoring) {
      // Revealing is a courtesy for a rail nobody has touched. If the position
      // changed between frames and this script did not change it, something
      // else did — the reader, or the host page — and it wins. The wheel and
      // key listeners catch a reader's intent, but not every way a rail can be
      // moved fires one, so the position itself is the reliable signal.
      if (placed !== null && Math.abs(owner.scrollTop - placed) > 1) {
        stop();
        return;
      }
      // Revealing finishes the moment the item is in view. It must *not* wait
      // for the document, and must not re-run once satisfied: unlike a stored
      // offset, this target does not move as the rail grows (rows arrive below
      // it), so a second pass has nothing to correct and everything to break —
      // it would undo scrolling that happened in between, and hold the marker
      // that keeps the saving adapter quiet for the whole load.
      if (reveal()) stop();
      else if (--frames <= 0) stop();
      else {
        placed = owner.scrollTop;
        requestAnimationFrame(apply);
      }
      return;
    }

    // Stop only once the write has actually taken *and* the document has
    // finished growing. Stopping on readyState alone loses a race that a fast
    // cached history navigation reliably wins: the document can reach
    // "complete" before the first frame callback runs, so the single write
    // lands on a container that has not been laid out yet, clamps to zero, and
    // the rail stays at the top for good.
    if (restore() && document.readyState === "complete") {
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
