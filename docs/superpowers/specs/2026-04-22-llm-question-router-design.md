# LLM Question Router Design

Date: 2026-04-22

## Goal

Replace the current frontend-heavy question routing logic with a backend LLM router that understands the active scenario context, returns structured routing decisions, and keeps the matrix as the primary answer surface.

This design is intended to solve the current instability in the question box, especially for the `VO112` scenario, where broad, perspective-specific, and follow-up questions are not being mapped reliably to the correct matrix cell.

## Product shape

The question box should behave like an intelligent scenario-aware router, not like a generic chatbot.

The app should continue to work as:

- `Context Builder`
- `Matrix`
- `Insight Panel`
- `Question Layer`

The `Question Layer` becomes LLM-backed, but its purpose remains constrained:

- understand the question
- decide whether to answer, clarify, or suggest
- route to the correct matrix cell when possible
- let the matrix and insight panel remain the visible answer system

The LLM should not become the primary answer renderer.

## Architecture

The system should be restructured into three cooperating layers:

1. `Frontend Matrix Layer`
2. `Backend LLM Router`
3. `Existing Matrix/Insight Logic`

### Frontend Matrix Layer

The frontend should continue to own:

- question input UI
- sending the current context payload
- displaying route notes
- rendering clarification prompts
- rendering recovery suggestion chips
- rendering follow-up chips
- applying the returned matrix highlight
- populating the insight panel from the selected cell

The frontend should stop owning:

- semantic question routing
- broad-question interpretation
- fallback question generation logic
- special-case `VO112` question heuristics
- cross-perspective question scoring

### Backend LLM Router

The backend router becomes the semantic decision layer for questions.

It should:

- accept the current scenario context and question
- prompt a real LLM with a constrained routing prompt
- return structured JSON only
- decide one of three modes:
  - `answer`
  - `clarify`
  - `suggest`

### Existing Matrix/Insight Logic

The matrix cell model and insight rendering should remain the source of truth for:

- recommended action
- primary risk
- likely consequence
- KPI list
- data to inspect
- chart/evidence block
- blind spot

The router should select a cell. The cell should still drive the displayed answer.

## Request / response contract

The frontend should send a structured request to a new backend endpoint such as:

- `POST /question-intelligence`

### Request payload

The payload should include:

- `persona_id`
- `scenario_id`
- `framework_code`
- `active_cell_id`
- `question`
- `clarification_context` when applicable
- a compact scenario summary
- a compact persona tension summary
- visible matrix perspectives
- visible emotional modes
- compact matrix cell inventory

The backend should not have to infer the visible matrix from scratch. It should reason over the exact current decision surface.

### Response payload

The backend should return structured JSON in this shape:

- `status`
- `mode`
- `persona_id`
- `scenario_id`
- `framework_code`
- `emotion_mode`
- `perspective_code`
- `target_cell_id`
- `confidence`
- `reason`
- `clarifying_question`
- `suggested_questions`
- `follow_up_questions`

Optional fields can be omitted when not relevant, but the JSON structure should remain stable.

## LLM prompt design

The model should be prompted as a constrained routing engine, not as a freeform assistant.

### Prompt inputs

Each prompt should include:

- active persona
- active scenario
- active framework
- scenario summary
- persona tension
- visible perspectives
- visible emotional modes
- compact matrix cell inventory
- user question
- optional prior clarification context

### Matrix cell inventory shape

Each cell passed to the model should be compact and structured:

- `cell_id`
- `emotion_mode`
- `perspective`
- `primary_kpi`
- `supporting_kpis`
- `recommended_action`
- `risk`
- `consequence`
- `question_tags`

The prompt should explicitly instruct the model:

- do not invent cells
- do not invent scenarios
- do not invent KPIs
- stay inside the supplied scenario
- if confidence is low, ask exactly one clarification
- if the question is too broad, return 3 to 5 better scenario-specific questions
- if confidence is high, return the best-fit cell

### Output format

