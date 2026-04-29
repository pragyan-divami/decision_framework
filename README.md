# Decision Framework System

Decision Framework System is a persona-and-scenario-driven decision-support application built around a fixed `4 × 4` matrix. It helps a user understand a difficult decision through a stable set of decision lenses and perspectives, then routes each question to exactly one best-fit matrix cell, applies the correct decision-model stack, and returns a traceable answer.

This repository is no longer the older "6 emotional lenses reweighting KPIs" prototype. The current system is a fixed-matrix decision engine with explicit routing, weighting, and execution rules.

## Quick Start

### Run locally

```bash
python3 app/server.py
```

Then open:

```text
http://127.0.0.1:8010
```

### Optional external-answer mode

```bash
OPENAI_API_KEY="your_key_here" OPENAI_EXTERNAL_MODEL="gpt-5.4" python3 app/server.py
```

Without an API key, the system still runs fully in scenario-bound local mode.

## Why This Exists

Most decision tools fail in one of two ways:

- they stay too generic and produce vague advice
- they become dashboards of raw KPIs without explaining what those signals mean for the actual decision

This system sits between those extremes.

It is designed to answer:

- what matters in this scenario for this persona
- which decision lens should dominate right now
- which supporting evidence is most decision-relevant
- what the recommended decision is
- what risk, missing data, and next step come with that recommendation

## Core System Model

The system has five runtime layers:

1. `Persona + Scenario Input Layer`
2. `Matrix Configuration Layer`
3. `Visible Data Generation Layer`
4. `Question Routing Layer`
5. `Execution + Response Layer`

The runtime flow is:

1. load persona
2. load scenario
3. generate the fixed `4 × 4` matrix
4. generate per-cell visible decision-support data from backend scenario/persona inputs
5. classify the user question
6. score decision lenses
7. score canonical perspectives
8. score all 16 cells
9. select exactly one best-fit cell
10. rank visible data inside that cell
11. execute the cell’s framework stack
12. generate the answer object
13. highlight the selected matrix cell in the UI

### Compact architecture diagram

```text
Persona + Scenario Inputs
        ↓
Normalized Profiles
        ↓
Fixed 4×4 Matrix
        ↓
Per-cell Visible Data Generation
        ↓
Question Routing
  - question type
  - decision family
  - lens scoring
  - perspective scoring
  - 16-cell scoring
        ↓
Winning Cell
        ↓
Visible Data Match Inside Cell
        ↓
Framework Stack Execution
  - primary model
  - secondary correction
  - support model
        ↓
Structured Answer + Highlighted Cell
```

## Fixed 4×4 Decision Framework

The matrix is always fixed.

### X-axis: Decision Lens

- `Cautious`
- `Strategic`
- `Decisive`
- `Analytical`

### Y-axis: Canonical Perspective

- `Self / Personal Risk`
- `Stakeholder / People`
- `Business / Outcome`
- `Ethics / Governance`

### Persona-specific UI labels

The UI can show persona-specific wording, but every visible perspective still maps to one of the four canonical internal perspectives.

Example:

- UI label: `Capital / Funding Exposure`
- Canonical perspective: `Business / Outcome`

This preserves:

- stable internal routing
- stable model selection
- persona-specific language in the interface

## What Each Cell Contains

Each of the 16 cells is not a freeform tile. It has a fixed internal definition.

Each cell contains:

- `primary_fit`
- `secondary_fit`
- `support_fit`
- `decision_style`
- `best_data_to_show`
- `why_this_data`
- `persona_adjustment`

These are defined by the matrix spec and do not change per scenario.

Scenario changes only affect:

- which visible data is generated inside that cell
- how visible data is ranked
- the answer generated after routing

## Persona and Scenario Input Model

The backend normalizes persona and scenario data before matrix generation.

### Persona profile includes

- `persona_id`
- `role`
- `mandate`
- `primary_accountabilities`
- `key_risks`
- `priority_stakeholders`
- `authority_level`
- `governance_constraints`
- `default_decision_bias`
- `default_emotion_tendency`
- `default_perspective_weights`

### Scenario profile includes

- `scenario_id`
- `scenario_title`
- `scenario_summary`
- `tension`
- `decision_context`
- `options`
- `source KPI families`
- `scenario kinds`

Persona does not change matrix shape or framework-stack assignment.

Persona changes:

- visible-data ranking
- perspective weighting
- answer phrasing
- stakeholder emphasis
- risk ordering

