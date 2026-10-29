<!-- GENERATED from switchboard_theme/reference.py; do not edit here.

Every table below is projected from the typed token registry in tokens.py (the
source of truth) and the prose lives in reference.py. Edit those and run `just
generate`; test_generated.py fails the build if this page drifts. -->

# Theme tokens

The theme is configured entirely through CSS custom properties, the `--sb-*` tokens. They are defined in a typed registry, `switchboard_theme.tokens`, from which both the shipped `static/default.css` and this page are rendered. A host re-themes by overriding any token; the structural layer never reads a token except the `--sb-fit-*` contract. This page lists every token and its default.

## Naming

Every token name is `--sb-<category>-<role>`. The `<category>` is one of a closed set; the `<role>` is everything after it and may itself contain hyphens (`bg-raised`, `accent-fg`, `control-block`).

A scheme-varying token expands to three properties: the two authored arms `--sb-<category>-<role>-light` and `--sb-<category>-<role>-dark`, plus the composed `--sb-<category>-<role>` defined as `light-dark(var(…-light), var(…-dark))`. The composition is generated, never hand-written. The OS color scheme (or a `color-scheme` pinned on a subtree) chooses the arm.

## The registry

`switchboard_theme.tokens` is the single source of truth. `default.css` is rendered from it by `render_css()`, this page by `render_reference()`, and both carry a "do not edit here" header. `test_generated.py` fails the build if either artifact drifts from the registry.

