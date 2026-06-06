(function () {
  "use strict";

  // SBUI design tokens are CSS custom properties, so they inherit through the
  // shadow boundary; the .sb-demo-* classes do not. A shadow-DOM component
  // therefore re-expresses those classes' rules from the same tokens (the source
  // of truth) rather than hard-coding values. The fallbacks match shell.css so
  // the component looks right with no host present.
  var COUNTER_STYLE = [
    ":host { display: block; padding: var(--spacing-xl, 24px); }",
    "button {",
    "  font: inherit; color: inherit;",
    "  background: var(--color-surface, light-dark(#fafafa, #161618));",
    "  border: var(--border-width-thin, 1px) solid",
    "    var(--color-border, light-dark(#e2e2e2, #2a2a2c));",
    "  padding: var(--spacing-sm, 8px); min-inline-size: 8rem; cursor: pointer;",
    "}",
    "button:focus-visible {",
    "  outline: 2px solid var(--color-accent, light-dark(#7c3aed, #a78bfa));",
    "  outline-offset: -2px;",
    "}",
  ].join("");

  var READOUT_STYLE = [
    ":host {",
    "  display: block; padding: var(--spacing-sm, 8px);",
    "  color: var(--color-text-muted, light-dark(#6a6a6a, #9a9a9a));",
    "}",
  ].join("");

  class ExampleCounter extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this.bus = null;
      this.count = 0;
    }

    configure(props, bus) {
      this.bus = bus;
      this.count = props.start || 0;
      this.render();
    }

    connectedCallback() {
      this.render();
    }

    render() {
      this.shadowRoot.innerHTML = [
        "<style>",
        COUNTER_STYLE,
        "</style>",
        '<button type="button">count: ' + this.count + "</button>",
      ].join("");

      this.shadowRoot.querySelector("button").addEventListener("click", () => {
        this.count += 1;
        this.bus.publish("web:count", this.count);
        this.render();
      });
    }
  }

  class ExampleReadout extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this.off = null;
    }

    configure(props, bus) {
      this.render("waiting for a click...");
      this.off = bus.subscribe("web:count", (count) => {
        this.render("latest count: " + count);
      });
    }

    disconnectedCallback() {
      if (this.off) this.off();
    }

    render(message) {
      this.shadowRoot.innerHTML = [
        "<style>",
        READOUT_STYLE,
        "</style>",
        "<strong>" + message + "</strong>",
      ].join("");
    }
  }

  customElements.define("example-counter", ExampleCounter);
  customElements.define("example-readout", ExampleReadout);

  window.switchboard.register("web-counter", function (el, props, bus) {
    var node = document.createElement("example-counter");
    node.configure(props, bus);
    el.replaceChildren(node);
    return function teardown() {
      node.remove();
    };
  });

  window.switchboard.register("web-readout", function (el, props, bus) {
    var node = document.createElement("example-readout");
    node.configure(props, bus);
    el.replaceChildren(node);
    return function teardown() {
      node.remove();
    };
  });
})();
