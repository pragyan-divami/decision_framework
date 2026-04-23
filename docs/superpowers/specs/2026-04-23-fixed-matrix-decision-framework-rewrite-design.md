# Fixed Matrix Decision Framework Rewrite

## Purpose

This spec replaces the current mixed KPI-first / heuristic routing behavior with a fixed decision-framework engine driven by:

- `decision_framework_matrix_spec.md`
- `decision_model_definitions_spec.md`
- `decision_model_execution_logic.md`
- `decision_model_question_routing_logic.md`
- `decision_response_generation_templates_v2.md`

The result should be a persona-and-scenario-driven application where:

- the matrix is always a fixed `4 x 4`
- each cell has a fixed framework stack from the matrix spec
- the matrix shows light summaries, not KPI tiles
- questions route to exactly one best-fit cell
- the final answer is generated from the selected cell, its framework stack, and scenario-derived visible data

## Goals

- Make the matrix a true decision-support architecture instead of a KPI display.
- Keep persona-specific language in the UI while using canonical internal structure.
- Make routing and answer generation traceable from question -> cell -> framework stack -> answer.
- Remove the old ambiguity where answers are partly generated from generic heuristics and partly from matrix state.

## Non-Goals

- Cross-scenario routing
- Multi-cell answer mode
- Clarification loops
- Top-two-cell display
- Internet retrieval as part of the core decision engine
- Preserving the old KPI-first engine as a parallel primary path

## Architecture

The rewritten system has five layers:

1. Persona + Scenario Input Layer
2. Matrix Configuration Layer
3. Execution Layer
4. Question Routing Layer
5. Response Layer

The runtime sequence is:

1. load persona
2. load scenario
3. generate fixed 4 x 4 matrix
4. apply persona modifiers to visible data ranking and phrasing
5. classify question
6. score decision lenses
7. score canonical perspectives
8. score all 16 cells
9. select exactly one best-fit cell
10. rank visible data inside that cell
11. run framework stack execution
12. generate final answer object
13. highlight the selected matrix cell

## Matrix Model

### Fixed Matrix

The matrix is always `4 x 4`.

#### X-Axis: Decision Lens

- Cautious
- Strategic
- Decisive
- Analytical

#### Y-Axis: Canonical Perspective

- Self / Personal Risk
- Stakeholder / People
- Business / Outcome
- Ethics / Governance

### Persona-Specific Perspective Labels

The UI should show persona-specific perspective labels, but each label must map to one of the four canonical perspectives.

Example:

- UI: `Capital / Funding Exposure`
- Canonical: `Business / Outcome`

This preserves:

- stable internal routing and execution
- persona-relevant wording in the UI

### Fixed Framework Stack Per Cell

Each cell must use the exact framework stack defined in the matrix spec. Persona does not swap models in or out.

Each cell contains:

- `primary_fit`
- `secondary_fit`
- `support_fit`
- `decision_style`
- `best_data_to_show`
- `why_this_data`
- `persona_adjustment`

Scenario changes do not alter framework stacks. Scenario changes only alter:

- the scenario-derived visible data generated for each cell
- the answer generated from the selected cell

## Persona and Scenario Input Layer

### Inputs

Use existing backend persona and scenario files as the source of truth.

The normalized persona profile should include:

- `persona_id`
- `role`
- `mandate`
- `primary_accountabilities`
- `key_risks`
- `priority_stakeholders`
- `authority_level`
- `governance_constraints`
- `default_decision_bias`

The scenario profile should include:

- `scenario_id`
- `scenario_title`
- `scenario_summary`
- `tension`
- `decision_context`
- `options`
- `source KPI families`

### Persona Rules

Persona does not change matrix structure.

Persona changes:

- perspective weighting
- visible data ranking within each cell
- answer phrasing
- stakeholder emphasis
- risk ordering

## Visible Data Generation

### Principle

The matrix must show decision-support data, not KPI names as the primary payload.

KPIs remain source evidence only.

### Visible Data Sources

Visible data should be derived from:

- persona profile
- selected scenario
- scenario tension
- scenario options
- decision context notes
- KPI families as raw evidence

### Cell Output

For each cell, generate ranked visible data items aligned to that cell’s `best_data_to_show` definition.

Examples:

- worst-case downside
- reversibility of the choice
- confidence / certainty level
- stakeholder map
- trust impact
- expected value
- option value
- operational bottleneck
- time window for action
- threshold / red line
- missing evidence
- defensibility over time

### Data Ranking Logic

Rank visible data according to the execution spec:

1. perspective relevance
2. primary model relevance
3. emotion relevance
4. persona relevance
5. secondary/support correction relevance

Use the weighted model:

- `0.30 * perspective relevance`
- `0.30 * primary model relevance`
- `0.20 * emotion relevance`
- `0.15 * persona relevance`
- `0.05 * correction relevance`

### Implementation Rule

Cells should show a light preview of the top visible data, not the full ranked list.