## Visible Data Generation

The matrix does not primarily display KPI names.

KPIs are treated as source evidence. The system transforms that evidence into decision-support data appropriate to each cell.

### Inputs to visible-data generation

- normalized persona profile
- normalized scenario profile
- scenario tension
- scenario options
- decision context
- KPI families as raw evidence

### Examples of visible data types

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

### Visible-data weighting method

Visible data is ranked with this weighting model:

- `0.30 * perspective relevance`
- `0.30 * primary model relevance`
- `0.20 * emotion relevance`
- `0.15 * persona relevance`
- `0.05 * correction relevance`

That means the system is not simply asking "what KPI exists?" It is asking:

- which evidence is most relevant to this perspective
- which evidence best fits the primary decision model in the cell
- which evidence best matches the active decision lens and persona

## Decision Model Selection Method

Decision models are not chosen ad hoc for each question.

Each matrix cell already has a fixed framework stack:

- `primary_fit`
- `secondary_fit`
- `support_fit`

### How the stack works

- `primary_fit`
  - defines the dominant reasoning style for the cell
- `secondary_fit`
  - corrects the blind spot of the primary model
- `support_fit`
  - makes the answer executable, safe, and operationally grounded

Example stack shape:

- `Expected Utility -> OODA -> Dual-Process`
- `OODA -> Recognition-Primed Decision -> Bounded Rationality`

The question router does **not** pick a new model stack dynamically. It picks a cell. The selected cell already determines the correct model stack.

So the selection order is:

1. select persona
2. select scenario
3. route question to one cell
4. inherit that cell’s framework stack
5. execute the answer through that stack

## Question Routing Model

The routing layer is the main selector of *where* a question should land inside the matrix.

### Canonical question types

The fixed-matrix router classifies each question into one of:

- `meaning`
- `comparison`
- `threshold`
- `consequence`
- `prioritization`
- `clarification`
- `action`
- `missing_data`

### Important rule

`question_type` is separate from `decision_family`.

Example:

- `What is my variance?`
  - `question_type = meaning`
  - `decision_family = variance`

- `What should I do next?`
  - `question_type = action`
  - `decision_family = risk` or `commercial-exposure` depending on the active scenario

## Weighting and Scoring Method

The current router uses explicit score formulas rather than vague heuristics.

### Emotion score formula

- `0.50 * direct_language_signal`
- `0.20 * question_type_fit`
- `0.20 * persona_bias_fit`
- `0.10 * current_ui_context`

#### Meaning

- `direct_language_signal`
  - the wording of the question itself
- `question_type_fit`
  - how naturally the question type maps to a lens
- `persona_bias_fit`
  - the persona’s normal decision tendency
- `current_ui_context`
  - currently active cell, selected perspective, or selected decision lens

### Perspective score formula

- `0.55 * direct_language_signal`
- `0.20 * question_object_fit`
- `0.15 * persona_priority_fit`
- `0.10 * current_ui_context`

#### Meaning

- `direct_language_signal`
  - wording around trust, money, governance, schedule, self-risk, stakeholders, and similar cues
- `question_object_fit`
  - what the question is actually about
- `persona_priority_fit`
  - how strongly the persona tends to weight each perspective
- `current_ui_context`
  - current selection or recent matrix state

### Cell score formula

Once lens and perspective scores exist, all 16 cells are scored with:

- `0.30 * emotion score`
- `0.30 * perspective score`
- `0.20 * persona alignment`
- `0.10 * question type compatibility`
- `0.10 * visible data fit`

This is the core selection method that decides which matrix cell becomes active for a given question.

### Deterministic selection rule

The router always returns exactly one best-fit cell.

This version does **not** support:

- top-two cell display
- multi-cell answers
- clarification-loop expansion as a primary mode

## Visible-data Routing Inside the Winning Cell

The system does not stop at:

- `Which cell wins?`

It also performs:

- `Which visible data inside that cell best answers the question?`

This is a separate stage after cell selection.

That gives the system a much stronger answer chain:

- persona
- scenario
- question type
- decision lens
- perspective
- winning cell
- winning visible-data items
- framework stack execution
- final answer

## Execution Layer

After a cell is selected, the answer is generated in a fixed order:

1. load selected cell
2. load `primary_fit`, `secondary_fit`, and `support_fit`
3. load matched visible data
4. apply the primary model
5. apply the secondary correction
6. apply the support model
7. generate the answer object

This makes the output traceable rather than improvised.

