# Explanation: layout

The first standard surface the package provides is the page shell itself: a three-column application frame. This page explains the idea behind it. For the CSS contract, see [The shell layout](../reference/shell-layout.md).

## The shell is the invariant; the islands are the variable

The governing idea is that the shell, its regions, and their sizes are fixed and known before any data loads, while islands are the changing content poured into them. Islands mount into regions that already hold their final geometry at first paint.

This is the same boundary the island model expresses, seen from the layout side. Render the stable frame, then hydrate the changing content into boxes that never resize. A region holds its size whether or not it is ever filled, so adding or removing an island never reflows the page.

## Three columns plus six chrome areas

The frame is nine named regions, `head`/`body`/`foot` by `l`/`c`/`r`, arranged as an outer column of three rows. The top and bottom rows are chrome rails; the middle row is the three island-hosting columns; only the middle row scrolls.

```
┌────────┬────────┬────────┐
│ head-l │ head-c │ head-r │   top rail (chrome)
├────────┼────────┼────────┤
│ body-l │ body-c │ body-r │   the three columns; only this row scrolls
├────────┼────────┼────────┤
│ foot-l │ foot-c │ foot-r │   bottom rail (chrome)
└────────┴────────┴────────┘
```

The outer ring is chrome, so the one elastic main region (`body-c`) never touches the viewport edge. The side columns host islands but are sized as fixed-width rails.

## Nested flex stacks, one layout mechanism

Layout is a recursive value. A `Frame` is a one-dimensional flex stack (a row or a column) whose children are islands or nested frames. The nine-region shell is one preset of that primitive: a column of three rows, each row a stack of three cells. Composition to arbitrary depth is the same mechanism repeated, so a region can hold a nested sub-layout as naturally as it holds islands. A child may be wrapped in a `Slot` to pin its size (a fixed rail) or let it grow (an elastic pane), so layouts of fixed and flexible parts compose from the same primitive.

The event bus is global, so nesting is a layout concern only; an island anywhere in the tree coordinates with any other over the same bus. The region names in the stylesheet are the same nine names the Python model declares, and a consistency test keeps the two in agreement.

For why the layout primitive is flexbox rather than CSS grid, see [Design decisions](design-decisions.md).

## Tokens with standalone fallbacks

Every value reads a design-system token with a built-in fallback. The shell renders correctly with no host, using the fallbacks, and inherits the design system's visual language when its tokens are present. The rails are sized by tokens; an empty region collapses to nothing so one shell serves many layouts.

## The layout follows three rules

**Every viewport edge is chrome.** The rails frame the center so main content never touches the viewport edge.

**The page never scrolls; the columns do.** The shell is locked to the viewport and clips. Vertical scrolling is delegated to the body cells; horizontal scrolling belongs to leaf elements inside a cell.

**Regions are sized by tokens and collapse when empty.** Rail sizes come from tokens; an empty region renders but collapses, so optional slots leave no gaps.