| Piece | Role |
|---|---|
| `Category` (enum) | The closed namespace: `color`, `font`, `space`, `radius`, `border-width`, `shadow`, `fit`. A new category is a deliberate edit, caught by the type checker; it cannot drift in as a stray prefix. |
| `ValueType` (enum) | What the value is and how the builder edits it: `color`, `length`, `number`, `font-family`, `shadow`. |
| `Themed(light, dark)` | A scheme-varying value; renders the two arms plus the `light-dark()` composition. |
| `Fixed(value)` | A single scheme-invariant declaration. |
| `Derived(expr)` | A `calc()`/`var()` expression over other tokens (the `--sb-fit-*` contract). |
| `Token` | A frozen record: `category`, `role`, `type`, `value`, `doc`. Its `name` property builds the `--sb-…` string and its `doc` is the Role column below, so a token arrives documented. |
| `REGISTRY` | The ordered tuple of every token; both renderers group it by category. |
| `MODES` | The density modes (see [Density](#density)). |

## Color

Every color token is `Themed`: each row authors a `-light` and a `-dark` arm, and the public token is the `light-dark()` of the two.

| Token | Light | Dark | Role |
|---|---|---|---|
| `--sb-color-bg` | `#ffffff` | `#16181d` | Base surface |
| `--sb-color-bg-raised` | `#f6f7f9` | `#1c1f27` | Raised surface (panels, code, the table header band) |
| `--sb-color-fg` | `#1b1d22` | `#e6e8ec` | Primary text |
| `--sb-color-muted` | `#6b7280` | `#9aa1ad` | Secondary text |
| `--sb-color-subtle` | `#9ca3af` | `#6b7280` | Tertiary text, separator glyphs |
| `--sb-color-faint` | `#8b919c` | `#666d79` | The label chrome that recedes furthest: uppercase group labels, counts, faint annotations |
| `--sb-color-border` | `#e3e5e9` | `#2b2f37` | Lines and seams |
| `--sb-color-accent` | `#5b4bd6` | `#9d8bff` | The single accent |
| `--sb-color-accent-fg` | `#ffffff` | `#16181d` | Text on the accent fill |
| `--sb-color-accent-soft` | `#efedfb` | `#23203a` | The accent's tinted surface: the ground of a callout that reads as marked, not interactive |
| `--sb-color-danger` | `#c2334b` | `#ff6b81` | Error / invalid |
| `--sb-color-danger-fg` | `#ffffff` | `#16181d` | Text on danger |
| `--sb-color-diag-bad` | `#b4252e` | `#ff8a8f` | The removed line in a before/after code annotation |
| `--sb-color-diag-good` | `#1f7a4d` | `#69d49a` | Its replacement in a before/after code annotation |
| `--sb-color-popover-scrim` | `rgb(0 0 0 / 0)` | `rgb(0 0 0 / 0)` | Popover backdrop (transparent: a non-modal popover does not dim the page) |
| `--sb-color-modal-scrim` | `rgb(0 0 0 / 0.4)` | `rgb(0 0 0 / 0.6)` | Modal backdrop (dims the page; darker in the dark scheme) |
| `--sb-color-handle-ring` | `#ffffff` | `#f6f7f9` | Color-picker handle ring (near-white in both arms so it stays visible over any spectrum color) |

The default surface reads flat: `bg-raised` is only a faint step from `bg`, present as the hook a host needs for a real raised surface. Meaning is carried by text and weight rather than color, so `success` / `warning` / `info` are not defined until a component needs them; `danger` ships because forms need an error state, and the `diag-*` pair ships scoped to before/after code annotation.

## Type

| Token | Default | Role |
|---|---|---|
| `--sb-font-family` | `"Recursive", ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace` | The UI family: everything structural, over a monospace fallback stack |
| `--sb-font-family-prose` | `"Recursive", ui-sans-serif, system-ui, sans-serif` | The prose family: running text, over a proportional fallback stack |
| `--sb-font-axis-mono` | `1` | MONO position for the UI arm (proportional `0` to mono `1`) |
| `--sb-font-axis-casual` | `0` | CASL position for the UI arm (linear `0` to casual `1`) |
| `--sb-font-axis-mono-prose` | `0` | MONO position for the prose arm: proportional |
| `--sb-font-axis-casual-prose` | `0.36` | CASL position for the prose arm: a warm cast |
| `--sb-font-size-sm` | `0.8125rem` | The chrome scale: structural labels, table grids, code, rail rows |
| `--sb-font-size-base` | `0.9375rem` | The body size, and a density cause |
| `--sb-font-size-lg` | `1.125rem` | Section titles and prose `h2` |
| `--sb-font-weight-normal` | `400` | Running text |
| `--sb-font-weight-medium` | `500` | The current nav row |
| `--sb-font-weight-bold` | `700` | Headings, table headers, structural labels |
| `--sb-font-line-height` | `1.5` | The body line box, and a cause of `--sb-fit-control-block` |
| `--sb-font-tracking` | `0` | Natural-case text: no extra tracking |
| `--sb-font-tracking-wide` | `0.04em` | Uppercase structural labels: table headers, group labels, badges |
| `--sb-font-size-display` | `1.9rem` | The page-title size, well clear of body |
| `--sb-font-weight-display` | `800` | The page title's weight, the step past bold |
| `--sb-font-line-height-display` | `1.12` | The tight leading a display size needs |
| `--sb-font-tracking-tight` | `-0.02em` | The slight negative tracking a display size needs |
| `--sb-font-measure` | `46rem` | The prose reading measure: paragraphs and lists cap here while tables and code take the column's full width |

Type tokens stay generic (family, size, weight, line-height, tracking), so the toolkit is not coupled to one typeface; the default theme names one. Both family tokens lead with Recursive, a single variable font whose axes carry the role distinction: the `--sb-font-axis-*` tokens hold the MONO (proportional `0` to monospace `1`) and CASL (linear `0` to casual `1`) positions for the UI and prose arms, and the theme's paint sets `font-variation-settings` from them wherever it sets a family. Weight is never driven through the axis tokens: `font-weight` maps to the registered `wght` axis on its own, so the weight tokens keep working against the variable face and synthesize against the fallbacks.

The display four (`size-display`, `weight-display`, `line-height-display`, `tracking-tight`) are consumed together wherever a page title is set, so an `h1` reads as display type rather than as a bolder body line. `--sb-font-measure` caps running text at a comfortable line length; it is a property of the type, not of the layout, which is why it sits here rather than beside the content column's cap in the `--sb-fit-*` contract.

### Typeface delivery

The face ships in the theme distribution as `static/recursive.woff2` (licensed under the SIL Open Font License; the license text ships beside it). A binary cannot ride the inline `<style>` seam, so delivery is the host's: serve `switchboard_theme.font_bytes()` at a URL you own and prepend `switchboard_theme.font_head(url)` to `extra_head`. A page without the font block degrades to the system stacks in the family tokens.

## Space

| Token | Default | Role |
|---|---|---|
| `--sb-space-2xs` | `0.125rem` | The tightest rhythm: rail rows, a heading's inset over its rule |
| `--sb-space-xs` | `0.25rem` | Quiet chrome: a nav row's inset, a text action |
| `--sb-space-sm` | `0.5rem` | Table cells, chrome strips, the gap within a control group |
| `--sb-space-md` | `0.75rem` | The common gap between blocks |
| `--sb-space-lg` | `1rem` | Prose code blocks and list indents |
| `--sb-space-xl` | `1.5rem` | The gap between unrelated groups in a bar |
| `--sb-space-2xl` | `2rem` | Document-surface insets: a reading column's breathing room |
| `--sb-space-3xl` | `3rem` | The widest document inset |
| `--sb-space-inset` | `0.75rem` | The inset a control applies to its own content, and a density cause |

`--sb-space-inset` is a separate semantic token, not a step on the scale: it is the inset a control applies to its own content, and density moves it without disturbing the scale steps. It happens to share `0.75rem` with `md` at the default density.

The scale itself spans two ranges. `2xs` through `xl` are the chrome range, the gaps and insets of controls, rails and table cells; `2xl` and `3xl` are the document range, where a reading column needs more room than a control-sized gap.

## Radius

| Token | Default | Role |
|---|---|---|
| `--sb-radius-base` | `0` | The default corner: square |
| `--sb-radius-sm` | `0.125rem` | The small opt-in rounding step |
| `--sb-radius-lg` | `0.375rem` | The large opt-in rounding step |

Components use `--sb-radius-base`, which is `0`, so the default look is square. A host rounds the whole UI by setting `--sb-radius-base`, or reaches for a step where differential rounding is wanted.

## Border width

| Token | Default | Role |
|---|---|---|
| `--sb-border-width-thin` | `1px` | Every hairline |
| `--sb-border-width-accent` | `2px` | The selection stripe and the focus-ring width |

Border *color* is not in this category: it is `--sb-color-border`, over in color. A token's category is its value type, so the width and the color of one hairline live apart.

## Shadow

| Token | Default | Role |
|---|---|---|
| `--sb-shadow-base` | `none` | The default: no shadow, so the look stays flat |
| `--sb-shadow-sm` | `light-dark(0 1px 2px rgb(0 0 0 / 0.08), 0 1px 2px rgb(0 0 0 / 0.45))` | The themed step a host opts into |

The default look has no shadows: components use `--sb-shadow-base`, which is `none`. `--sb-shadow-sm` is a themed step a host opts into; its color varies by scheme, so it carries arms. A shadow stays in the `shadow` category even when its color varies, because the category names the dominant value type and scheme variance rides the arm axis.

## The component geometry contract

The `--sb-fit-*` tokens are `Derived` or `Fixed` obligations projected from the cause tokens above. They are the only theme values the structural layer is allowed to read (see [Ownership](../explanation/ownership.md)). Structure consumes a fit token as a floor; it never defines one.

| Token | Value | Derived from |
|---|---|---|
| `--sb-fit-control-block` | `calc(var(--sb-font-size-base) * var(--sb-font-line-height) + 2 * var(--sb-space-inset) + 2 * var(--sb-border-width-thin))` | The rendered height of one standard control: line box + symmetric inset + symmetric hairline |
| `--sb-fit-control-inline` | `6rem` | The short-label minimum width |
| `--sb-fit-content-inline` | `60rem` | The content column's cap: how wide a document surface grows before the margins take the rest |
| `--sb-fit-hit-target` | `1.5rem` | The minimum pointer-target square |
| `--sb-fit-rail-block` | `var(--sb-fit-control-block)` | A rail row is one control tall |
| `--sb-fit-color-area` | `12rem` | The square saturation/value surface |
| `--sb-fit-color-hue` | `var(--sb-fit-control-block)` | The hue track is one control tall |
| `--sb-fit-color-handle` | `0.75rem` | The picker drag handle |
| `--sb-fit-slider-thumb` | `0.875rem` | The slider thumb's inline size |
| `--sb-fit-modal-inline` | `32rem` | The modal width cap |
| `--sb-fit-modal-block` | `90dvb` | The modal height cap, stopping short of the viewport so a band of scrim stays visible |

`control-block` is the one computed root. Because `rail-block` and `color-hue` alias it, a rail row and the hue track are guaranteed the same height as a control and reproject together.

## Density

`MODES` renders one `:root[data-density="<name>"]` rule per mode. Each mode reassigns only the cause tokens; because `--sb-fit-control-block` is a `calc()` over them, the whole contract reprojects automatically.

| Mode | `--sb-font-size-base` | `--sb-space-inset` |
|---|---|---|
| default (no attribute) | `0.9375rem` | `0.75rem` |
| `compact` | `0.875rem` | `0.5rem` |
| `spacious` | `1rem` | `1rem` |

Set `data-density` on `:root` to switch. Nothing else is overridden directly: the control inset is a dedicated token precisely so density can move it without touching the space scale, and everything sized off `control-block` follows.

## Scheme pinning

The scheme is the second mode axis, with the same attribute contract. By default the page follows the OS: `:root` declares `color-scheme: light dark`, and every scheme-varying token composes through `light-dark()`. Setting `data-scheme="light"` or `data-scheme="dark"` on `:root` pins `color-scheme` to that arm, which flips every composed token at once; removing the attribute returns to auto. Pinning flows only through `color-scheme`: no individual color is restated.

## Per-instance values

A few paint rules read a custom property that is not a registry token: the color-input and color-picker swatches paint `background: var(--sb-swatch)`. The factory carries that value per instance (the current color), so it never appears in `:root`. Auditing the registry against the CSS will show this `var()` with no matching definition; that is by design, not a missing token.

## See also

- [Ownership](../explanation/ownership.md): the floor-and-surface split (tokens are the surface), and the `--sb-fit-*` contract as the one channel from theme to structure.
- [The workbench preset](workbench.md): the structural CSS that consumes the fit tokens.
