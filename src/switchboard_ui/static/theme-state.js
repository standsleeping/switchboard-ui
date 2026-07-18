/* Theme-state adapter: apply live token edits to a scoped element.
 *
 * This is what makes the preview live. Each binding maps a bus topic to a token
 * edit; when a bound topic publishes a value, the edit is written onto the
 * scoping element(s). Two binding kinds:
 *
 *   - "arm":   one scheme arm of a scheme-varying token (a color). Writes
 *              `<token>-<arm>` (`--sb-color-accent-light` / `-dark`) AND
 *              re-declares the composed `light-dark()` on the scope. The
 *              re-declaration is the crux: the composed token on `:root` is
 *              inherited already-substituted, so overriding an arm alone on a
 *              descendant scope does not reproject it. Re-declaring the
 *              composition on the scope makes it re-substitute the scope's arms,
 *              and everything reading `var(<token>)` in the subtree repaints. The
 *              unedited arm resolves from `:root`, so editing one arm leaves the
 *              other scheme untouched. The composition string is fixed boilerplate
 *              per the arm model, not a parsed value.
 *   - "value": a scheme-invariant token (length / number / font family). Written
 *              straight onto the token, no arms, no composition.
 *
 * Scoped, not :root: the overrides land only on the preview's wrapper, so the
 * surrounding chrome (the controls editing the theme) stays stable while the
 * preview restyles. The token names come from the trusted bindings, never from
 * the published value, so a value can only ever be a CSS value, not a selector. */
window.switchboard.register("theme-state", function (el, props, bus) {
  var scopes = Array.prototype.slice.call(document.querySelectorAll(props.scope));
  var bindings = props.bindings || [];
  var offs = [];

  function apply(scope, binding, value) {
    if (binding.kind === "arm") {
      var token = binding.token;
      scope.style.setProperty(token + "-" + binding.arm, value);
      scope.style.setProperty(
        token,
        "light-dark(var(" + token + "-light), var(" + token + "-dark))"
      );
    } else if (binding.kind === "value") {
      scope.style.setProperty(binding.token, value);
    }
  }

  bindings.forEach(function (binding) {
    offs.push(
      bus.subscribe(binding.topic, function (value) {
        if (typeof value !== "string") return;
        scopes.forEach(function (scope) {
          apply(scope, binding, value);
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
