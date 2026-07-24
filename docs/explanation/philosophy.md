# Design philosophy

Two commitments run under every layer of this package: align with the browser, and enumerate what leaks. They predate any individual component, and new work is measured against them.

## Align with the browser

The browser is the platform, not an obstacle. Where the platform already provides a behavior, the package uses it and shapes its own layers around it, instead of reimplementing it in script and CSS. The platform's version is specified, accessible, maintained by someone else, and already installed.

This is not an aspiration; it is how the package is built today:

- **Navigation is native.** Pages are real URLs and links are `<a>` elements. History, middle-click, prefetching, and the back/forward cache's scroll restoration all work because nothing intercepts the click.
- **The popover panel is a native `[popover]`.** Top-layer promotion, light dismiss, and the escape key come from the UA, not from a positioning library.
- **State semantics are the styling hooks.** The current page is `aria-current="page"`; the theme styles the semantic attribute rather than inventing a parallel class. What the assistive stack reads and what the eye sees cannot drift apart.
- **In-page tables of contents are plain anchors.** The scroll owner follows them natively; there is no scroll-management script.
- **Color scheme is the platform's.** Scheme-varying tokens use `light-dark()`, `color-scheme` sits on the root, and the native scrollbar is themed by it and never rebuilt.
- **Focus is `:focus-visible`.** The heuristic for when a ring should appear belongs to the UA.

The rule for future work follows from the record: when the platform grows a capability that covers a hand-rolled behavior, adopting the native one is the default direction, and the bar for reimplementing something is *the platform does not offer it* — never *the platform's version takes effort to style*.

Aligning with the browser also bounds costs. When a design accepts a platform boundary — a full page load resets client-held state — the platform states that boundary precisely: back/forward restores what the user had, a forward click starts fresh. A precise boundary makes the remedy small and local (persist the state, restore it on load), because the fix works with the grain of navigation instead of replacing navigation to avoid it.

## Every abstraction leaks; enumerate the leaks

Every abstraction leaks. The measure of a design is not whether it has leak classes but whether each class is small, named, and guarded. That is two duties, and the second is the one most designs skip.

**Keep each class small.** Boundaries are chosen so that what can go wrong is bounded and nameable. "Client-held state in shared chrome does not survive a page load" is a class you can write on one line and inventory in one sitting. "The framework and the app disagree about who owns the DOM" is not, and boundaries that would create classes like it are rejected.

**Enumerate with the strongest guard the class admits.** The guards form a ladder, and each class is pushed to the highest rung it can reach:

1. **Inexpressible at authoring time.** Components validate at the call site and raise where the mistake is written: an empty option list, a value not among the options, a blank accessible name. A malformed page fails in the author's editor, not in the reader's browser.
2. **Mechanically guarded in tests.** The contract tests discover every component stylesheet automatically — no registration step to forget — and hold each one to the structural contract (geometry only, token-free, `.sb-*` selectors only). The paint-side policy is enforced the same way: a state rule may repaint but never reshape. Generated CSS is diffed against its source of truth so hand-edits cannot drift. The analyzer makes island wiring a static property of the rendered page, checkable without running it.
3. **Documented as a named tradeoff.** When a class cannot be mechanized, the explanation docs record the tradeoff and enumerate its members, so the class is at least written down where the next person will look before they rediscover it the hard way.

"We'll be careful" is rung zero, and it is not an acceptable resting place for a known class. A new abstraction or accepted tradeoff ships with its leak class named and a guard chosen; a bug that arrives from an unnamed class is two findings, not one — the bug, and the missing enumeration.

The two commitments reinforce each other. Aligning with the browser keeps classes small, because the platform's behavior is a specification someone else maintains and every deviation from it is a class you now own. Enumeration catches what remains, because even a well-chosen boundary leaks somewhere — and when it does, the class it belongs to should already have a name.
