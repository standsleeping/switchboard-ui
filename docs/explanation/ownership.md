# Ownership

The package builds a page from several layers, and gives each layer authority over a different kind of decision. This page explains that division: which layer owns which decision, why the boundaries are enforced rather than merely suggested, and the two things the discipline buys (a theme you can replace wholesale, and a visual bug that traces to a single layer).

## One decision, one owner

Every spatial and visual decision on a page has exactly one owner. The structural stylesheet owns geometry; the theme owns paint; a box owns its own inset; a container owns the rhythm between its children; an interactive state owns repaint and nothing else. No two layers decide the same thing.

What makes this hold is the absence of *co-ownership*. When two layers can both set the same property, neither is safe to change, because a change on one side collides silently with the other. The bans in the stylesheets remove those collisions at the source. [Seams](seams.md) is this same rule applied to a single property, the border between two tiled cells: one line, one owner, never drawn by both neighbours. This page is that rule generalized to the whole system.

## What each layer owns

| Layer | Owns | May never touch |
|---|---|---|
| Structure (`layout.css`) | Geometry: the flex tree, sizing, `gap`, overflow, position | Color, type, any appearance |
| Theme | Paint: color, background, border paint, type, the token values | `position`, `transform` (the coordinate system is structure's) |
| The component geometry contract (`--sb-fit-*`) | The one sanctioned channel from theme to structure: the theme projects its causes (inset, type, border) into a sizing obligation, and structure consumes that obligation as a floor | The reverse flow; structure never defines an obligation, the theme never reads one back |
| A box | Its own inset (`padding`), as a control or content surface — never a layout, mount, or region hook | The space outside itself |
| A container | The rhythm between its children (`gap`) | Reaching into a child's box |
| An interactive state (`:hover`, `:focus`) | Repaint | Geometry; a state never reshapes the box |

Two consequences are worth stating directly. Rhythm between siblings is the container's `gap`, never a child's `margin`: `margin` is banned outright, because it is the property a child would use to claim space that belongs to its parent. And a box's inset is its own `padding`, applied only to the controls and content surfaces that inset their own content, never to a layout, mount, or region hook.

## Composability: a theme you can replace

The division buys *orthogonality*: structure and paint become independent axes, so one can vary while the other holds still. A host can override every visual token, down to the last color and length, and the layout still holds, because the structural layer was never allowed to encode appearance and the theme was never allowed to encode geometry. The substitution is fearless. You can replace the theme in full, knowing it could not have reached into the structure to begin with.

This is why the structural stylesheet declares no tokens of its own: it sets layout properties and consumes only the `--sb-fit-*` obligations the theme publishes (the contract row above), never a color or a paint value. Paint and geometry stay disjoint: the theme paints but never positions, structure positions but never paints, and the test suite checks that the structural sheet admits nothing but layout properties and those contract tokens.

## The floor and the surface

The boundaries divide into two kinds, and the difference is what makes the package both strict and open.

Taste decisions are open to the bone. Color, type, the spacing scale, border weight, radius, shadow, and density are all tokens. None is fixed, and a host overrides any of them. This is the surface, and it is meant to be replaced.

Correctness decisions are fixed. The ownership boundaries, the rule that rhythm is `gap` and never `margin`, geometry that stays stable across interactive state, and the contracts that keep one layer out of another's decisions are not configurable. This is the floor. It is small and rigid on purpose, and the rigidity is what makes the surface safe to vary: a theme can change everything that is taste precisely because it can change nothing that is correctness.

## Least authority, enforced three ways

Each layer is granted only the authority its job needs, and an attempt to exceed it is caught as early as possible. The enforcement runs at three levels, strongest first.

- **Made unrepresentable.** The authoring API offers no surface for the forbidden thing. A `Frame` emits a flex stack spaced with `gap`; there is no margin to set, and the structural CSS holds no tokens. The violation cannot be written. The same tier holds the layers apart at the package level: the core mechanism declares no dependency on the theme, so it has no path to import it, and the separation is a fact of the package graph rather than a guard that watches for a stray import.
- **Made explicit.** Where a layer needs a channel into another, or an exception to the default, it is declared in the open rather than left implicit. The component-geometry contract is the one sanctioned channel from theme to structure: the theme publishes a `--sb-fit-*` obligation and structure consumes it, one way, in plain sight. Overflow is a declared policy, not an accident: every frame clips by default so nothing escapes the viewport-locked root, a region opts into owning its scroll by carrying `sb-scroll`, and a component that scrolls its own content (a wide table, a long code line) declares that scroll in its own structural CSS. Each is visible in a stylesheet, never a silent overflow.
- **Guarded.** Where a rule lives in hand-written CSS, one shared checker parses every stylesheet — and the rendered inline `style` attributes, so paint cannot slip through a `style=` either — and asserts it: every property in the structural sheet is a layout property, an inline style carries only a custom-property value, padding never lands on a layout, mount, or region hook, no state rule changes geometry, and no tiled cell draws an all-sides border. This tier is the weakest of the three by design: it catches the checkable part of each rule, the part a parser can see, and it backstops the layer a host edits most. It keeps an edit made by eye from regressing the rule, but it does not make the rule unwritable the way the first tier does.

## The contract: require and grant

The component geometry contract is the one place two layers meet on purpose, and its vocabulary is directional. A themed component *requires*: its geometry is intrinsic, derived from its own causes (type size, line height, inset, border weight). Structure *grants*: a slot's size is extrinsic, an offer made without knowing what will sit in it. The `--sb-fit-*` tokens are the requirement made public, and the structural sheet consumes each one as a floor, so a slot never grants less than a conforming component requires.

The contract stays minimal by one criterion: a metric belongs in it only if omitting it would let two valid themes be indistinguishable to structure while needing different space. The control's outer block size passes: two themes with different insets need different rail heights, and structure cannot tell them apart without being told. A color fails, and so does anything structure can already observe on its own. The criterion is what keeps that one channel from widening into a general pipe between the layers.

Necessity and sufficiency are checked separately. The guards above are necessity conditions: each bans one way a layer could take space it was not granted. Sufficiency is proven rather than banned. The theme's test suite resolves the contract's `calc()` chain to pixels in pure Python, with no browser, and asserts that every rail floors to at least the control's outer block size and every side column grants at least the control's inline requirement. A companion check renders a control into all nine regions, so the stress case is real, not hypothetical. That assertion is the capstone of the discipline: when every structural slot satisfies the contract, every conforming themed component fits every slot it can be placed in.

## Diagnosability: a bug you can place

The same boundaries that let you replace a layer let you blame one. Because no two layers own the same decision, a visual symptom has a single suspect, and the bans actively clear the layers that could not have caused it. Something in the wrong place is structure's coordinate system, never the theme, which is forbidden to position. A wrong color is the theme or a token, never the structural sheet, which declares no color. A box that jumps on hover is a state rule that changed geometry, which the guard names exactly.

Using this needs no knowledge of the internals. Describe the symptom in plain visual terms, and the description already points at the owner.

| The symptom | The owner to look at |
|---|---|
| Uneven or wrong spacing between things | the container's `gap` (rhythm is the parent's; a child's `margin` is banned) |
| Wrong inset inside one box | that box's own `padding` |
| Wrong color, low contrast, an invisible surface | the theme, or a token value |
| Something mispositioned or overlapping | structure (the theme cannot position) |
| A jump or reflow on hover, focus, or selection | a state rule that changed geometry |
| Content clipped, or it will not scroll | the overflow policy: the frame's clip-by-default and `sb-scroll` opt-in, or the component's own scroll container |
| Wrong size, will not fill, or overflows the page | a slot's sizing, or the component-geometry contract |
| A click does nothing, or an event never arrives | the adapter or the bus, not the CSS |
| Wrong text, missing rows, the wrong markup | the factory that built it, not the CSS |

## See also

- [Seams](seams.md): single ownership applied to one property, the border between tiled cells, with the owners and the guard in full.
- [Layout](layout.md): the structural stylesheet, and why visual style belongs to the host.
