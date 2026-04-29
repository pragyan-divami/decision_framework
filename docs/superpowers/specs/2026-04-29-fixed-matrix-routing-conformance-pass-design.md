# Fixed Matrix Routing Conformance Pass

## Purpose

This spec aligns the current fixed-matrix question router with the newer `decision_model_question_routing_logic.md` routing model without rewriting the rest of the application again.

The goal is to keep the current:

- fixed `4 x 4` matrix
- framework stack execution layer
- answer object contract
- frontend answer surfaces

while tightening the backend routing behavior so question interpretation is:

- more explicit
- easier to audit
- easier to tune
- more consistent with the approved routing logic

## Goals

- Align fixed-matrix question routing with the new routing spec.
- Make `question type` and `decision family` separate routing concepts.
- Adopt explicit emotion and perspective score formulas.
- Adopt explicit fixed-matrix cell score formulas.
- Make visible-data routing a first-class part of the selection flow.
- Preserve the current frontend answer contract to avoid unnecessary UI regressions.

## Non-Goals

- Replacing the fixed matrix structure
- Replacing the framework stack execution layer
- Rewriting answer-generation from scratch
- Cross-scenario routing
- Multi-cell answers
- Clarification-loop expansion
- Full UI redesign

## Scope

This pass updates only the routing layer.

### In Scope

- backend question type classification
- backend emotion scoring
- backend perspective scoring
- backend cell scoring
- backend visible-data matching
- frontend context payload additions required by the new scoring model
- backend routing trace for debugging and tuning

### Out of Scope

- matrix shape changes
- persona model changes
- framework stack changes
- charting changes
- changing the frontend answer component structure

## Current Architecture Boundary

The current rewrite already has:

- a fixed `4 x 4` matrix
- a scenario-bound runtime
- ranked visible data per cell
- fixed framework stack execution
- one-cell question routing
- a stable answer object returned to the frontend

This pass preserves those boundaries.

The work happens primarily in:

- [app/question_intelligence.py](/Users/pragyan/Workspaces/Decision%20Framework%20System/app/question_intelligence.py:1)
- [app/static/index.html](/Users/pragyan/Workspaces/Decision%20Framework%20System/app/static/index.html:1)

## Runtime Sequence

The fixed-matrix routing runtime should follow this order:

1. read persona profile
2. read question
3. detect `question_type`
4. detect `decision_family`
5. score all decision lenses
6. score all canonical perspectives
7. score all 16 cells
8. choose exactly one best-fit cell
9. rank visible data inside that cell
10. execute the framework stack
11. generate the answer

This order is important:

- `question_type` should shape routing behavior early
- `decision_family` should remain separate from `question_type`
- visible-data routing should happen after cell selection, not instead of it

## Question Type Model

The canonical fixed-matrix question types become:

- `meaning`
- `comparison`
- `threshold`
- `consequence`
- `prioritization`
- `clarification`
- `action`
- `missing_data`

### Rule

`question_type` is not the same as `decision_family`.

Example:

- `What is my variance?`
  - `question_type = meaning`
  - `decision_family = variance`

- `What should I do next?`
  - `question_type = action`
  - `decision_family = risk` or `commercial-exposure` depending on context

### Implementation Rule

The current mixed heuristics in the fixed router should be normalized so these eight question types are the only canonical output of fixed-matrix question classification.

## Decision Family Model

The current scenario-bound commercial family detection remains in place and continues to operate independently of `question_type`.

Expected active families remain:

- `contract-entitlement`
- `commercial-exposure`
- `variance`
- `bids-pricing`
- `disclosure`
- `timing`
- `risk`
- `consequence`
- `strategy`
- `data-needed`

This pass does not redesign the family taxonomy. It only clarifies that family detection and question type detection are separate stages.

## Emotion Scoring Alignment

The fixed router should adopt the following explicit emotion score model:

- `0.50 * direct_language_signal`
- `0.20 * question_type_fit`
- `0.20 * persona_bias_fit`
- `0.10 * current_ui_context`

### Definitions

- `direct_language_signal`
  - words and semantic cues in the question itself
- `question_type_fit`
  - how naturally the question type aligns to the emotion
- `persona_bias_fit`
  - the persona’s default decision or emotion tendency
- `current_ui_context`
  - current active cell, selected perspective, selected decision lens, or nearby UI state

### Expected Effect

- question wording dominates
- question type shapes the lens but does not overwhelm wording
- persona bias helps stabilize the route
- UI context acts only as a light nudge

## Perspective Scoring Alignment

The fixed router should adopt the following perspective score model:

- `0.55 * direct_language_signal`
- `0.20 * question_object_fit`
- `0.15 * persona_priority_fit`
- `0.10 * current_ui_context`

### Definitions

- `direct_language_signal`
  - explicit wording around people, cost, governance, self-risk, outcome, trust, and similar cues