The full matched visible data appears only in the answer area after:

- question routing, or
- manual cell click

## Question Routing Layer

### Inputs

The router accepts:

- active persona profile
- active scenario profile
- full current 4 x 4 matrix state
- optional currently selected lens/perspective in the UI
- user question

### Question Types

The router must classify the question into one of:

- `meaning`
- `comparison`
- `threshold`
- `consequence`
- `prioritization`
- `clarification`
- `action`
- `missing_data`

### Decision Lens Scoring

Use the routing spec categories:

- direct language signal
- question type fit
- persona bias fit
- current UI context

### Perspective Scoring

Use:

- direct language signal
- question object fit
- persona priority fit
- current UI context

### Cell Scoring

Every question must score all 16 cells using:

- `0.30 * emotion score`
- `0.30 * perspective score`
- `0.20 * persona alignment`
- `0.10 * question type compatibility`
- `0.10 * visible data fit`

### Deterministic Selection Rule

The router always returns exactly one best-fit cell.

There is no:

- top-two-cell display
- clarification loop
- explicit no-answer mode in v1

Low confidence is handled through answer phrasing and confidence output, not alternate UI flow.

## Execution Layer

Once a cell is selected, execution follows:

1. load selected cell
2. load `primary_fit`, `secondary_fit`, `support_fit`
3. take matched visible data
4. apply primary model logic
5. apply secondary correction
6. apply support feasibility / guardrail logic
7. determine final answer mode
8. pass execution output to response templates

### Model Roles

#### Primary Fit

- drives the main reasoning pattern
- decides what matters most

#### Secondary Fit

- corrects the blind spot of the primary model
- prevents extreme outputs

#### Support Fit

- ensures feasibility, practicality, and safety

### Output Modes

Use the response-template modes:

- `direct_recommendation`
- `comparative_recommendation`
- `conditional_recommendation`
- `need_more_data`

## Response Layer

The final response must be generated from:

- selected cell
- framework stack
- matched visible data
- execution output
- persona tone adjustment

### Required Outputs

- `recommended_decision`
- `decision_risk`
- `suggested_next_step`

### Optional Supporting Outputs

- `reasoning_summary`
- `confidence`
- `watch_item`
- `missing_data`

### Answer Area Structure

The answer area must contain two layers.

#### Decision Answer

- recommended decision
- decision risk
- suggested next step

#### Why This Answer

- selected cell
- framework stack
- matched visible data
- reasoning summary
- confidence

## UI Behavior

### Matrix

The matrix always shows all 16 cells.

Each cell shows only a light summary:

- decision lens
- persona-specific perspective label
- framework stack hint
- short visible-data preview

Cells do not show:

- full answer
- long reasoning trace
- large KPI lists

### Answer Area

The answer area is the main reasoning surface.

It updates when:

- a question is asked, or
- a cell is clicked

### Highlighting

Exactly one matrix cell must be highlighted.

The highlighted cell must always match the selected execution cell shown in the answer area.

### Header

When persona and scenario are selected:

- header title = scenario name
- subheader = full scenario explanation
- persona remains visible as the active role context

## Migration Plan

This rewrite should replace the current mixed model, not sit beside it.

### Remove or Isolate

- old KPI-first cell generation path
- old heuristic question router as a primary engine
- old answer-generation path that writes directly from cell text or KPI text

### Keep and Adapt

- persona/scenario parsing from existing backend files
- existing server/bootstrap endpoints where possible
- existing static app shell if it can host the new engine cleanly

## Implementation Slices

1. Add canonical decision-lens and perspective matrix definitions
2. Add persona-specific UI label mapping to canonical perspectives
3. Build visible-data generation layer from current persona/scenario files
4. Replace current cell builder with fixed 4 x 4 matrix builder
5. Replace question router with spec-based routing engine
6. Add framework execution layer
7. Add response-template generator
8. Update answer area and matrix UI bindings
9. Remove or isolate old KPI-first answer logic

## Acceptance Criteria

- The matrix is always `4 x 4`
- Each cell uses the fixed framework stack from the matrix spec
- Persona-specific perspective labels appear in the UI
- Matrix cells show summary decision-support data, not KPI lists
- Question routing always selects exactly one cell
- The answer is generated from:
  - selected cell
  - matched visible data
  - framework execution
  - response templates
- Clicking a cell produces the same answer structure as routed questions
- Highlighted cell and answer area never drift out of sync

## Risks

- Partial migration will leave the old and new engines competing
- Reusing old KPI-first answer code will weaken trust and consistency
- Persona label mapping can become inconsistent if not normalized centrally
- Visible-data generation can become vague if KPI evidence is not translated carefully into decision-support language

## Recommendation

Implement this as a true engine rewrite behind the existing app shell:

- keep the current UI shell where useful
- replace the matrix engine, router, execution layer, and answer generator

That is the shortest path to a system that actually behaves like the decision framework described in the specs, rather than a KPI dashboard with routed prose.
