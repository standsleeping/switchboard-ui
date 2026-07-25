# The three-column preset

`three_column` is a layout preset: a function that places islands into a nine-region arrangement and returns a [`Document`](page-model.md#document). It is sugar over the [`Frame`](page-model.md#frame) primitive, not a separate type, so anything it builds you could build by hand. It lives in `switchboard_ui.presets`.

```python
from switchboard_ui import Island, render_document, three_column

page = three_column(
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

## Generated markup

The preset is plain frames and slots, so it renders through [`render_document`](rendering.md#render_document) like any other layout. Every element is an `sb-frame`, sized by an inline `flex` style from its [`Slot`](page-model.md#slot). Each cell also carries an `sb-<region>` class: a theming hook the packaged CSS leaves unpainted, so a host stylesheet can target one region without the preset imposing any look.

```html
<div class="sb-frame sb-frame-column sb-root">
  <div class="sb-frame sb-frame-row sb-rail sb-head-row">                            <!-- head row -->
    <div class="sb-frame sb-frame-column sb-head-l" style="flex: 0 0 220px"></div>  <!-- empty: collapses -->
    <div class="sb-frame sb-frame-column sb-head-c" style="flex: 1 1 0">...</div>
    <div class="sb-frame sb-frame-column sb-head-r" style="flex: 0 0 200px"></div>  <!-- empty: collapses -->
  </div>
  <div class="sb-frame sb-frame-row sb-body-row" style="flex: 1 1 0">...</div>       <!-- body row -->
  <div class="sb-frame sb-frame-row sb-rail sb-foot-row">...</div>                  <!-- foot row -->
</div>
```

| Class | Role |
|---|---|
| `.sb-frame` + `.sb-frame-row` / `.sb-frame-column` | A flex stack and its axis. |
| `.sb-root` | The document root frame, sized to the viewport. |
| `.sb-head-row`, `.sb-body-row`, `.sb-foot-row` | Row identity hooks; themes use the head and foot hooks to own full-width horizontal seams. |
| `.sb-rail` | A content-driven head or foot row with a theme-published minimum block size. |
| `.sb-scroll` | A scroll owner: overrides a frame's default clip with `overflow: auto`. The preset marks the three body cells. |
| `.sb-<region>` | A cell's region identity (`sb-head-l` through `sb-foot-r`), a theming hook. |
| `.sb-island` | A mount point inside a cell. |

## Layout sizes

The side columns use the preset's `220px` / `200px` structural widths. The head and foot rows are content-driven and floored by the theme's `--sb-fit-rail-block` geometry obligation; only the middle row receives a flexible slot. For different column widths or row behavior, build your own frame tree with different [`Slot`](page-model.md#slot) bases and role classes.

## The stylesheet is structure only

The packaged stylesheet (`switchboard_ui/static/layout.css`) carries layout structure only: the flex rules that make a frame tree render, an empty-cell collapse, a viewport-filling root, and an island block. It sets no color, type, theming, or design tokens. Visual style is the host application's to add.

## Dressing a region

The shipped theme sheet paints components, never regions: a region is part of this structural vocabulary, and the theme is held to insetting none of it. Chrome that dresses a region therefore ships as an opt-in helper the host inlines in `extra_head`, beside the theme:

| Helper | Region | What it paints |
|---|---|---|
| `switchboard_theme.chrome.content_column_styles()` | `body-c` | The document shape: both inline seams, the column's square inset, one gap between islands, and an island cap at `--sb-fit-content-inline`. Anchored elements clear the scroll owner's top edge. |
| `switchboard_theme.modes.mode_switch_styles()` | `head-r` | The mode switch's rail chrome: the cell as an end-aligned row, plus the trigger and panel. |

A page with a different shape (a gallery filling the viewport width) simply omits the helper, or overrides the few declarations after it. Nothing here is load-bearing: the layout stands up unpainted.
