# The workbench preset

`workbench` is a layout preset: a function that places islands into a nine-region arrangement and returns a [`Document`](page-model.md#document) whose root mode is `"viewport"`. It is sugar over the [`Frame`](page-model.md#frame) primitive, not a separate type, so anything it builds you could build by hand. It lives in `switchboard_ui.presets`.

It builds the page shape a user works in: a tool, dashboard, editor, or console. The page itself never scrolls; each body region owns its scroll independently. See [`document_site`](document-site.md) for the flowing shape, and [Scroll ownership](page-model.md#rootmode) for the decision between them.

```python
from switchboard_ui import Island, render_document, workbench

page = workbench(
    {
        "head-c": (Island(name="brand"),),
        "body-c": (Island(name="app"),),
        "body-r": (Island(name="inspector"),),
    },
    title="My app",
)
html = render_document(page)
```

## The nine regions

```
┌────────┬────────┬────────┐
│ head-l │ head-c │ head-r │   top rail (content-driven)
├────────┼────────┼────────┤
│ body-l │ body-c │ body-r │   middle row (flexible)
├────────┼────────┼────────┤
│ foot-l │ foot-c │ foot-r │   bottom rail (content-driven)
└────────┴────────┴────────┘
  fixed    flexible  fixed
```

The preset builds an outer **column** of three rows: content-driven head and foot rails around a flexible middle. Each row is a **row** of three cells: fixed-width sides around a flexible center. Islands are placed by region name (`head-l` through `foot-r`), the keys the `regions` argument accepts, drawn from [`REGIONS`](page-model.md#region-and-regions). An omitted region is an empty cell that collapses. The rows carry identity hooks so full-width horizontal *seams* can have one owner; see [Seams](../explanation/seams.md).

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `regions` | `Mapping[Region, Sequence[Island]] \| None` | `None` | Islands to place, keyed by region name. |
| `title` | `str` | `"switchboard-ui"` | The document `<title>`. |
| `left_width` | `str` | `"220px"` | The left column's fixed width. |
| `right_width` | `str` | `"200px"` | The right column's fixed width. |

## Scroll ownership

The three body cells declare `overflow="auto"`, so each owns its scroll independently. Every frame above them declares `overflow="clip"`, so nothing escapes the locked root and the page itself never scrolls.

`clip` rather than `hidden` is deliberate. A `hidden` box is not user-scrollable but remains *programmatically* scrollable, and the user agent uses that to bring a focused off-screen descendant into view, which shows up later as a mystery offset. `clip` creates no scroll container at all.

The independence is the shape's purpose: a tool's regions hold their own positions, and a reader's place in one region does not move because another changed. Its accepted cost is that those positions are client-held state that a forward page navigation does not carry.

An `overflow="auto"` frame reserves a stable scrollbar gutter, so a cell's inline geometry does not shift when its content grows past the fold on a platform with classic scrollbars.

## Generated markup

The preset is plain frames and slots, so it renders through [`render_document`](rendering.md#render_document) like any other layout. Every frame carries exactly one overflow policy class, emitted from its own `overflow` value, and every element is sized by an inline `flex` style from its [`Slot`](page-model.md#slot).

```html
<body class="sb-document">
<div class="sb-frame sb-frame-column sb-overflow-clip sb-root sb-root-viewport">
  <div class="sb-frame sb-frame-row sb-overflow-clip sb-rail sb-head-row">
    <div class="sb-frame sb-frame-column sb-overflow-clip sb-head-l"
         style="flex: 0 0 220px"></div>              <!-- empty: collapses -->
    <div class="sb-frame sb-frame-column sb-overflow-clip sb-head-c"
         style="flex: 1 1 0">...</div>
    <div class="sb-frame sb-frame-column sb-overflow-clip sb-head-r"
         style="flex: 0 0 200px"></div>              <!-- empty: collapses -->
  </div>
  <div class="sb-frame sb-frame-row sb-overflow-clip sb-body-row"
       style="flex: 1 1 0">...</div>
  <div class="sb-frame sb-frame-row sb-overflow-clip sb-rail sb-foot-row">...</div>
</div>
</body>
```

| Class | Role |
|---|---|
| `.sb-document` | The generated body envelope. Carries the one owned reset: the user agent's default body margin. |
| `.sb-root` + `.sb-root-viewport` | The document root and its root mode. A viewport root is `position: fixed; inset: 0`, the only rule in the structural sheet that positions anything. |
| `.sb-overflow-visible` / `-clip` / `-auto` | The frame's declared overflow policy; every frame carries exactly one. |
| `.sb-head-row`, `.sb-body-row`, `.sb-foot-row` | Row identity hooks; themes use the head and foot hooks to own full-width horizontal seams. |
| `.sb-rail` | A content-driven head or foot row with a theme-published minimum block size. |
| `.sb-<region>` | A cell's region identity (`sb-head-l` through `sb-foot-r`), a theming hook. |
| `.sb-island` | A mount point inside a cell. |

## Layout sizes

The side columns use the preset's `220px` / `200px` structural widths, overridable per call. The head and foot rows are content-driven and floored by the theme's `--sb-fit-rail-block` geometry obligation; only the middle row receives a flexible slot. For different row behavior, build your own frame tree with different [`Slot`](page-model.md#slot) bases and role classes.

## A locked root needs a scroll owner

A viewport root never scrolls at the page level, so anything past the viewport is reachable only through a descendant that declared `overflow="auto"`. A tree of `clip` and `visible` frames under a locked root renders content that cannot be reached by scrolling, by keyboard, or by the user agent's own scroll-into-view.

Each frame's policy is valid in isolation, so this cannot be a type error; it is a property of the whole tree. [`unreachable_content`](analyzer.md) reports it.

## The stylesheet is structure only

The packaged stylesheet (`switchboard_ui/static/layout.css`) carries layout structure only: the flex rules that make a frame tree render, the overflow policies, the two root modes, an empty-cell collapse, and the envelope's margin reset. It sets no color, type, theming, or design tokens. Visual style is the host application's to add.

## Dressing a region

The shipped theme sheet paints components, never regions: a region is part of this structural vocabulary, and the theme is held to insetting none of it. Chrome that dresses a region therefore ships as an opt-in helper the host inlines in `extra_head`, beside the theme:

| Helper | Region | What it paints |
|---|---|---|
| `switchboard_theme.chrome.content_column_styles()` | `body-c` | The document shape: both inline seams, the column's square inset, one gap between islands, and an island cap at `--sb-fit-content-inline`. Anchored elements clear the scroll owner's top edge. |
| `switchboard_theme.modes.mode_switch_styles()` | `head-r` | The mode switch's rail chrome: the cell as an end-aligned row, plus the trigger and panel. |

A page with a different shape (a gallery filling the viewport width) simply omits the helper, or overrides the few declarations after it. Nothing here is load-bearing: the layout stands up unpainted.
