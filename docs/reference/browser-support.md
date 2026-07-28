# Browser support

The structural layer uses four platform features that are newer than the rest of what it relies on. Each is listed with what it does, what happens without it, and whether the package compensates.

The package does not feature-detect, polyfill, or branch on any of them. Every one degrades to something readable, which is the condition for using a feature this way at all.

| Feature | Used for | Without it |
|---|---|---|
| `overflow: clip` | Containment that creates no scroll container | Falls back to the UA's handling of an unknown value, i.e. `visible`. Content that should be clipped is painted outside its frame. |
| `scrollbar-gutter: stable` | Reserving a classic scrollbar's width so a column's inline geometry does not move | The declaration is ignored. On a classic-scrollbar platform the intermittent shift returns; on an overlay-scrollbar platform there was nothing to reserve and nothing changes. |
| `position: sticky` on a flex child | Side rails that stay in view as the article scrolls past | The rail scrolls away with the page. The nav still works; it is simply not persistent. |
| Small viewport units (`svb`) | The flow root's floor and the sticky rail's cap | The length is invalid and ignored, so the root loses its minimum height and the rail loses its cap. A rail taller than the screen runs past the bottom instead of scrolling within itself. |

## Notes on two of them

**`clip` is chosen over `hidden` deliberately**, and the difference matters more than the support question. A `hidden` box is not user-scrollable but stays *programmatically* scrollable, and the user agent uses that to scroll a focused off-screen descendant into view — which surfaces later as an unexplained offset with no visible scrollbar to explain it. `clip` creates no scroll container, so that cannot happen. The tradeoff is that content in a clipped frame is genuinely unreachable, which [`unreachable_content`](analyzer.md#unreachable_content) exists to report.

**`svb`, not `dvb`.** The dynamic viewport units resize as mobile browser chrome collapses and expands during a scroll, so a length written in one has a mid-scroll geometry change built into the unit — the exact defect class this layer exists to eliminate. The small viewport unit is the always-visible area and never changes while the reader scrolls. A static guard rejects the dynamic units in structural values.

## The scrollbar stance

A scroll container uses `overflow: auto`, and the platform paints its own bar, themed by `color-scheme` on the root. The package never hides, tints, or resizes it.

Reserving the space that bar will occupy is a different thing from styling it: the platform still paints, sizes, and themes the bar, and the user's OS scrollbar preference is untouched. A gutter exists only where a classic scrollbar exists, so the reservation is inert under overlay scrollbars and converts an intermittent inline shift into a constant inset under classic ones.

This matters for testing more than it looks. macOS uses overlay scrollbars by default, so a developer working there never sees the shift they ship. Set "Show scroll bars: Always" in system settings, or attach a mouse, to make the classic behaviour observable.

## The progressive enhancement

Rail scroll persistence ([`nav(scroll_key=...)`](components.md)) needs `sessionStorage` and an inline script.

Storage access is guarded, since it throws in a private or blocked context. A strict Content-Security-Policy without `'unsafe-inline'` or a nonce blocks the inline script; the package emits no nonce, so the enhancement is lost silently and the rail starts at the top, exactly as it would without the feature.

In both cases the nav is fully readable and every link is a real link.

## See also

- [The page model](page-model.md) — `Overflow` and `RootMode`
- [Scroll ownership and navigation state](../explanation/scroll-ownership.md)
- [Design philosophy](../explanation/philosophy.md) — the leak classes these boundaries belong to
