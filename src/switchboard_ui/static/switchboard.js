/* switchboard-ui runtime — zero-build, no dependencies.
 *
 * Three pieces:
 *   - bus:      a topic-keyed pub/sub channel; the global-state layer.
 *   - register: an adapter registry, name -> mount(el, props, bus) -> teardown.
 *   - boot:     scan the DOM for [data-island] mount points and mount each.
 *
 * The mount contract `mount(el, props, bus) => teardown` is the stable seam.
 * Vanilla, Web Component, and React islands are all just adapters that satisfy
 * it; the page and the Python renderer never know which kind an island is.
 *
 * Cross-island wiring is declared as data on each mount point
 * (data-pub / data-sub), so the dependency graph is recoverable from the HTML
 * alone, without executing anything. The runtime reads data-props to mount;
 * the declared topics are the static-analysis surface. */
(function () {
  "use strict";

  // --- bus: topic -> Set<handler> -------------------------------------------
  var listeners = new Map();
  var bus = {
    publish: function (topic, detail) {
      var set = listeners.get(topic);
      if (!set) return;
      // Copy so a handler that (un)subscribes mid-dispatch can't corrupt it.
      Array.from(set).forEach(function (fn) {
        fn(detail, topic);
      });
    },
    subscribe: function (topic, fn) {
      var set = listeners.get(topic);
      if (!set) {
        set = new Set();
        listeners.set(topic, set);
      }
      set.add(fn);
      return function unsubscribe() {
        set.delete(fn);
      };
    },
  };

  // --- registry: name -> mount(el, props, bus) -> teardown ------------------
  var registry = new Map();
  var mounted = new WeakSet();

  function mountElement(el) {
    if (mounted.has(el)) return;
    var mount = registry.get(el.dataset.island);
    if (!mount) return; // adapter not registered yet; a later register() retries
    var props = el.dataset.props ? JSON.parse(el.dataset.props) : {};
    mounted.add(el);
    var teardown = mount(el, props, bus);
    if (typeof teardown === "function") el.__sbTeardown = teardown;
  }

  function mountAll(root) {
    (root || document).querySelectorAll("[data-island]").forEach(mountElement);
  }

  function register(name, mount) {
    registry.set(name, mount);
    // Mount any mount points already in the DOM for this newly-known adapter.
    mountAll();
  }

  function boot() {
    mountAll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.switchboard = { bus: bus, register: register, boot: boot };
})();
