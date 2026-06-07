# Explanation: layout

Layout is a recursive value. The package provides one general primitive, the `Frame`, and a preset that arranges it into a ready-made page. This page explains the primitive first, then the preset. For the preset's structure, see [The three-column preset](../reference/three-column.md).

## Layout is a recursive value

A `Frame` is a one-dimensional flex stack (a row or a column) whose children are islands or nested frames. Composition to arbitrary depth is the same mechanism repeated, so a region can hold a nested sub-layout as naturally as it holds islands. A child may be wrapped in a `Slot` to pin its size (a fixed rail) or let it grow (an elastic pane), so layouts of fixed and flexible parts compose from the same primitive. A `Document` wraps a root frame as a full page.

One mechanism (a flex stack) at every level means there is no separate page-level layout system to learn: the outermost arrangement and the deepest nested one are the same kind of value. The event bus is global, so nesting is a layout concern only; an island anywhere in the tree coordinates with any other over the same bus.

For why the primitive is flexbox rather than CSS grid, see [Design decisions](design-decisions.md).

## A preset is just an arrangement of frames

A preset is an ordinary function that assembles islands into a frame tree and returns a `Document`. It owns no rendering path and no type of its own; it is sugar over the primitive, so anything a preset builds you could build by hand.

`three_column` is the preset the demo uses: a column of three rows (a fixed-height top and bottom around a flexible middle), each a row of three cells (fixed-width sides around a flexible center). Islands are placed by region name, and an omitted region collapses. It is built from `Frame` and `Slot` like any other layout; the sizes are plain CSS lengths the preset owns, not design tokens.

## Style is the host's, not the package's

The packaged stylesheet is layout structure only: the flex rules that make a frame tree render. It sets no color, type, or theming, and no box-spacing either: it distributes space with `gap` and never uses `margin` (banned) or `padding` (a box's inset is a density decision the host owns). It styles only its own `.sb-*` elements, never your `body` or `:root`. A preset may hold opinions about *layout* (three columns, fixed side rails, a flexible center), but visual *style* belongs to the application that hosts the islands; the package stays out of the way. The test suite enforces all of this statically.
