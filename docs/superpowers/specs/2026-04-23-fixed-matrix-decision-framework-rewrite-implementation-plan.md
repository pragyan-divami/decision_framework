# Fixed Matrix Decision Framework Rewrite Implementation Plan

## Purpose

This plan turns the approved rewrite spec into an execution sequence that can replace the current mixed KPI-first matrix and question-routing logic without leaving overlapping engines active.

The plan assumes:

- the fixed-matrix rewrite spec is approved
- the current app shell can remain
- the matrix engine, routing layer, execution layer, and answer generation will be rewritten behind that shell

## Delivery Strategy

Implement this rewrite in vertical slices that preserve a runnable app after each phase.

The order should be:

1. introduce the new fixed matrix engine in parallel
2. move answer generation onto the new execution model
3. move question routing onto the new routing model
4. remove or isolate the old KPI-first logic

This avoids a big-bang cutover where the UI loses its answer behavior mid-rewrite.

## Phase 1: Canonical Matrix Foundation

### Goal

Create a new internal fixed 4x4 matrix definition that is independent from scenario-specific KPI grid construction.

### Tasks

1. Add a canonical matrix configuration module.
   - Define the four decision lenses:
     - Cautious
     - Strategic
     - Decisive
     - Analytical
   - Define the four canonical perspectives:
     - Self / Personal Risk
     - Stakeholder / People
     - Business / Outcome
     - Ethics / Governance

2. Encode the 16 fixed cell definitions from `decision_framework_matrix_spec.md`.
   - For each cell store:
     - `emotion`
     - `perspective`
     - `primary_fit`
     - `secondary_fit`
     - `support_fit`
     - `decision_style`
     - `best_data_to_show`
     - `why_this_data`
     - `persona_adjustment`

3. Add a persona-to-perspective-label mapping layer.
   - Persona-specific UI labels must map onto one canonical perspective each.

### Deliverable

A new matrix configuration module that can generate all 16 canonical cells without using the current KPI-first frontend cell builder.

## Phase 2: Persona and Scenario Normalization

### Goal

Normalize existing persona and scenario files into the new runtime shape expected by the matrix, routing, and execution layers.

### Tasks

1. Add a persona normalization layer.
   - Output:
     - `persona_id`
     - `role`
     - `mandate`
     - `primary_accountabilities`
     - `key_risks`
     - `priority_stakeholders`
     - `authority_level`
     - `governance_constraints`
     - `default_decision_bias`
     - `default_perspective_weights`
     - `default_emotion_tendency`

2. Add a scenario normalization layer.
   - Output:
     - `scenario_id`
     - `scenario_title`
     - `scenario_summary`
     - `tension`
     - `decision_context`
     - `options`
     - `source_kpis`
     - scenario evidence text blocks

3. Keep the current markdown files as source of truth.
   - Do not create a second scenario-authoring system.

### Deliverable

Normalized persona and scenario objects that can be passed to the new matrix engine and question router.

## Phase 3: Visible Data Generation Engine

### Goal

Replace KPI-display logic with visible decision-support data generation for each cell.

### Tasks

1. Add a visible data catalog.
   - Supported data types should include:
     - downside
     - reversibility
     - confidence
     - expected value
     - option value
     - stakeholder map
     - trust impact
     - harm potential
     - bottleneck
     - time window
     - threshold
     - missing evidence
     - defensibility
     - approval requirement

2. Implement scenario-to-visible-data translation.
   - Convert raw scenario context and source KPIs into decision-support data.
   - Example:
     - raw KPI: `Grant clawback risk`
     - visible data: `Risk of breaching grant assumptions if this path slips further`

3. Implement ranked visible-data generation per cell.
   - Use the approved ranking formula:
     - `0.30 perspective relevance`
     - `0.30 primary model relevance`
     - `0.20 emotion relevance`
     - `0.15 persona relevance`
     - `0.05 correction relevance`

4. Store both:
   - the full ranked visible-data set for execution
   - a short preview for matrix-cell display

### Deliverable

A visible-data engine that can populate all 16 cells with decision-support data derived from backend scenario/persona files.

## Phase 4: Matrix Renderer Migration

### Goal

Swap the current matrix UI from KPI-first cells to fixed-matrix summary cells.

### Tasks

1. Replace the current frontend cell builder with a new builder that consumes:
   - canonical matrix config
   - persona-specific perspective labels
   - ranked visible-data preview

2. Update each cell to show only:
   - decision lens
   - persona-specific perspective label
   - framework stack hint
   - short visible-data preview

3. Remove KPI-heavy cell content as primary display.

4. Preserve clickability of all 16 cells.

### Deliverable

A visible 4x4 matrix with lightweight summaries in every cell.

## Phase 5: Question Router Rewrite

