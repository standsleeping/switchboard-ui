/* Nav adapter: persist a scrolled rail's position across native navigations.
 *
 * The boundary this exists for: a forward navigation creates a new document and
 * therefore a new element scroll container, which the browser starts at zero. A
 * rail that is shared chrome — the same nav on every page — loses the reader's
 * place on every click, even though the browser restored everything it owns.
 * The page's own scroll position is not this adapter's business; the browser
 * restores that correctly already.
 *
 * This half only *saves*. Restoring happens in the tiny inline script the nav
 * factory emits directly after the nav markup, because restoring after first
 * paint would replace a reset with a visible corrective jump — the reader would
 * watch the rail snap. Saving has no such deadline, so it lives here with the
 * other adapters.
 *
 * sessionStorage, not localStorage: the position wanted is per-tab navigation
 * continuity, not a durable preference. Two tabs on the same site scroll their
 * rails independently, and closing the tab forgets it.
 *
 * Storage can throw (Safari private mode, a blocked third-party context, a full
 * quota), so every access is guarded. A failure costs the enhancement and
 * nothing else: the links are real links and the nav is fully readable without
 * any of this.
 *
 * It defers to the restoring script while that is still working: see the
 * `data-sb-restoring` marker below. Without that, leaving a page before its
 * rail finished restoring would save the un-restored position over the stored
 * one, and the reader would lose their place on the *next* navigation rather
 * than this one — the hardest kind of bug of this class to attribute.
 *
 * No click is intercepted, and back/forward-cache restores are left alone: a
 * bfcache traversal reuses the live DOM, whose element scroll position the
 * browser has already restored, so writing to it would fight the platform. */
window.switchboard.register("nav", function (el, props) {
  var key = props && props.scrollKey;
  if (!key) return;
  var name = "sb-nav-scroll:" + key;

  var owner = el.parentElement;
  while (owner && owner !== document.documentElement) {
    var overflow = getComputedStyle(owner).overflowY;
    if (overflow === "auto" || overflow === "scroll") break;
    owner = owner.parentElement;
  }
  if (!owner || owner === document.documentElement) return;

  function save() {
    // Restoration in flight: the rail is where the restoring script put it, not
    // where the reader put it. Persisting now would overwrite a good stored
    // offset with a transient one — and if the navigation away happens before
    // restoration lands, that transient one is zero.
    if (owner.hasAttribute("data-sb-restoring")) return;
    try {
      sessionStorage.setItem(name, String(owner.scrollTop));
    } catch (e) {
      /* storage unavailable: the nav still works, it just forgets */
    }
  }

  // Throttled to one write per frame: a scroll fires far more often than a
  // frame paints, and the value only has to be correct when the page unloads.
  var pending = false;
  function onScroll() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(function () {
      pending = false;
      save();
    });
  }

  owner.addEventListener("scroll", onScroll, { passive: true });
  // pagehide rather than unload: unload is unreliable and disables the
  // back/forward cache in some engines. pagehide fires for both a real unload
  // and a bfcache suspension.
  window.addEventListener("pagehide", save);
  el.addEventListener("click", save);

  return function teardown() {
    owner.removeEventListener("scroll", onScroll);
    window.removeEventListener("pagehide", save);
    el.removeEventListener("click", save);
  };
});
