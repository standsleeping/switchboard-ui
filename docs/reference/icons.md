# Icons

The theme distribution ships an icon set: 28 glyphs from Radix Icons, a closed vocabulary rendered by two renderers from one source. On the server, `icon` returns an inline `<svg>` string to embed in any markup. In the browser, a generated ES module builds the same glyph as an `SVGElement`. Both stamp the same class and the same decorative attributes, so a glyph looks and behaves the same whichever side drew it.

Import from the theme:

```python
from switchboard_theme import icon, icon_module, icon_styles
```

The metadata lives in the submodule beside them: `switchboard_theme.icons` exports `IconName`, `ICON_NAMES`, `IconCategory`, `ICON_CATEGORIES`, `CATEGORY_GUIDANCE`, `IconEntry`, and `ICONS` (all re-exported from `switchboard_theme`).

## The set

Each glyph is one SVG file under `switchboard_theme/static/icons/`, named for the glyph (`check.svg`). Every file keeps the same contract:

- A `viewBox` of `0 0 15 15`, and no `width` or `height`, so the CSS sizes the glyph.
- Paint in `currentColor`, so the glyph takes the color of the text around it.
- No class and no ARIA attributes; the renderers add those.

The glyphs are Radix Icons, MIT License, Copyright (c) 2022 WorkOS. The license text ships beside them as `static/icons/radix-icons-MIT.txt`, and the generated module repeats the notice in its header.

To look a glyph up, open the showcase gallery (`uv run python -m showcase.server`) and select **Icons**: the specimen lists every glyph beside its name, category, and guidance, read straight from `ICONS`.

### `IconName` and `ICON_NAMES`

```python
IconName = Literal["arrow-down", "arrow-left", ..., "trash"]
ICON_NAMES: tuple[IconName, ...]
```

`IconName` is the closed type of glyph names, so a misspelled name is a type error at the call rather than a missing glyph at runtime. `ICON_NAMES` holds every name, alphabetical.

### `IconEntry` and `ICONS`

```python
@dataclass(frozen=True)
class IconEntry:
    name: IconName
    category: IconCategory
    guidance: str

ICONS: tuple[IconEntry, ...]
```

`ICONS` is the curated metadata: one entry per glyph naming its category and when to use it, grouped by category in `ICON_CATEGORIES` order and curated within each group (a chevron before the arrow it outranks).

## Categories

```python
IconCategory = Literal["direction", "action", "navigation", "status", "content"]
ICON_CATEGORIES: tuple[IconCategory, ...]
CATEGORY_GUIDANCE: Mapping[IconCategory, str]
```

Every glyph belongs to one category; `CATEGORY_GUIDANCE` says when to reach for each.

| Category | Use it for |
|---|---|
| `direction` | Disclosure and movement: where activating the control leads, or what it reveals. |
| `action` | Controls that change state. The control carries its own accessible name; the glyph never carries the meaning alone. |
| `navigation` | Persistent chrome in the rails and toolbars, not controls repeated on every row. |
| `status` | Status and meta information. Use sparingly: one glyph per meaning, never as ornament. |
| `content` | The kind of resource a row or a link points at. |

## Rendering on the server

### `icon`

```python
def icon(name: IconName) -> str
```

Return the glyph `name` as an inline `<svg>` string. The root carries `class="sb-icon"`, `aria-hidden="true"`, and `focusable="false"`: the glyph is decorative, hidden from assistive tech and out of the focus order. A control whose only content is a glyph names itself with `aria-label`. The string is trusted markup, so it drops into any raw-HTML argument (an island's `initial`, a table `Cell`, a modal's `trigger`). Raises `ValueError` naming an unknown `name`, which only untyped code can pass.

```python
close = f'<button type="button" aria-label="Close">{icon("cross-1")}</button>'
```

### `icon_styles`

```python
def icon_styles() -> str
```

Return the glyph's CSS as a `<style>` block, for `extra_head` beside the theme. It makes `.sb-icon` a `1em` square that never shrinks in a flex row and paints in `currentColor`, so a glyph scales with the font size of its context and takes its color.

```python
html = render_document(
    doc,
    extra_head=switchboard_theme.head("default") + icon_styles(),
)
```

## Rendering in the browser

### `icon_module`

```python
def icon_module() -> str
```

Return the set as an ES module (the shipped `static/icons.js`). Serve it at a URL you own with a JavaScript content type, then import it from client code:

```js
import { icon } from "/assets/icons.js";

button.append(icon("copy"));
```

| Export | Value |
|---|---|
| `iconNames` | Every glyph name, alphabetical. |
| `iconMeta` | Each name's `category` and `guidance`. |
| `iconCategories` | Each category's `name` and `guidance`, in grouping order. |
| `icon(name)` | A decorative `SVGElement` classed `sb-icon`, or `null` for an unknown name (and outside a browser, where there is no `DOMParser`), so the caller can fall back to text. |

The module sizes nothing itself: a page that renders glyphs from it includes `icon_styles()` too.

### A generated module

`render_icon_module()` in `switchboard_theme.icons` renders the module from the SVG files and `ICONS`. Its output is committed as `static/icons.js`, and the theme's `tests/test_icon_module.py` fails when the committed file drifts from what the files and the metadata render; `just generate` rewrites it. Edit the SVG files or the metadata, never the module.

## Adding a glyph

1. Copy the Radix SVG into `static/icons/` and delete its `width` and `height` attributes.
2. Add its name to `IconName`, keeping the list alphabetical.
3. Add an `IconEntry` to `ICONS` in its category's group.
4. Run `just generate` and commit the file, the name, the entry, and the regenerated module together.

The theme's `tests/test_icons.py` fails until the name, the entry, and the file all agree, and until the file keeps the contract above.

## See also

- [Theme tokens](tokens.md): the `--sb-*` tokens and the typeface, which ship from the same distribution.
- [Components](components.md): the island factories whose raw-HTML arguments accept a glyph.