- `question_object_fit`
  - whether the object of the question is naturally stakeholder, business, self-risk, or ethics-oriented
- `persona_priority_fit`
  - the persona’s weighting across canonical perspectives
- `current_ui_context`
  - current selection or recent matrix state

### Expected Effect

- the subject of the question dominates perspective routing
- persona weighting shapes ties and near-ties
- UI context nudges but should not hijack routing

## Cell Scoring Alignment

After emotion and perspective scoring, all 16 cells should be scored with the canonical fixed-matrix formula:

- `0.30 * emotion score`
- `0.30 * perspective score`
- `0.20 * persona alignment`
- `0.10 * question type compatibility`
- `0.10 * visible data fit`

### Definitions

- `emotion score`
  - the resolved score for the lens attached to that cell
- `perspective score`
  - the resolved score for the canonical perspective attached to that cell
- `persona alignment`
  - fit between the persona’s weighting model and the cell
- `question type compatibility`
  - whether this cell is naturally strong for the question type
- `visible data fit`
  - whether the cell’s visible data is semantically close to the question

### Rule

The fixed router must always return exactly one best-fit cell.

No top-two mode and no clarification loop are added in this pass.

## Visible Data Routing

Visible-data routing becomes an explicit, two-step part of the question flow:

1. use visible-data fit as one input to cell scoring
2. after choosing the winning cell, rank visible data inside that cell for execution and answer generation

### Why

The router should answer not just:

- `Which cell wins?`

but also:

- `Which visible signal inside that cell best answers the question?`

### Implementation Rule

The chosen cell’s `rankedVisibleData` remains the source of truth, but:

- visible-data fit must be clearly separated from broader heuristic scoring
- post-selection ranking inside the winning cell must be treated as a dedicated stage

## Frontend Context Additions

The backend context payload should explicitly carry the UI state required by the routing formulas.

Add or strengthen:

- active cell id
- currently selected decision lens, if user narrowed it
- currently selected perspective, if user narrowed it
- current visible matrix state
- ranked visible data for the visible cells

### Rule

This information is used only as `current_ui_context`, not as a dominant selector.

## Output Contract

The existing frontend-facing answer contract remains unchanged.

The router should continue returning:

- `mode`
- `decision_family`
- `decision_lens`
- `perspective_code`
- `target_cell_id`
- `confidence`
- `reason`

And for answer mode:

- `direct_answer`
- `why_this_answer`
- `recommended_decision`
- `decision_risk`
- `suggested_next_step`
- `reasoning_summary`
- `watch_item`
- `missing_data`
- existing backward-compatible fields already used by the frontend

## Internal Routing Trace

Internally, the router should now also produce a routing trace for tuning and debugging.

This trace should include:

- canonical `question_type`
- per-emotion scores
- per-perspective scores
- per-cell total score
- winning cell
- winning visible-data items

### Rule

This trace does not need to be shown in the UI in this pass, but it should exist in the backend result path for debugging and verification.

## Migration Rules

### Preserve

- current fixed matrix
- current framework execution
- current answer object
- current frontend answer rendering

### Replace

- mixed fixed-router classification behavior
- implicit or ad hoc score weighting
- loosely defined visible-data matching
- underused UI context in routing

### Avoid

- rewriting the entire answer system
- introducing a second routing engine
- keeping conflicting score formulas active in parallel

## File-Level Implementation Targets

### Backend

Primary changes:

- [app/question_intelligence.py](/Users/pragyan/Workspaces/Decision%20Framework%20System/app/question_intelligence.py:1)

Expected work:

- normalize fixed-matrix question types
- refactor lens scoring to match the new formula
- refactor perspective scoring to match the new formula
- refactor cell scoring to match the new formula
- separate decision family detection from question type classification
- add routing trace payloads

### Frontend

Primary changes:

- [app/static/index.html](/Users/pragyan/Workspaces/Decision%20Framework%20System/app/static/index.html:1)

Expected work:

- strengthen `buildQuestionIntelligenceContext(...)`
- include explicit UI selection state needed by the router
- preserve the existing answer consumption path

## Success Criteria

This pass is successful when:

- the router uses the canonical 8 question types
- emotion, perspective, and cell scoring follow explicit formulas
- visible-data ranking is explicitly integrated into routing
- the frontend contract remains stable
- the selected cell is more consistent with the actual question wording and active scenario
- routing behavior is easier to debug from backend trace output

## Risks

- current answer phrasing may still expose older wording quality issues even if routing improves
- UI context could become too strong if not kept to the specified weight
- preserving backward compatibility may temporarily keep some low-value compatibility helpers around

## Recommendation

Implement this as a spec-conformance pass, not a clean-slate router rewrite.

That gives:

- better routing quality
- lower regression risk
- a clearer bridge between the current rewrite and the improved routing spec
