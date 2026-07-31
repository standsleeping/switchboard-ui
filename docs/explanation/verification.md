# Verification

How the package is tested: four rungs, each one step further from the code and one step closer to what a reader experiences. Anything provable without executing layout stays on the first rung; anything that needs a real engine moves down, and only what needs Apple's own browser reaches the bottom. The rung above never substitutes for the one below, and the one below never re-proves what the one above already settled.

## The four rungs

| Rung | Command | What it proves | Needs |
|---|---|---|---|
| Fast gate (`tests/`, theme tests) | `just check` | The structural contracts, at 100% branch coverage, plus the static guards: the layer never styles the scrollbar, never animates scrolling, and no shipped script requests smooth scrolling. | Nothing |
| Browser suite (`tests_browser/`) | `just browser-test` | Behaviour in Chromium, Firefox, and WebKit: scroll ownership, rail continuity, first-paint restoration, keyboard traversal, anchor landings, font loading, viewport widths, canvas colour, and classic-scrollbar geometry. | `just browser-install` once |
| Real Safari (`tests_safari/`) | `just safari-test` | The same shipped assembly in the engine Safari actually ships, including a Back navigation that Safari may serve from its back/forward cache. | macOS, `safaridriver --enable` once |
| Eyes | — | The perceptual residue: how the focus ring is drawn, how rubber-band overscroll looks, whether anything reads as a jump. The measurable halves of each are guarded on the rungs above. | Ordinary use |

The browser suites run against a stdlib fixture server rather than the showcase's, so a case controls exactly what it serves and how fast; the pages it serves are built from the same `document_site`, `workbench`, and component factories an application uses, so the cases exercise the shipped assembly rather than a copy of it. The Safari harness imports that same server and those same pages.

## When each rung runs

| Trigger | check | browser | safari |
|---|---|---|---|
| Pull request | runs | runs | — |
| Manual dispatch | runs | runs | runs |

CI calls the same `just` targets a developer runs locally, so green in one place means green in the other. The Safari job runs only on dispatch: the engine under test changes on the runner image's cadence, not the repository's, and macOS minutes are the expensive pool. A dispatch also reruns the fast jobs, which revalidates the whole gate against runner-image drift.

Two configurations differ between a development machine and CI, and both differences are load-bearing:

**Classic scrollbars.** The gutter-reservation cases can only fail where a scrollbar takes real space, and overlay bars are the default nearly everywhere now: on macOS, and on modern GTK desktops too. The gutter cases therefore launch their engines with the classic-bar switch each engine offers (a Chromium feature flag, a Firefox preference; WebKit offers none), and the probe still makes the final call: wherever the switch takes — the CI runners included — the cases bite, and wherever the platform imposes overlay bars anyway, they skip, each naming why. A failure there has no local reproduction by construction, which is why the browser job uploads every failing case's screenshot and trace as artifacts: for those cases the artifact is the whole report.

**Real input.** The keyboard cases use trusted key events, so focus traversal, activation, and the restoration-takeover keypress are the browser's own behaviour rather than synthesized events dispatched at it.

## What a green run means

The suites are built so that a pass cannot be vacuous:

**Probes decide, not assumptions.** Every classic-scrollbar case first measures the platform's bar and skips, by name, when there is nothing to test. The viewport-gutter case likewise probes whether the engine applies the root's declaration at all, so the guard strengthens by itself when an engine's behaviour changes.

**Preconditions before assertions.** Cases assert their own setup — the short page must fit the viewport, the rail must overflow — so a fixture drifting out of shape fails loudly instead of passing emptily.

**Allowances are exact shapes.** Engine behaviour the package cannot change is tolerated as an expected failure matching precisely its signature, never as a loosened assertion. Anything outside the named shape still fails. The named shapes are listed in [browser support](../reference/browser-support.md) and beside the code they concern.

**Silent breakage is loud.** Every browser case fails if its page throws an uncaught exception or logs a console error, in whichever engine logged it.

**Failures carry their evidence.** A failing browser case leaves its screenshot and full trace under `test-results/`, locally and in CI.

## Engine boundaries

Running one contract in four engines surfaces the places the engines genuinely differ. Each known boundary is named where the next person will look: the root-level `scrollbar-gutter` gap in [browser support](../reference/browser-support.md), the warm-load font promotion beside the font policy in the theme's `font_head`, and the keyboard-traversal differences (WebKit walks links with Option+Tab, as shipping Safari does; Firefox may leave an already-peeking focus target a few pixels short of fully revealed) in the keyboard cases themselves, whose assertions state the contract that actually holds everywhere: focus is never on a row the reader cannot see.
