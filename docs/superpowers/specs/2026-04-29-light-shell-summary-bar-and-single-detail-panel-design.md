# Light Shell, Summary Bar, and Single Detail Panel Design

## Purpose

Replace the current dark shell with a lighter, lower-fatigue workspace that preserves the fixed 4×4 matrix engine while making the UI easier to scan and easier to use in long decision sessions.

This pass is a shell refactor, not a backend logic rewrite.

## Goals

- move the app to a light visual theme
- adopt a compact top summary bar
- keep the matrix as the dominant surface
- replace the tabbed right-side pane with a single persistent decision detail panel
- keep current matrix selection, routing, and answer behavior underneath
- reduce visual density and top-of-page vertical cost

## Non-Goals

- changing the fixed 4×4 matrix structure
- changing persona or scenario backend definitions
- rewriting question routing again
- changing execution-layer semantics
- redesigning decision data generation in this pass

## Product Direction

The app should feel like a decision workspace rather than a command console.

The visual reference direction is:

- warm white and soft neutral backgrounds
- light cards with subtle borders
- restrained primary blue
- semantic tints for cautious, strategic, decisive, and analytical states
- compact controls and summary chrome
- one continuous decision workflow rather than tabbed mode switching

## Architecture

This redesign should remain a presentation-layer refactor inside:

- [app/static/index.html](/Users/pragyan/Workspaces/Decision%20Framework%20System/app/static/index.html:1)

The current backend runtime, matrix bootstrap, cell data generation, routing, and answer object contracts remain unchanged.

The implementation should preserve existing render hooks and DOM ids wherever practical so the shell can change without destabilizing matrix behavior.

## Layout Model

The new page shell should have four major regions.

### 1. Top Summary Bar

A compact utility strip at the top of the page.

Contents:

- product / system label
- active scenario summary pill
- scenario selector
- persona selector

The scenario summary pill should compress the active decision into a single line, for example:

- `P4 · Transition gap cash shortfall — bridge internally, renegotiate customer contracts, or draw down grant early?`

This strip is for orientation, not narrative explanation.

### 2. Scenario Header

A compact scenario context header below the summary bar.

Contents:

- `Current scenario` label
- scenario title
- persona role subtitle
- `Expand scenario` control
- one compact route / tension card
- a small stat stack on the right

The stat stack should show:

- persona
- options
- live signals
- anchors

The current scenario modal behavior should remain. Expanding scenario context must continue to open a popup rather than expanding inline.

### 3. Matrix Workspace

The matrix remains the dominant page surface.

Structure:

- left rail with 4 perspective labels
- top row with 4 decision lens headers
- 16 light matrix cards in the center

The matrix must remain fully visible on common laptop screens as often as possible. The header and summary bar should be compressed specifically to preserve matrix height.

### 4. Right Detail Panel

Replace the current right-side tabbed panel with one persistent `Decision Detail` panel.

The panel should show, in order:

- selected cell label
- executive answer
- signal visuals / charts
- primary risk
- likely consequence
- next step
- question input at the bottom

Question asking and cell clicking should both update this same surface.

## Visual System

### Color

Use a light theme built from warm neutral surfaces.

Base direction:

- page background: warm white / soft stone
- primary panels: white and off-white
- borders: low-contrast gray
- primary accent: restrained blue
- semantic accents:
  - cautious: muted amber
  - strategic: muted green-blue
  - decisive: muted coral/red
  - analytical: muted violet

Strong color should be reserved for:

- active state
- routed state
- summary emphasis
- RAG signals

The shell should avoid simply inverting the dark theme. Colors should be recalibrated for light mode rather than copied at full saturation.

### Typography

The type system should become calmer and more compact.

Rules:

- section labels: compact uppercase or semi-condensed feel
- body text: neutral sans
- executive answers: larger and stronger than body, but not oversized
- matrix card data: crisp, legible, and aligned for scanning

### Surfaces

Panels and cards should use:

- pale surfaces
- subtle borders
- soft shadows
- small to medium radius
- modest hover lift

The right detail panel should have slightly stronger section separation than the matrix cards, but still remain visibly lighter than the current dark shell.

## Matrix Card Presentation

Each matrix card should present:

- top 2 to 3 generated decision-support data points
- short decision line
- no heavyweight title block

The card should be optimized for comparison, not reading long prose.

Card states:

- default: subtle border
- hover: light lift
- selected: blue border / light blue wash
- routed: amber border / light amber wash

The matrix should feel dense enough for comparison while staying visually quiet.

## Decision Detail Panel

The right panel becomes a single continuous decision surface.

### Content Blocks

The detail panel should show:

1. selected cell label
2. executive answer block
3. visual signals block
4. risk block
5. likely consequence block
6. next step block
7. question input block

### Interaction Model

- clicking a matrix cell updates the panel
- asking a question routes to one cell, highlights it, and updates the same panel
- there is no separate assistant mode in the main shell

This removes visual mode switching and keeps the user inside one decision workflow.

## Summary Bar and Header Behavior

The upper page chrome must become compact and skimmable.

Rules:

- the summary bar is always visible
- the scenario header must not behave like a hero section
- long scenario text remains in the modal popup only
- the compact route / tension card remains visible as the only inline context narrative

The top area should provide orientation while consuming substantially less height than the current shell.

## Responsiveness

The redesign should prioritize common laptop widths first, then degrade cleanly for narrower viewports.

Key rules:

- matrix remains the main surface on desktop
- the right detail panel must stay fully usable within viewport height
- top controls should wrap before overflowing
- the summary pill and selectors should truncate gracefully
- matrix card rows should align cleanly and truncate instead of wrapping awkwardly

## Migration Rules

This is a shell-level refactor only.

Rules:

- preserve existing ids and render hooks where possible
- adapt current DOM bindings instead of creating a parallel UI path
- remove obsolete tab logic only after the single detail panel is stable
- do not change backend answer contracts in this pass

## Testing Expectations

Validate at minimum:

- matrix renders correctly across personas and scenarios
- selected and routed cell states remain correct
- clicking a cell updates the right detail panel
- asking a question updates the same right detail panel
- scenario modal still opens and closes correctly
- top summary bar selectors still switch persona and scenario correctly
- right panel does not overflow vertically on common laptop screens
- matrix remains substantially visible without pushing key rows below the fold

## Success Criteria

The redesign is successful if:

- the app feels lighter and less cognitively heavy than the dark shell
- the matrix remains the visual center of the workflow
- the right side becomes one coherent decision detail surface
- the upper page chrome is compact and skimmable
- no backend matrix or routing behavior regresses