### Goal

Replace the current mixed KPI/heuristic router with the spec-based routing engine.

### Tasks

1. Implement question classification for:
   - meaning
   - comparison
   - threshold
   - consequence
   - prioritization
   - clarification
   - action
   - missing_data

2. Implement decision-lens scoring using:
   - direct language signal
   - question type fit
   - persona bias fit
   - UI context

3. Implement canonical perspective scoring using:
   - direct language signal
   - question object fit
   - persona priority fit
   - UI context

4. Implement full 16-cell scoring using:
   - `0.30 emotion score`
   - `0.30 perspective score`
   - `0.20 persona alignment`
   - `0.10 question type compatibility`
   - `0.10 visible data fit`

5. Enforce deterministic one-cell selection.
   - No top-two mode
   - No clarification loop
   - No alternate UI mode in v1

### Deliverable

A new router that always returns exactly one selected cell and matched visible data.

## Phase 6: Framework Stack Execution Engine

### Goal

Execute the selected cell through the fixed model stack.

### Tasks

1. Implement primary model handlers for the built-in decision models.
   - Expected Utility
   - Prospect Theory
   - Bounded Rationality
   - Dual-Process Theory
   - Recognition-Primed Decision
   - OODA
   - COM-B

2. Implement secondary model correction logic.
   - Correct the primary model’s likely blind spot.

3. Implement support model feasibility / guardrail logic.
   - Check executability
   - Check safety
   - Check whether the answer should be downgraded to a more practical choice

4. Implement final answer mode selection:
   - direct recommendation
   - comparative recommendation
   - conditional recommendation
   - need more data

### Deliverable

A new execution engine that returns structured decision output from the selected cell.

## Phase 7: Response Generator Rewrite

### Goal

Generate answers strictly from execution output and response templates.

### Tasks

1. Implement the required response fields:
   - `recommended_decision`
   - `decision_risk`
   - `suggested_next_step`

2. Implement optional supporting fields:
   - `reasoning_summary`
   - `confidence`
   - `watch_item`
   - `missing_data`

3. Implement answer formatting by:
   - question type
   - decision lens
   - persona tone adjustment

4. Remove direct answer generation from:
   - raw KPI strings
   - legacy cell heuristics
   - generic route-note text

### Deliverable

A single answer generator that produces the full answer object from execution output only.

## Phase 8: Answer Area Integration

### Goal

Make the answer area the primary reasoning surface.

### Tasks

1. Update the answer area to show:

   #### Decision answer
   - recommended decision
   - decision risk
   - suggested next step

   #### Why this answer
   - selected cell
   - framework stack
   - matched visible data
   - reasoning summary
   - confidence

2. Ensure click-to-cell and question-to-cell use the same answer-generation pipeline.

3. Ensure the highlighted cell always matches the selected execution cell shown in the answer area.

### Deliverable

A unified answer area with both executive recommendation and execution trace.

## Phase 9: Remove or Isolate Old Engine Paths

### Goal

Prevent mixed behavior from the old and new engines.

### Tasks

1. Remove or isolate old KPI-first cell generation.
2. Remove or isolate the old local mixed heuristic question router as a primary path.
3. Remove direct answer-generation helpers that build prose from legacy cell text.
4. Keep legacy paths only if explicitly marked as deprecated fallback and unreachable in normal runtime.

### Deliverable

A single active decision engine in production code.

## Testing Strategy

### Unit Tests

- persona normalization
- scenario normalization
- canonical matrix generation
- visible-data ranking
- question classification
- decision-lens scoring
- perspective scoring
- 16-cell selection
- framework stack execution
- response generation

### Golden Tests

Create fixed question -> expected cell -> expected answer tests for representative personas and scenarios.

Each golden test should verify:

- selected decision lens
- selected canonical perspective
- selected cell
- matched visible data
- final answer mode
- recommended decision

### UI Tests

- matrix always renders 16 cells
- persona-specific perspective labels appear correctly
- question asks -> one cell highlights
- cell click -> answer area updates
- answer area and highlighted cell never drift

## Risks and Controls

### Risk

The old and new engines both remain active.

### Control

Introduce a temporary feature flag during migration, then remove the old path once parity is validated.

### Risk

Visible data becomes too generic.

### Control

Require every visible-data item to reference concrete scenario evidence or source KPIs.

### Risk

Persona-specific labels drift away from canonical mappings.

### Control

Store mappings centrally and validate them in tests.

## Recommended Implementation Order

Use this exact order:

1. canonical matrix config
2. normalization layer
3. visible-data engine
4. matrix renderer migration
5. router rewrite
6. execution engine
7. response generator
8. answer-area integration
9. old-engine removal

This order minimizes time spent with a half-migrated system.
