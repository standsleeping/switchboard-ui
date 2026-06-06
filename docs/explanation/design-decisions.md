# Explanation: design decisions

This is the decision record: the questions that shaped the package, the options weighed, and the choices made. The rest of the documentation describes the system as it stands; this page records why it is that way, including the paths not taken.

## Origin

The starting point was a review of comparison work across small UI frameworks (Mithril, Preact, Hyperapp, Solid, Lit, VanJS), reactivity models (signals, observables, virtual DOM, proxies, compilers, manual), and component-composition approaches. The recurring pull was toward the minimal end: tiny runtimes, no build step, no framework lock-in. In parallel, a body of design-system work had accumulated without a concrete product to aim it at.

The goal that emerged: a reusable Python package for server-rendered HTML pages, into which arbitrarily complex JavaScript mini-apps could be mounted per region, sharing global state, event-driven. That goal was named against an established pattern: the islands architecture (static shell, independent interactive islands) plus an event bus for cross-island state.

## The three founding forks

### Template authoring

Alternatives weighed:

- Pure-Python builders (functions and dataclasses returning HTML strings).
- An existing HTML DSL library (htpy, dominate, FastHTML-style).
- Jinja2 template files.

**Decision: pure-Python builders, zero dependencies.** A survey of the sibling Python projects confirmed the house style (zero runtime deps, src-layout, dataclasses, pure functions, strict tooling), which this choice matches.

### Island runtime

Alternatives weighed:

- Zero-build, data-attribute islands (a `div` with `data-island`, a small runtime that scans and mounts).
- Zero-build, native Web Components.
- A build step (bundler), enabling JSX/Solid/Svelte islands.

**Decision: a stable mount contract is the seam.** `mount(element, props, bus)` returning `teardown` is the interface; vanilla, Web Component, and React become adapters that satisfy it. The package ships only the vanilla adapter and the contract; other adapters are later additions that change nothing in the core. No build step.

### Global state

Alternatives weighed:

- A shared store whose mutations broadcast events (hybrid).
- A pure event bus (ephemeral pub/sub, no canonical store).
- Federated per-island stores coordinated by a bus.

**Decision: declarative pub/sub.** Islands declare the topics they publish and subscribe to as data on the descriptor, rather than calling the bus imperatively. Static analyzability (being able to draw the dependency diagram without executing anything) is the deciding factor, and it is what produced the spine.

## The spine

Synthesizing the three answers produced the organizing idea: one declarative `Island` descriptor with three consumers. Python emits it as a mount-point `div` with `data-*` attributes; the browser runtime mounts and wires from it; a static analyzer can graph the pub/sub wiring from the declared topics without executing anything. This is the structural payoff of the declarative-wiring decision. See [Architecture](architecture.md).

## Greenfield and name

**Relationship to the existing component-host project.** Alternatives: clean-room (build fresh but lift what works from the existing app), pure greenfield, or extraction (pull code out of the existing app). **Decision: pure greenfield.** The existing app is a full web application with its own dependencies; the new package is the zero-dependency library it was groping toward, so it starts clean.

**Name.** Alternatives: `islehost`, `atoll`, `switchboard`. **Decision: `switchboard-ui`**, leading with the event-bus identity.

## Backend independence and self-hosting

The conclusion was a property to preserve, not a feature to add: the package returns a `str` and imports no framework type, so integration is a one-liner at the host edge. Two delivery modes follow, inline and linked. The consequence is that the package can render its own docs and storybook to static HTML and host them anywhere. See [Backend independence](backend-independence.md).

## Layout

**Decision: layout is a recursive flex value.** Originally built as a CSS grid: the model is literally a 3x3, so `grid-template-areas` mapped one-to-one onto the nine regions.

