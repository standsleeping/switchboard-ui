# Reference: the shell layout

The shell is one preset of the [`Frame`](page-model.md#frame) primitive, defined in `switchboard_ui/static/shell.css`. It is a set of nested flex stacks: an outer column of three rows, each row a flex row of three region cells. This page documents the CSS contract; for the design rationale see [Layout](../explanation/layout.md).

## The nine regions

```
┌────────┬────────┬────────┐
│ head-l │ head-c │ head-r │   top rail (chrome)
├────────┼────────┼────────┤
│ body-l │ body-c │ body-r │   the three columns; only this row scrolls
├────────┼────────┼────────┤
│ foot-l │ foot-c │ foot-r │   bottom rail (chrome)
└────────┴────────┴────────┘
   rail     main    rail
```

The shell is an outer **column** of three rows:

- `head`: a fixed-height chrome rail.
- `body`: the flexible row; its cells scroll.
- `foot`: a fixed-height chrome rail.

Each row is a flex **row** of three cells (`l`, `c`, `r`). The names match `model.REGIONS` exactly; a test (`tests/test_shell_css.py`) fails if the Python names and the stylesheet's region classes ever disagree.

## Generated markup

`render_shell` emits nested flex `<div>`s:

```html
<div class="sb-frame sb-frame-column sb-shell">
  <div class="sb-frame sb-frame-row sb-head">
    <div class="sb-region sb-head-l" data-region="head-l">...</div>
    <div class="sb-region sb-head-c" data-region="head-c">...</div>
    <div class="sb-region sb-head-r" data-region="head-r">...</div>
  </div>
  <div class="sb-frame sb-frame-row sb-body">
    <div class="sb-region sb-body-l" data-region="body-l">...</div>
    <div class="sb-region sb-body-c" data-region="body-c">
      <div class="sb-island" data-island="app">...</div>
    </div>
    <div class="sb-region sb-body-r" data-region="body-r">...</div>
  </div>
  <div class="sb-frame sb-frame-row sb-foot">...</div>
</div>
```

| Class | Role |
|---|---|
| `.sb-frame` + `.sb-frame-row` / `.sb-frame-column` | A flex stack and its axis. |
| `.sb-shell` | The outer column, locked to the viewport. |
| `.sb-head` / `.sb-body` / `.sb-foot` | The three rows. |
| `.sb-region` + `.sb-{region}` | A region cell. |
| `.sb-island` | A mount point inside a cell. |

This is the same structure `render_frame` produces for any [`Frame`](page-model.md#frame); the shell is one preset arrangement of it.

## Sizing

Rows and columns are sized with flex, from tokens with standalone fallbacks so the shell works with no host.

| Track | Sizing | Token | Fallback |
|---|---|---|---|
| Chrome rail height (`head`, `foot`) | `flex: 0 0` | `--layout-chrome-bar-h` | `2.5rem` |
| Body row | `flex: 1 1 0` | takes the remaining height | — |
| Left cell (`*-l`) | `flex: 0 0` | `--sb-rail-l` / `--layout-sidebar-width` | `220px` |
| Right cell (`*-r`) | `flex: 0 0` | `--sb-rail-r` / `--layout-toc-width` | `200px` |
| Center cell (`*-c`) | `flex: 1 1 0` | takes the remaining width | — |

Column widths are applied to all three rows, so the rails stay aligned with the body columns (`PEER_RAIL`). When the design system's tokens are present, the shell inherits them; when absent, the fallbacks apply.

## Behavior

**Every viewport edge is chrome.** The top and bottom rails and the left and right cells frame the center, so the single elastic main region (`body-c`) never touches the viewport edge.

**The page never scrolls; the columns do.** The shell is locked to the viewport (`100dvh`) and clips. Vertical scrolling is delegated to the `body` cells (`body-l`, `body-c`, `body-r`). Horizontal scrolling belongs to leaf elements inside a cell.

**Empty cells collapse.** A cell always renders, holding its geometry at first paint, but `.sb-region:empty` sets `display: none`, so an unused cell leaves no gap. One shell serves many layouts.

## Theming

The stylesheet sets `color-scheme: light dark` on `:root` and reads color tokens (`--color-bg`, `--color-text`, `--color-surface`, `--color-border`, `--color-accent`) with light/dark fallbacks. Provide the design system's `tokens.css` to override the fallbacks.
