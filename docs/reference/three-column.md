# Reference: the three-column preset

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
│ head-l │ head-c │ head-r │   top row (fixed height)
├────────┼────────┼────────┤
│ body-l │ body-c │ body-r │   middle row (flexible)
├────────┼────────┼────────┤
│ foot-l │ foot-c │ foot-r │   bottom row (fixed height)
└────────┴────────┴────────┘
  fixed    flexible  fixed
```

The preset builds an outer **column** of three rows: a fixed-height top and bottom around a flexible middle. Each row is a **row** of three cells: fixed-width sides around a flexible center. Islands are placed by region name (`head-l` through `foot-r`), the keys the `regions` argument accepts, drawn from [`REGIONS`](page-model.md#region-and-regions). An omitted region is an empty cell that collapses. The lines between regions are *seams*; see [Seams](../explanation/seams.md) for how each is drawn exactly once.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `regions` | `Mapping[Region, Sequence[Island]] \| None` | `None` | Islands to place, keyed by region name. |
| `title` | `str` | `"switchboard-ui"` | The document `<title>`. |

## Generated markup

The preset is plain frames and slots, so it renders through [`render_document`](rendering.md#render_document) like any other layout. Every element is an `sb-frame`, sized by an inline `flex` style from its [`Slot`](page-model.md#slot). Each cell also carries an `sb-<region>` class: a theming hook the packaged CSS leaves unpainted, so a host stylesheet can target one region without the preset imposing any look.

```html
<div class="sb-frame sb-frame-column sb-root">
  <div class="sb-frame sb-frame-row" style="flex: 0 0 2.5rem">                       <!-- head row -->
    <div class="sb-frame sb-frame-column sb-head-l" style="flex: 0 0 220px"></div>  <!-- empty: collapses -->
    <div class="sb-frame sb-frame-column sb-head-c" style="flex: 1 1 0">...</div>
    <div class="sb-frame sb-frame-column sb-head-r" style="flex: 0 0 200px"></div>  <!-- empty: collapses -->
  </div>
  <div class="sb-frame sb-frame-row" style="flex: 1 1 0">...</div>                   <!-- body row -->
  <div class="sb-frame sb-frame-row" style="flex: 0 0 2.5rem">...</div>              <!-- foot row -->
</div>
```

| Class | Role |
|---|---|
| `.sb-frame` + `.sb-frame-row` / `.sb-frame-column` | A flex stack and its axis. |
| `.sb-root` | The document root frame, sized to the viewport. |
| `.sb-<region>` | A cell's region identity (`sb-head-l` through `sb-foot-r`), a theming hook. |
| `.sb-island` | A mount point inside a cell. |

## Layout sizes

The rails are sized with plain CSS lengths, not design tokens: a `2.5rem` row height and `220px` / `200px` side columns, emitted as inline `flex` styles. These are layout values the preset owns. For different sizes, build your own frame tree with different [`Slot`](page-model.md#slot) bases.

## The stylesheet is structure only

The packaged stylesheet (`switchboard_ui/static/layout.css`) carries layout structure only: the flex rules that make a frame tree render, an empty-cell collapse, a viewport-filling root, and an island block. It sets no color, type, theming, or design tokens. Visual style is the host application's to add.