**Reversed to nested flex stacks** once layout became a recursive value. A recursive layout is a tree of one-dimensional stacks, which is flexbox; grid's 2D template fights nesting and over-emphasizes grid. The general primitive is `Frame` (a flex stack), sized by `Slot` and wrapped as a page by `Document`; the three-column layout is a preset built from them. See [Layout](layout.md).

## The governing rule: general mechanism, opinionated invariants

The layout decisions follow one rule. Every generalization is "one primitive, many presets," never "a configurable subsystem" that eats the small core.

`Frame` is the general mechanism (a recursive flex stack); `three_column` is a preset, an ordinary function that arranges frames and returns a `Document`, not a type co-equal with `Frame`. `Slot` adds sizing to the mechanism. The package ships layout structure only: the stylesheet sets no color, type, or theming, so a preset may be opinionated about layout while visual style stays the host application's concern. `Frame` stays layout-only; style never enters the package.

The same rule guides the forward work. A component library is a small canonical set, not a framework; a theme exposes only the legitimately-variable axes, holding the design system's invariants (square corners, a single accent color, monospace-first type) fixed. The tension is always opinionated-canonical versus general-composable, and the resolution is always: general mechanism, opinionated invariants.

## Testing stance

A design review found the browser runtime and layout invariants untested. The proposed remedy had two parts: a headless test of the runtime, and layout-invariant audits.

The honest split: behavioral tests (structural assertions, a headless DOM test, a browser smoke test) are standard; the layout-invariant audits are bespoke design-system governance, disproportionate for a small package.

**Decision: carry only the standard subset, and defer even the headless test.** The layout audits are dropped. The headless runtime test is deferred rather than rejected: adding a JavaScript test runner would be the package's first dependency, and the zero-dependency property is not spent on testing a small runtime that the demo page already exercises. The deferral is recorded rather than left as a silent gap. The testing baseline is the Python suite at full coverage.

This is why the demo is in scope and not optional: it is the runtime's exerciser. Removing it would leave the runtime both untested and unexercised.

## Corrections

**Never `if TYPE_CHECKING`.** A linter rule (Ruff's `TC` / flake8-type-checking) pushed for `if TYPE_CHECKING:` import blocks. This is rejected as a hard rule: every import is a plain runtime import. The blocks were reverted and the `TC` ruleset removed from the linter selection, because that ruleset exists specifically to mandate the banned pattern.

**Demo adapters are real files.** The demo adapters had been written as Python string blobs, which cannot be linted or served as real JavaScript. They were moved to real `static/*.js` files, and a single memoized asset reader now serves both the renderer and the demo, so packaged assets are read one way.

**The shell was demoted from a type to a preset.** `Shell` began as a dataclass co-equal with `Frame`, with its own `render_shell` path and region-classed, token-themed CSS. That made one specific three-column layout look like a core concept, pinned a generic-sounding name to a single arrangement, and let design-system opinions (chrome, tokens, theming) leak into the package. It is now `three_column`, an ordinary function that builds a `Frame` and returns a `Document`; the region names live only in `REGIONS` and the preset, and the stylesheet was cut to structural layout with no color, tokens, or theming. The package is opinionated about layout mechanism, never about visual style.

## Decisions at a glance

| Decision | Alternatives weighed |
|---|---|
| Pure-Python builders | HTML DSL library; Jinja2 |
| Mount-contract seam, vanilla first | Web-Component-only; build-step islands |
| Declarative pub/sub | hybrid store+events; federated stores |
| Pure greenfield | clean-room mining; extraction |
| Name `switchboard-ui` | `islehost`; `atoll` |
| `str` output; inline and linked modes | framework coupling (rejected on principle) |
| Layout as nested flex frames (3x3 = preset) | a single fixed CSS grid |
| Never `if TYPE_CHECKING`; drop ruff `TC` | comply with the linter |
| Testing: Python suite at full coverage | headless JS test now; layout audits |
| Demo adapters as real `static/*.js` | Python string blobs |
| Shell demoted to a `three_column` preset | a `Shell` type with its own renderer |
