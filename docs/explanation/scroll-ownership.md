# Scroll ownership and navigation state

Every page has to answer one question: what scrolls? The answer is not a styling detail. It decides where the reader's position lives, and therefore which of the browser's own behaviors can look after it.

## Two shapes, one question

A page is a *document* or a *workbench*, and it says which in [`Document.root`](../reference/page-model.md#rootmode).

In a document the page itself scrolls. The reader's position lives in the document, which is where the browser's scroll restoration, find-in-page, fragment anchors, and overscroll all operate. The chrome rails stay at the top and bottom of the viewport while the article passes under them; the side rails stick beneath the head rail, sized to the window between the chrome, and they are the only contained scrollers.

```
┌──────────────────────────────────────┐
│ head rail                            │   stays at the top
├────────┬───────────────────┬─────────┤
│ nav    │ article           │ toc     │
│ sticky │ ...               │ sticky  │   the PAGE scrolls
│ window │ ...               │ window  │   the rails fill the window
│ -sized │ ...               │ -sized  │   between the chrome rails
├────────┴───────────────────┴─────────┤
│ foot rail                            │   stays at the bottom
└──────────────────────────────────────┘
```

In a workbench the page never scrolls. The root is fixed to the viewport, every frame above a scrolling leaf clips, and named regions own their scroll independently.

```
┌──────────────────────────────────────┐
│ head rail                     clip   │
├────────┬───────────────────┬─────────┤
│ nav    │ centre            │ inspect │
│ auto ▲ │ auto ▲            │ auto ▲  │   each REGION scrolls
│      ▼ │      ▼            │      ▼  │   the page never does
├────────┴───────────────────┴─────────┤
│ foot rail                     clip   │
└──────────────────────────────────────┘
```

Choose the workbench when the page is a tool whose regions hold independent state, and the document when it is something a reader reads from top to bottom.

## Why the shape decides who keeps your place

The browser restores what it owns. On a back or forward traversal it restores the whole page, and on a back/forward-cache traversal it restores the live DOM including element scroll positions. What it does not do is carry an *element's* scroll offset into a freshly built document, because that document is new and the element in it has never been scrolled.

That is the whole of the boundary, and the shape decides how much of it you feel.

In a document the article's position is the page's position, so a forward navigation to a new article correctly starts at the top, and a back navigation correctly returns you to where you were. Nothing to arrange.

In a workbench every region's position is client-held state, and none of it survives a forward load. That is the accepted cost of independent regions, not a bug to fix: regions hold their own positions precisely so that changing one does not move another.

## The one piece worth carrying

A long navigation rail that is the same on every page is the case where the boundary hurts, in either shape. The reader scrolls the rail, clicks a link they can see, and the next page rebuilds the rail at zero — so the thing they were using to navigate has forgotten the navigating they just did.

`nav(scroll_key=...)` carries exactly that one offset, and nothing else. Not a general state store, not a router, not an interception of the click. The links stay real links, history stays native, and the remedy stays the size of the problem: one number, per tab, for one rail.

Two behaviors fall out of it, and which one applies depends on whether the reader has been here before in this tab.

**Restore.** A stored offset means the reader has a position in the rail. Put it back, before the rail is painted complete, so there is no visible correction.

**Reveal.** No stored offset means a first visit — a deep link, a search result, a shared URL. The rail opens at the top, and on a long rail the page the reader actually landed on can be far below the fold, so the nav says nothing about where they are. Scroll by the smallest amount that brings the current item into view, and leave an already-visible item alone.

Both stand down the moment the reader scrolls. A reader who has said where they want to be outranks a stored offset; continuing to place the rail would be the same defect in the other direction.

See [the browser runtime](../reference/browser-runtime.md#rail-scroll-persistence) for how the two halves are split and why.

## Reading a scroll bug

The shape tells you where to look.

| Symptom | Where the answer is |
|---|---|
| The page scrolls when it should not | the document's root mode; a workbench should be `"viewport"` |
| A region will not scroll | that frame's own `overflow` value; only `"auto"` scrolls |
| Content is unreachable entirely | a locked root with no `"auto"` descendant — [`unreachable_content`](../reference/analyzer.md#unreachable_content) reports it |
| A rail stretches instead of sticking | the sticky role's `align-self`; a stretched flex child has nothing to stick within |
| A rail forgets its position across pages | a missing `scroll_key`, or a Content-Security-Policy blocking the inline script |
| A column shifts when content grows | a scroll container without a reserved gutter, on a classic-scrollbar platform |

## See also

- [Layout](layout.md) — the frame primitive and the two presets
- [The page model](../reference/page-model.md) — `RootMode`, `Overflow`, and the values that carry them
- [Design philosophy](philosophy.md) — the leak classes this boundary belongs to
