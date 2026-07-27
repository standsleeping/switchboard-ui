# The document-site preset

`document_site` is a layout preset: a function that places islands into a nine-region arrangement and returns a [`Document`](page-model.md#document) whose root mode is `"flow"`. It is sugar over the [`Frame`](page-model.md#frame) primitive, not a separate type, so anything it builds you could build by hand. It lives in `switchboard_ui.presets`.

It builds the page shape a reader reads: an article, a documentation site, generated reference. The page itself is the primary scroll owner. See [`workbench`](workbench.md) for the viewport-locked shape, and [Scroll ownership](page-model.md#rootmode) for the decision between them.

```python
from switchboard_ui import Island, document_site, render_document

page = document_site(
    {
        "head-c": (Island(name="brand"),),
        "body-l": (Island(name="site-nav"),),
        "body-c": (Island(name="article"),),
        "body-r": (Island(name="on-this-page"),),
        "foot-c": (Island(name="status"),),
    },
    title="Reference",
)
html = render_document(page)
```

## The nine regions

```
┌────────┬────────┬────────┐
│ head-l │ head-c │ head-r │   top rail (content-driven)
├────────┼────────┼────────┤
│ body-l │ body-c │ body-r │   body row (grows into slack)
├────────┼────────┼────────┤
│ foot-l │ foot-c │ foot-r │   bottom rail (content-driven)
└────────┴────────┴────────┘
  sticky   flowing   sticky
```

Islands are placed by region name (`head-l` through `foot-r`), the keys the `regions` argument accepts, drawn from [`REGIONS`](page-model.md#region-and-regions). An omitted region is an empty cell that collapses. The rows carry identity hooks so full-width horizontal *seams* can have one owner; see [Seams](../explanation/seams.md).

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `regions` | `Mapping[Region, Sequence[Island]] \| None` | `None` | Islands to place, keyed by region name. |
| `title` | `str` | `"switchboard-ui"` | The document `<title>`. |
| `left_width` | `str` | `"220px"` | The left rail's fixed width. |
| `right_width` | `str` | `"200px"` | The right rail's fixed width. |

## Scroll ownership

The center column declares `overflow="visible"`, so a long article extends the page and the page scrolls it. The reader's position therefore lives in the document, which is where the browser's own scroll restoration, find-in-page, and fragment anchors operate.

The two side cells declare `overflow="auto"` and carry `sb-sticky-rail`. Each stays in view as the article scrolls past it, and scrolls within itself only when it is taller than the screen. They are the only contained scrollers on the page.

An `overflow="auto"` frame reserves a stable scrollbar gutter, so a rail's inline geometry does not shift when its content grows past the fold on a platform with classic scrollbars.

## Generated markup

The preset is plain frames and slots, so it renders through [`render_document`](rendering.md#render_document) like any other layout. Every frame carries exactly one overflow policy class, emitted from its own `overflow` value.

```html
<body class="sb-document">
<div class="sb-frame sb-frame-column sb-overflow-visible sb-root sb-root-flow">
  <div class="sb-frame sb-frame-row sb-overflow-clip sb-rail sb-head-row">...</div>
  <div class="sb-frame sb-frame-row sb-overflow-visible sb-body-row sb-flow-body">
    <div class="sb-frame sb-frame-column sb-overflow-auto sb-body-l sb-sticky-rail"
         style="flex: 0 0 220px">...</div>
    <div class="sb-frame sb-frame-column sb-overflow-visible sb-body-c"
         style="flex: 1 1 0">...</div>
    <div class="sb-frame sb-frame-column sb-overflow-auto sb-body-r sb-sticky-rail"
         style="flex: 0 0 200px">...</div>
  </div>
  <div class="sb-frame sb-frame-row sb-overflow-clip sb-rail sb-foot-row">...</div>
</div>
</body>
```

| Class | Role |
|---|---|
| `.sb-document` | The generated body envelope. Carries the one owned reset: the user agent's default body margin. |
| `.sb-root` + `.sb-root-flow` | The document root and its root mode. A flow root is content-sized with a floor of `100svb`, so a short page still fills the screen. |
| `.sb-flow-body` | The body row, `flex: 1 1 auto`: it takes the slack a short page leaves so the foot rail sits at the bottom, while its own content still sizes it. |
| `.sb-sticky-rail` | A side column that stays in view as the page scrolls past, capped at `100svb` and aligned to the start so its row cannot stretch it. |
| `.sb-overflow-visible` / `-clip` / `-auto` | The frame's declared overflow policy; every frame carries exactly one. |
| `.sb-head-row`, `.sb-body-row`, `.sb-foot-row` | Row identity hooks; themes use the head and foot hooks to own full-width horizontal seams. |
| `.sb-rail` | A content-driven head or foot row with a theme-published minimum block size. |
| `.sb-<region>` | A cell's region identity (`sb-head-l` through `sb-foot-r`), a theming hook. |
| `.sb-island` | A mount point inside a cell. |

## Why the body row is not a flexible slot

Both presets give the center column a flexible [`Slot`](page-model.md#slot) along the *inline* axis, where the row's width is definite. Along the block axis they differ.

A workbench wraps its body row in a `Slot`, which renders `flex: 1 1 0`. That is correct when the root height is definite: the row takes exactly the leftover viewport space.

A document site does not. Its root is content-sized, and a zero basis contributes nothing to an auto-height column's intrinsic size, so the row would be sized from leftover viewport space and a long article would be crushed into it rather than extending the page. The row instead carries `sb-flow-body` for `flex: 1 1 auto`: it grows into slack, but its basis is its own content.

## The stylesheet is structure only

The packaged stylesheet (`switchboard_ui/static/layout.css`) carries layout structure only: the flex rules that make a frame tree render, the overflow policies, the two root modes, the sticky-rail role, an empty-cell collapse, and the envelope's margin reset. It sets no color, type, theming, or design tokens. Visual style is the host application's to add.

One consequence is worth naming: a background on a `div` propagates to nothing, so under a flow root the areas the root frame does not cover (the elastic overscroll region at the top and bottom of a rubber-band scroll) are painted by the user agent unless a theme paints the canvas on the root element. The shipped theme does.

## Dressing a region

The shipped theme sheet paints components, never regions: a region is part of this structural vocabulary, and the theme is held to insetting none of it. Chrome that dresses a region therefore ships as an opt-in helper the host inlines in `extra_head`, beside the theme:

| Helper | Region | What it paints |
|---|---|---|
| `switchboard_theme.chrome.content_column_styles()` | `body-c` | The document shape: both inline seams, the column's square inset, one gap between islands, and an island cap at `--sb-fit-content-inline`. Anchored elements clear the scroll owner's top edge. |
| `switchboard_theme.modes.mode_switch_styles()` | `head-r` | The mode switch's rail chrome: the cell as an end-aligned row, plus the trigger and panel. |

A page with a different shape simply omits the helper, or overrides the few declarations after it. Nothing here is load-bearing: the layout stands up unpainted.