## Answer Generation Model

The frontend answer contract is structured. The answer layer is not supposed to emit random prose.

### Main answer fields

- `recommended_decision`
- `decision_risk`
- `suggested_next_step`
- `reasoning_summary`
- `watch_item`
- `missing_data`
- `answer_mode`

### Additional trace fields

- `decision_family`
- `decision_lens`
- `target_cell_id`
- `supporting_kpis`
- `evidence_used`

The intended user experience is:

- matrix gives a light preview
- selected answer gives the executive recommendation
- detail and answer layers reveal the reasoning and evidence underneath

## Frontend Experience

The UI is built around:

- a light summary shell
- a fixed `4 × 4` matrix workspace
- a `Decision Detail` panel
- a separate `Question Answer` panel

### Intended interaction model

- clicking a matrix cell shows the detail for that cell
- asking a question routes to exactly one best-fit cell
- the routed cell is highlighted in the matrix
- the answer layer shows:
  - main answer
  - context
  - risk
  - next step
  - supporting cell
  - evidence used

## Repository Structure

Key files and directories:

- [app/server.py](app/server.py)
  - HTTP server entrypoint
- [app/question_intelligence.py](app/question_intelligence.py)
  - question routing, scoring, and answer orchestration
- [app/fixed_matrix.py](app/fixed_matrix.py)
  - fixed matrix definitions, scenario/persona normalization, visible-data generation, and cell execution helpers
- [app/matrix_catalog.py](app/matrix_catalog.py)
  - matrix bootstrap and runtime catalog assembly
- [app/static/index.html](app/static/index.html)
  - current frontend shell, matrix UI, detail panel, and answer layer
- [docs/superpowers/specs](docs/superpowers/specs)
  - design specs for matrix rewrite, routing conformance, and UI shell changes
- `SKILL.md`
  - skill entrypoint for agent-assisted use

## How To Run

### Local web app

Start the backend:

```bash
python3 app/server.py
```

Then open:

```text
http://127.0.0.1:8010
```

### Optional external-answer mode

If you want the question layer to use OpenAI-backed external answering where supported, run the server with:

```bash
OPENAI_API_KEY="your_key_here" OPENAI_EXTERNAL_MODEL="gpt-5.4" python3 app/server.py
```

Without an API key, the app still runs on the local scenario-bound routing path.

## Key Design Docs

The most important current specs are:

- [2026-04-23-fixed-matrix-decision-framework-rewrite-design.md](docs/superpowers/specs/2026-04-23-fixed-matrix-decision-framework-rewrite-design.md)
- [2026-04-23-fixed-matrix-decision-framework-rewrite-implementation-plan.md](docs/superpowers/specs/2026-04-23-fixed-matrix-decision-framework-rewrite-implementation-plan.md)
- [2026-04-29-fixed-matrix-routing-conformance-pass-design.md](docs/superpowers/specs/2026-04-29-fixed-matrix-routing-conformance-pass-design.md)
- [2026-04-29-light-shell-summary-bar-and-single-detail-panel-design.md](docs/superpowers/specs/2026-04-29-light-shell-summary-bar-and-single-detail-panel-design.md)
- [2026-04-29-light-shell-summary-bar-and-single-detail-panel-implementation-plan.md](docs/superpowers/plans/2026-04-29-light-shell-summary-bar-and-single-detail-panel-implementation-plan.md)

## Current Limitations

The system is intentionally opinionated and still evolving.

Current boundaries and limitations include:

- routing returns exactly one best-fit cell rather than multi-cell or top-two answers
- the core engine is scenario-bound; cross-scenario synthesis is not the default behavior
- framework stacks are fixed per cell and not dynamically swapped per question
- the answer system is structured for executive decision support, not open-ended freeform analysis
- visible-data generation quality depends on the richness of the scenario/persona backend inputs
- external-answer mode is optional and should not be treated as the primary core-engine path
- the frontend shell is still under active iteration even though the matrix/runtime architecture is already established

These limitations are design choices in some areas and active roadmap items in others.

## Current State of the Project

The current project state is:

- fixed `4 × 4` matrix runtime is active
- routing uses explicit question-type, perspective, lens, and cell weighting
- answer generation is structured
- UI shell is in active iteration

The most important architectural rule to keep in mind is:

> the system does not answer directly from raw scenario text or raw KPI text; it answers from the selected matrix cell, the matched visible data inside that cell, and the fixed framework stack attached to that cell.
