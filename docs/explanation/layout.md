# Layout

A page is described by three independent decisions, each carried by its own value: how the frames are *arranged*, what each frame does with content that *exceeds* it, and how the root relates to the *viewport*. They are independent in the sense that changing one leaves the others meaning what they meant. The rest of this page takes them in turn, then the presets that combine them.

## Arrangement is a recursive value

A `Frame` is a one-dimensional flex stack (a row or a column) whose children are islands or nested frames. Composition to arbitrary depth is the same mechanism repeated, so a region can hold a nested sub-layout as naturally as it holds islands. A child may be wrapped in a `Slot` to pin its size (a fixed rail) or let it grow (an elastic pane), so layouts of fixed and flexible parts compose from the same primitive. A `Document` wraps a root frame as a full page.

One mechanism (a flex stack) at every level means there is no separate page-level layout system to learn: the outermost arrangement and the deepest nested one are the same kind of value. The event bus is global, so nesting is a layout concern only; an island anywhere in the tree coordinates with any other over the same bus.

## Overflow is declared, not inherited

Every `Frame` names what it does with content that exceeds it: `visible`, `clip`, or `auto`. The renderer emits exactly one class for that value, so the policy is readable in the Python, in the HTML, and in the stylesheet under one name.

The point is what it stops being. Scroll ownership used to be a property of the *stylesheet*: frames clipped by default, a region opted out by carrying an extra class, and the opt-out took effect only by winning an equal-specificity tie — so which element scrolled depended on the order rules happened to appear in, and reordering the sheet could change it silently. Now a frame that scrolls says so, and nothing above or beside it can decide otherwise.

Naming it also makes a whole-tree question askable. `clip` creates no scroll container at all, not even for the user agent's own scroll-a-focused-descendant-into-view behaviour, so a viewport-locked page whose frames are all `clip` or `visible` renders content nothing can reach. Each frame is valid alone; only the combination is the defect, which is why [`unreachable_content`](../reference/analyzer.md#unreachable_content) checks the tree rather than the node.

## Root policy is the page's shape

Every `Document` names how its root relates to the viewport: `flow`, where the root is content-sized and the *page* scrolls, or `viewport`, where the root is fixed and the page never scrolls.

This is the decision that determines where the reader's position lives, and therefore which of the browser's own behaviours can look after it — scroll restoration, find-in-page, fragment anchors, overscroll. [Scroll ownership and navigation state](scroll-ownership.md) is the long version.

It is **required**, not defaulted. These are two different kinds of page rather than one page with a setting, and defaulting either would privilege it while every call site quietly inherited it. Requiring it costs one word per document and buys a diff in which every page's shape is visible. The mode is also never inferred — not from content, region names, viewport size, or the presence of a nav — because a shape guessed from content changes when the content does.

## A preset combines the three

A preset is an ordinary function that combines the three decisions above into a page shape people actually build. It owns no rendering path and no type of its own; it is sugar over the primitives, so anything a preset builds you could build by hand.

There are two, named for the shapes rather than for the number of columns they happen to have. [`document_site`](../reference/document-site.md) returns a flowing document: the centre column is `visible` so the page scrolls the article, and the side cells are sticky `auto` rails. [`workbench`](../reference/workbench.md) returns a viewport-locked shell: the three body cells are `auto` and everything above them `clip`.

Both are a column of three rows (content-driven head and foot rails around a middle), each a row of three cells (fixed-width sides around a flexible center). Islands are placed by region name (or a region is handed a frame, which becomes its cell), and an omitted region collapses. The side widths are plain CSS lengths the preset owns, while the rail floor comes from the theme's component-geometry contract.

They are two assemblies rather than one constructor with a flag, because a flag would keep two page semantics hidden inside one convenient name. They share the nine region names and the three row hooks, so a page can move between shapes without learning a second placement vocabulary and a seam owner means the same thing in both.

## Why nested flex, not grid

A nine-region tiling is the shape CSS grid exists for: one grid container with named template areas would hold all nine cells under a single parent, and that parent's `gap` could draw every seam at once. The preset builds nested flex rows instead, and the choice is deliberate.

A grid template is a flat construct: it names a fixed set of areas at one level, and a sub-layout inside an area is a different mechanism, not the template again. The `Frame` is recursive: the preset's arrangement and the arrangement inside any of its cells are the same kind of value, so the preset is not special. Anything it builds you can build by hand, extend one cell deeper, or replace entirely, using the one primitive the package has. One mechanism at every level also keeps the enforcement surface small: the structural guards check one kind of rule, and a layout bug is always a flex question, never a which-system question.

The accepted cost is seam ownership. Because the nine cells never share a single parent, no one container can paint every border between them; each seam is assigned to exactly one owner instead. [Seams](seams.md) is the recipe that keeps that assignment single and complete.

## Style is the host's, not the package's

The packaged stylesheet is layout structure only: the flex rules that make a frame tree render. It sets no color, type, or theming, and no box-spacing either: it distributes space with `gap` and never uses `margin` (banned) or `padding` (a box's inset is a density decision the host owns). It styles only its own `.sb-*` elements, never your `body` or `:root`. A preset may hold opinions about *layout* (three columns, fixed side rails, a flexible center), but visual *style* belongs to the application that hosts the islands; the package stays out of the way. The test suite enforces all of this statically. This division of decisions among layers, and the two things it buys, is the subject of [Ownership](ownership.md).

The lines between tiled regions are a host (theme) concern too. For how a border between two cells is drawn exactly once, with a single owner, see [Seams](seams.md).
