# Components

The package ships a small canonical set of components as island factories in `switchboard_ui.components`. Each factory returns an [`Island`](page-model.md#island) carrying server-rendered markup; the theme paints it and an adapter (where present) adds behavior. The set proves the pattern and covers common application surfaces; it is not an exhaustive component framework. Each component carries no baked visual opinion and reads all appearance from [`--sb-*` tokens](tokens.md).

Import from the submodule:

```python
from switchboard_ui.components import segmented, table, code_block
```

## What a component ships

A component is up to four parts (see [Write an island adapter](../how-to/write-an-island-adapter.md#the-four-parts-of-a-component)). The factory always exists; the other parts are opt-in helpers beside it:

- `<name>_scripts() -> tuple[str, ...]` returns the adapter JavaScript to pass as `extra_scripts`.
- `<name>_styles() -> str` returns the structural CSS to pass in `extra_head`.

A purely static component (no behavior) has no `_scripts()`; a component with no markup of its own (`theme_state`) has no `_styles()`.

All factory arguments are keyword-only and validated at construction: bad input raises `ValueError` at the call site, not inside rendering. Arguments documented as raw-HTML fragments (`trigger`, `panel`, `body`, and `Cell`) are trusted and emitted verbatim, the same trust model as [`Island.initial`](page-model.md#island).

## Controls

Interactive components. Each publishes its value on a `topic` you choose, so other islands react over the [bus](browser-runtime.md). Each also takes an optional `listen` topic it follows: a value published there is applied in place — the selection moves, the thumb slides, the swatch repaints — without stealing focus and without republishing. An applied value is synced state, not user input, so two controls may follow each other (each listening to the other's `topic`) with no echo loop. The subscription is declared on the island (`data-sub`), so the analyzer sees the edge.

### `segmented`

```python
def segmented(*, topic: str, options: Sequence[tuple[str, str]], value: str, label: str, listen: str | None = None) -> Island
```

Pick one of `options` (each a `(value, label)` pair) and publish its value on `topic`. The markup is a radio group (`role="radiogroup"` of `role="radio"` options with roving `tabindex`), not a tab list, because a single-select that emits a value owns no `tabpanel` to control. `label` is the group's required accessible name. Raises `ValueError` if `options` is empty, `label` is blank, or `value` is not among the options. Companions: `segmented.js`, `segmented.css`.

### `color_input`

```python
def color_input(*, topic: str, value: str, label: str, listen: str | None = None) -> Island
```

A tokenised replacement for `<input type="color">`: a swatch plus a `#rrggbb` hex field, publishing the hex on `topic`. Raises `ValueError` if `value` is not a six-digit hex or `label` is blank. Companions: `color-input.js`, `color-input.css`.

### `color_picker`

```python
def color_picker(*, topic: str, value: str, label: str, listen: str | None = None) -> Island
```

A visual picker: a swatch that opens a spectrum popover (a saturation/brightness area plus a hue slider) alongside the inline hex field, all publishing the chosen `#rrggbb` on `topic`. It composes [`popover`](#popover), so include `popover_scripts()` and `popover_styles()` as well as its own. Same validation as `color_input`. Companions: `color-picker.js`, `color-picker.css` (plus the popover's).

### `slider`

```python
def slider(*, topic: str, min: float, max: float, value: float, label: str, step: float = 1, readout: bool = True, listen: str | None = None) -> Island
```

A restyled `<input type="range">` over `[min, max]`, publishing the numeric value on `topic`. Emits integers when `min`, `max`, `step`, and `value` are all whole, otherwise floats. `readout` shows the current value beside the track. Raises `ValueError` if `min >= max`, `step <= 0`, `value` is out of range, or `label` is blank. Companions: `slider.js`, `slider.css`.

### `value_field`

```python
def value_field(*, topic: str, value: str, label: str, listen: str | None = None) -> Island
```

A labelled text field for any scheme-invariant CSS value (a length, number, font family, or shadow), publishing the raw string on `topic`. It validates nothing about the value, since any string is a candidate; raises `ValueError` only if `label` is blank. Companions: `value-field.js`, `value-field.css`.

### `popover`

```python
def popover(*, trigger: str, panel: str, label: str, panel_id: str,
            haspopup: HasPopup = "dialog", panel_role: str = "group",
            trigger_class: str = "", trigger_label: str | None = None,
            trigger_style: str = "", open_topic: str | None = None) -> Island
```

A trigger button that reveals a floating panel using the native `[popover]` attribute, so the browser supplies the top layer (the panel escapes any ancestor's clipping with no `z-index`), light-dismiss, and Esc. `panel_id` wires the trigger to the panel and must be a valid HTML id. `haspopup` is the `aria-haspopup` value (`HasPopup` is a `Literal` of `"dialog"`, `"menu"`, `"listbox"`, `"grid"`, `"tree"`, `"true"`). Pass `open_topic` to echo `{"open": bool}` on the bus when it opens or closes; without it the popover publishes nothing. Raises `ValueError` if `label` is blank, `panel_id` is not a valid id, `panel` is empty, or `trigger` is empty with no `trigger_label`. Companions: `popover.js`, `popover.css`.

The adapter anchors the panel under its trigger with inline styles and keeps that placement current while the panel is open: it repositions on open, on viewport resize, on any scroll (a capture-phase listener sees every scroll container, so a trigger inside a scrolling column carries its panel with it), and when the open panel itself changes size (a `ResizeObserver`; a density switch grows the panel in place). A panel clamped against the viewport keeps an 8px clearance from every edge, so its own border stays visible. This hand placement stands in for CSS anchor positioning, which the toolkit's target browsers do not all support yet; the full invalidation ledger — each covered source and the one accepted residue — lives at the top of `popover.js`.

### `modal`

```python
def modal(*, trigger: str, body: str, label: str, dialog_id: str,
          title: str | None = None, trigger_class: str = "",
          trigger_label: str | None = None, open_topic: str | None = None) -> Island
```

The modal sibling of `popover`: a trigger that opens a centered native `<dialog>` with `showModal()`, so the browser supplies the top layer, the `::backdrop`, the focus trap, Esc, and the inert background. Dismissal is the close button or Esc, deliberately not a backdrop click, so the dialog is not lost to a stray outside click. `open_topic` behaves as on `popover`. Raises `ValueError` if `label` is blank, `dialog_id` is not a valid id, `body` is empty, or `trigger` is empty with no `trigger_label`. Companions: `modal.js`, `modal.css`.

### `theme_state`

```python
def theme_state(*, scope: str, bindings: Sequence[Binding]) -> Island
```

A behavior-only island (no markup) for live token editing: when a bound topic publishes, it writes the token edit onto every element matching the `scope` selector. Token names come from the trusted `bindings`, never from published values. It subscribes to the binding topics and publishes nothing. Raises `ValueError` if `scope` is blank or `bindings` is empty. Companion: `theme-state.js` (no CSS, since it renders no markup). See `ArmBinding` and `ValueBinding` below.

### `theme_export`

```python
def theme_export(*, scope: str, bindings: Sequence[Binding]) -> Island
```

The read-back sibling of `theme_state`: a button that reads each bound token's current computed value off `scope`, assembles a `:root` block, and copies a `tokens.css` to the clipboard. It reads on demand and is not bus-coupled. Raises `ValueError` if `scope` is blank or `bindings` is empty. Companions: `theme-export.js`, `theme-export.css`.

## Display and structure

Static surfaces. Most have no adapter; the two that do use it only for a copy action, not the bus.

### `preview`

```python
def preview(*, scope_id: str, scheme: Literal["light", "dark"] | None = None) -> Island
```

A representative sample of components inside a scope wrapper (`data-sb-scope`) that repaints as tokens change, so a sibling `theme_state` can show edits live; it is also a plain gallery specimen. Pass `scheme` to pin the pane to one color scheme. Raises `ValueError` if `scope_id` is blank. Companion: `preview.css`. `preview_items() -> tuple[str, ...]` returns the same sample surfaces individually, for laying light and dark out side by side.

### `table`

```python
def table(*, columns: Sequence[str], rows: Sequence[Sequence[str | Cell]], label: str) -> Island
```

A real `<table>`, the canonical structured-data surface, with `<th scope="col">` headers and an accessible name. It owns its own horizontal scroll, so a wide table scrolls inside itself rather than pushing the page. A `str` cell is escaped; a [`Cell`](#supporting-types) is trusted inline HTML. Raises `ValueError` if `columns` is empty, `label` is blank, or any row's cell count differs from the column count. Companion: `table.css`.

### `code_block`

```python
def code_block(*, code: str, label: str, language: str | None = None, copy: bool = True) -> Island
```

Preformatted source in a mono surface that scrolls horizontally rather than wrapping. `language` shows a cosmetic tag (there is no syntax highlighting); `copy` adds a clipboard button. With neither, the block carries no chrome strip. Raises `ValueError` if `code` is empty or `label` is blank. Companions: `code-block.js` (the copy action only), `code-block.css`.

### `breadcrumb`

```python
def breadcrumb(*, trail: Sequence[tuple[str, str]], current: str, label: str = "Breadcrumb") -> Island
```

A `<nav>` of ancestor links (each a `(label, href)` pair) ending at the current page, marked `aria-current="page"`. The `trail` may be empty for a root page. Raises `ValueError` if `current` or `label` is blank, or any trail crumb has a blank label or href. Companion: `breadcrumb.css`.

### `collapsible`

```python
def collapsible(*, title: str, body: str, count: int | None = None, open: bool = False) -> Island
```

A native `<details>`/`<summary>` section, so toggling, keyboard, and open/closed state come from the browser. An optional `count` shows beside the title; `open` renders it expanded. Raises `ValueError` if `title` is blank, `body` is empty, or `count` is negative. Companion: `collapsible.css`.

## Supporting types

Public types in `switchboard_ui.components` used by the factories above:

| Type | Used by | Meaning |
|---|---|---|
| `Cell(html: str)` | `table` | A trusted, already-rendered inline-HTML table cell. |
| `ArmBinding(topic, token, arm)` | `theme_state`, `theme_export` | Edits one scheme arm (`"light"` or `"dark"`) of a color token, re-declaring its `light-dark()`. |
| `ValueBinding(topic, token)` | `theme_state`, `theme_export` | Sets a scheme-invariant token directly. |
| `Binding` | the two above | `ArmBinding | ValueBinding`. |
| `HasPopup` | `popover` | `Literal["dialog", "menu", "listbox", "grid", "tree", "true"]`. |

## Summary

| Component | Factory | Bus | Adapter | Structural CSS |
|---|---|---|---|---|
| Segmented toggle | `segmented` | publishes `topic`, follows `listen` | `segmented.js` | `segmented.css` |
| Color input | `color_input` | publishes `topic`, follows `listen` | `color-input.js` | `color-input.css` |
| Color picker | `color_picker` | publishes `topic`, follows `listen` | `color-picker.js` (+ popover) | `color-picker.css` (+ popover) |
| Slider | `slider` | publishes `topic`, follows `listen` | `slider.js` | `slider.css` |
| Value field | `value_field` | publishes `topic`, follows `listen` | `value-field.js` | `value-field.css` |
| Popover | `popover` | `open_topic` (optional) | `popover.js` | `popover.css` |
| Modal | `modal` | `open_topic` (optional) | `modal.js` | `modal.css` |
| Theme state | `theme_state` | subscribes bindings | `theme-state.js` | — |
| Theme export | `theme_export` | — (clipboard) | `theme-export.js` | `theme-export.css` |
| Preview | `preview` | — | — | `preview.css` |
| Table | `table` | — | — | `table.css` |
| Code block | `code_block` | — (copy only) | `code-block.js` | `code-block.css` |
| Breadcrumb | `breadcrumb` | — | — | `breadcrumb.css` |
| Collapsible | `collapsible` | — | — | `collapsible.css` |

## See also

- [Write an island adapter](../how-to/write-an-island-adapter.md): the four-part recipe each component follows.
- [Theme tokens](tokens.md): the `--sb-*` values that paint these components.
- [Ownership](../explanation/ownership.md): why a component carries structure but no paint.