The prompt should force JSON-only output.

No markdown.
No prose outside the JSON object.

This keeps parsing reliable and makes failure handling much simpler.

## Routing modes

The backend LLM router must always choose exactly one mode.

### `answer`

Use this when:

- one matrix cell is a clear best fit
- there is no critical ambiguity
- confidence is high enough to highlight a cell safely

The response should include:

- `target_cell_id`
- inferred `emotion_mode`
- inferred `perspective_code`
- `reason`
- `follow_up_questions`

### `clarify`

Use this when:

- the question is relevant
- but one important distinction is missing

Examples:

- unclear perspective
- unclear stakeholder
- multiple plausible cells
- ambiguous path words like `safest` or `best`

The response should include:

- one short `clarifying_question`
- no `target_cell_id`
- optional scoped `suggested_questions`

### `suggest`

Use this when:

- the question is too broad
- malformed
- weakly related
- or cannot be mapped to one cell safely

Examples:

- `best solution`
- `help`
- `what now`
- `tell me the answer`

The response should include:

- 3 to 5 scenario-specific `suggested_questions`
- no `target_cell_id`
- no matrix highlight

The LLM should never answer vaguely when it should clarify or suggest.

## Frontend behavior

The frontend should trust the backend routing result and stop reinterpreting it through another heuristic layer.

### If mode is `answer`

The frontend should:

- switch context if needed
- set the returned `target_cell_id`
- highlight the cell
- update the insight panel from that cell
- display the returned `reason`
- show `follow_up_questions`

### If mode is `clarify`

The frontend should:

- not highlight a cell yet
- display the `clarifying_question`
- show any suggestion chips returned
- preserve the original question while awaiting the user’s clarification

### If mode is `suggest`

The frontend should:

- not highlight any cell
- display a short “too broad” style note
- show 3 to 5 scenario-specific suggestion chips

The matrix must remain the primary visual anchor.
The question area should assist navigation, not turn into a chat transcript.

## Runtime and safety

Because this design uses a real LLM API at runtime, operational rules are required.

### Secret handling

The API key must live only in the backend environment.

Never expose it to the frontend.

### Timeout and fallback

If the LLM call:

- times out
- fails
- returns invalid JSON

the app should:

- keep the existing matrix state unchanged
- return a short fallback message
- optionally use the current deterministic router as a fallback path

### Scenario boundary

The model must stay inside the supplied scenario context.

It should not invent:

- other scenarios
- external facts
- missing KPIs
- unsupported personas

### Logging

The backend should log each request with:

- question
- mode
- chosen cell
- confidence
- whether fallback was used

This is required to debug routing failures systematically.

### Cost control

The prompt should stay compact:

- scenario summary, not full raw markdown
- compact matrix cell inventory, not full panel prose
- only current scenario in v1

## First implementation scope

The first implementation should be intentionally narrow.

### In scope

- add a backend LLM routing endpoint
- support the current selected scenario only
- support `answer | clarify | suggest`
- return structured JSON only
- let the frontend highlight the returned matrix cell
- let the frontend render clarification and suggestion chips
- support follow-up question generation after a successful answer
- work especially well for `VO112`

### Out of scope

- full multi-turn chat history UX
- cross-scenario search in v1
- replacing the insight panel with LLM prose
- modifying the matrix schema
- external web search

## Recommended implementation order

1. Add backend endpoint and request/response contract
2. Add compact scenario + matrix context packer
3. Add LLM prompt builder and JSON parser
4. Add backend mode handling: `answer`, `clarify`, `suggest`
5. Update frontend to consume backend route results directly
6. Keep deterministic fallback for runtime failure
7. Tune `VO112` prompts and examples first

## Success criteria

This change is successful when:

- broad prompts no longer highlight random cells
- perspective-specific questions highlight the correct cell
- clarification happens only when needed
- suggestion chips are scenario-relevant
- `VO112` routes stop collapsing into the first box
- the frontend no longer fights the backend route result
