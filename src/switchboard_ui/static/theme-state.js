/* Theme-state adapter: apply live token edits to a scoped element.
 *
 * This is what makes the preview live. It binds bus topics to token names
 * (`{ "token:accent": "--sb-color-accent", ... }`): when a bound topic publishes
 * a value, it writes that value onto the scoping element(s) as the token's two
 * scheme arms (`--sb-color-accent-light` / `-dark`) AND re-declares the composed
 * `light-dark()` on the scope. The re-declaration is the crux: the composed token
 * on `:root` is inherited already-substituted, so overriding the arms alone on a
 * descendant scope does not reproject it. Re-declaring the composition on the
 * scope makes it re-substitute the scope's arms, and the whole scoped subtree —
 * everything reading `var(--sb-color-accent)` — repaints for free. The
 * composition string is fixed boilerplate per the arm model, not a parsed value.
 *
 * Scoped, not :root: the overrides land only on the preview's wrapper, so the
 * surrounding chrome (the controls editing the theme) stays stable while the
 * preview restyles. The token names come from the trusted bindings, never from
 * the published value, so a value can only ever be a CSS value, not a selector. */
window.switchboard.register("theme-state", function (el, props, bus) {
  var scopes = Array.prototype.slice.call(document.querySelectorAll(props.scope));
  var bindings = props.bindings || {};
  var offs = [];

  Object.keys(bindings).forEach(function (topic) {
    var token = bindings[topic];
    offs.push(
      bus.subscribe(topic, function (value) {
        if (typeof value !== "string") return;
        var composed =
          "light-dark(var(" + token + "-light), var(" + token + "-dark))";
        scopes.forEach(function (scope) {
          scope.style.setProperty(token + "-light", value);
          scope.style.setProperty(token + "-dark", value);
          scope.style.setProperty(token, composed);
        });
      })
    );
  });

  return function teardown() {
    offs.forEach(function (off) {
      off();
    });
  };
});
