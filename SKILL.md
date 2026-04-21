---
name: adaptive-decision-framing
description: This skill should be used when the user asks to "analyze this decision", "help me decide", "frame this decision", "break down this scenario", "show me only the important decision info", or provides a persona plus a scenario and wants the output adapted to role, emotion, mental load, urgency, or public role context.
version: 0.4.0
---

# Adaptive Decision Framing

Use this skill to turn a scenario into decision-ready information that matches the decision-maker's role, current state, and practical constraints.

The current product direction is no longer just a one-shot recommendation console. It is a
wizard-first dynamic decision matrix app. The backend decision framework remains the reasoning
core, while the UI is responsible for building context, rendering a matrix, and routing user
questions into cell-level decision insight.

The job is not to act like a generic advice engine. The job is to:

- normalize the persona into a usable profile
- parse the scenario into a human decision model
- identify what matters most right now for this specific persona
- resolve emotional interpretation into the existing emotion taxonomy only
- adapt information density, structure, and tone to the user's likely bandwidth
- score each option across weighted KPI categories to surface the strongest path
- optionally enrich a role-based persona with public internet context when requested or necessary
- keep scenario facts, public role context, and inferred assumptions clearly separated
- support wizard-first context resolution across domain, platform, persona, perspectives, and emotional framework
- expose matrix-ready outputs that let the UI show how perspective and emotional stance change what matters
- support cell-level insight for KPI focus, data needed, evidence type, action tendency, risk, and consequence

## Product Direction

The product should now be understood as:

`Context Builder -> Emotion + Perspective Matrix -> Question-Aware Highlighting -> Decision Insight`

The backend stays responsible for decision logic. The UI is the primary restructuring layer.

### Context Builder

Resolve inputs in this order:

1. `domain / industry`
2. `platform / operating context`
3. `persona`
4. `persona-dependent perspectives`
5. `2 recommended emotional frameworks`
6. `selected emotional framework`

If one of these values is already clearly present from uploaded content or prior state, auto-fill it
and skip asking again.

### Matrix Model

The matrix should be built only after the user selects one emotional framework.

- `X-axis`: persona-dependent perspectives
- `Y-axis`: operational sub-modes inside the selected emotional framework

Each matrix cell represents:

`emotion sub-mode × persona perspective`

Each cell should resolve to a structured object containing:

- KPI cluster
- evidence priority
- data requirements
- suggested chart type
- recommended action tendency
- risk pattern
- likely consequence
- likely blind spot

### Interaction Model

The matrix must support two modes:

1. `manual exploration`
   - user clicks a cell
   - the decision insight panel updates to that exact cell

2. `question-aware routing`
   - user asks a question
   - the system highlights the most relevant cell or cells
   - the decision insight panel opens automatically

The user must still be able to manually inspect neighboring cells after auto-highlighting.

## Tata Steel UK Grounding

The first implementation should be grounded in the Tata Steel UK Port Talbot EAF Transformation.

Use Tata UK-aware defaults for:

- domain
- platform / context
- persona sets
- perspective libraries
- evidence types
- chart and data mappings

The app architecture should remain generic, but the first working instantiation should be clearly
about Tata Steel UK transformation decisions, not a blank generic matrix.

Default project context:

- `domain`: industrial transformation / steel / heavy manufacturing
- `project`: Tata Steel UK Port Talbot EAF Transformation
- `platform`: Port Talbot transformation programme

Relevant Tata UK decision surfaces include:

- construction and commissioning
- scrap supply and quality
- energy and grid readiness
- customer and grade capability
- workforce transition
- grant and milestone compliance
- community and political legitimacy
- decarbonization and strategic positioning

## Inputs

Require for useful analysis:

- `domain`
- `platform` unless already inferable
- `persona` or `persona_profile`
- `scenario` or project decision question

Accept when available:

- `project`
- `decision_goal`
- `known_options`
- `emotion_signal`
- `kpi_families`
- `time_horizon`
- `stakeholders`
- `tension`
- `role_enrichment_requested`
- `perspectives`
- `recommended_emotional_frameworks`
- `selected_emotional_framework`

Treat `scenario` as the main source of truth.

Treat `persona` as explicit input, then normalize it into a common internal profile shape.

If the user gives only a role label such as `CFO`, `school principal`, or `single parent`, that is enough to start. Build missing persona detail conservatively from the scenario and label any added detail as inferred.

For the matrix app flow, the system should always resolve inputs in order, but skip prompts when a
field is already confidently known from prior state or uploaded content.

## Emotion Taxonomy

The skill uses exactly six emotion states. All emotional interpretation must resolve into one of these codes. Do not invent new states.

| Code | Name       | Orientation                               |
|------|------------|-------------------------------------------|
| A    | Cautious   | Risk-first, downside-protective           |
| B    | Strategic  | Long-horizon, thesis-protective           |
| C    | Diplomatic | Stakeholder-balancing, coalition-sensitive|
| D    | Decisive   | Action-biased, commitment-oriented        |
| E    | Analytical | Model-driven, sensitivity-aware           |
| F    | Pragmatic  | Outcome-focused, operationally grounded   |

Each emotion state carries a different KPI weight profile. The same scenario scored under Cautious (A) will rank options differently than under Decisive (D), because each mode concentrates weight on different categories.

When the user's state is ambiguous, default to the highest-confidence code and note uncertainty. Never blend codes into a new state.

## KPI Framework

The skill now uses a two-layer KPI architecture.

### Layer A: Native Scenario KPIs

These stay in the scenario's own language and should be what the user sees first.

Each native KPI should preserve, when available:

- label
- unit
- native scale
- threshold hints
- baseline note

Examples:

- patient harm rate
- affordable access loss
- disclosure deadline
- litigation exposure
- revenue at risk
- trust damage

### Layer B: Scoring Families

These are the abstract buckets the engine uses to score and compare actions.

| Family                    | Purpose                                                    |
|---------------------------|------------------------------------------------------------|
| `safety_harm`             | direct harm, severity, exposed downside                    |
| `financial_impact`        | cost, revenue, budget, economic burden                     |
| `resource_pressure`       | liquidity, staffing, near-term capacity load               |
| `regulatory_legal`        | compliance, reporting, legal and regulator exposure        |
| `urgency_time`            | deadline pressure and worsening-from-delay                 |
| `stakeholder_trust`       | affected-party trust, acceptance, relationship strain      |
| `institutional_reputation`| credibility, reputational and external-confidence risk     |
| `continuity_disruption`   | service, operating, or clinical continuity disruption      |
| `evidence_quality`        | evidence sufficiency, confidence, uncertainty              |
| `reversibility_optionality`| reversibility, optionality, ability to recover later      |
| `ethics_disclosure`       | ethical clarity, transparency, disclosure integrity        |
| `equity_access`           | affordability, access, uneven downside for vulnerable groups |

### Legacy Compatibility

The current engine still carries a smaller legacy scoring bucket set for backward compatibility with the existing UI and weighting logic:

| Category   | What it measures                                       |
|------------|--------------------------------------------------------|
| debt       | Leverage, balance-sheet risk, refinancing exposure     |
| cost       | Immediate cost increase or reduction                   |
| cash       | Short-term liquidity and cash flow impact              |
| regulatory | Compliance, legal, and regulatory risk                 |
| timeline   | Speed of execution and time-to-observable-outcome      |
| customer   | Customer trust, retention, and relationship risk       |
| rating     | Credit rating, reputation, and market perception       |
| emissions  | Environmental impact, ESG exposure                     |

The intended computational flow is:

`scenario -> native KPIs -> scoring families -> action scoring -> emotion reweighting -> recommendation`

The legacy categories remain only as an interim compatibility layer while the engine is being refactored.

When a scenario involves a domain with different natural KPIs (product, hiring, personal finance), map the scenario's actual dimensions into the closest available categories or note which categories are not applicable.

For edge cases that combine multiple operating logics in one decision, do not flatten them into a single category family too early. Examples:

- clinical safety plus ethics plus regulatory disclosure
- patient access plus institutional trust plus litigation exposure
- philanthropic mandate plus for-profit operating logic

In these cases:

- preserve the native KPI language from the scenario
- map each KPI into the closest scoring archetype only after extracting the real decision trade-off
- prefer the explicit option set from an `Options in play` section over a compressed `The call` sentence when both are present
- treat ties across all options as a scoring failure, not as a valid result

## KPI Slot Types

After scoring, KPIs are ordered into display slots. Slot order determines what the reader sees first.

| Slot                | Meaning                                                   |
|---------------------|-----------------------------------------------------------|
| priority            | Highest-weight KPIs for this emotion code                 |
| blind_spot_warning  | Under-weighted KPIs with red or yellow risk signals       |
| primary             | Remaining moderately weighted KPIs                        |
| secondary           | Lower-weight KPIs included for completeness               |

Always surface blind spot warnings even when the current emotion code assigns them low weight.

## Workflow

Follow this sequence.

### 1. Check input sufficiency

Proceed immediately when persona and scenario are both sufficient.

Ask a short follow-up only when one of these is true:

- the scenario is missing
- the scenario is too incomplete to identify the decision
- the decision-maker is unclear because persona is missing
- one missing fact blocks meaningful framing
- emotion, urgency, or mental load are too ambiguous to adapt safely

Keep clarification short and targeted. Ask one focused question rather than a survey.

### 2. Normalize the persona

Convert `persona` or `persona_profile` into a normalized internal profile.

Aim to capture:

- role label
- life or work domain
- responsibility scope
- decision authority
- primary goals
- key constraints
- risk orientation
- default time horizon
- stakeholders affected
- identity pressures

Do not force all fields to exist. Missing fields are acceptable when the scenario is still analyzable.

### 3. Optionally enrich a role-based persona

If the persona is role-based and role enrichment is requested or genuinely needed, gather public internet context about the role.

Use enrichment to improve understanding of:

- common responsibilities
- typical decision rights
- common stakeholder groups
- usual performance pressures
- common consequences and accountability exposure

Do not use internet enrichment for named real-person profiling here. This layer is for role-based personas only.

When enrichment is not explicitly requested, prefer asking one scenario question before browsing if that question is likely to produce better context than generic role research.

### 4. Extract the decision map

Read the scenario and identify:

- decision context
- trigger
- active goal
- stakes
- constraints
- explicit options
- implied options
- cues about urgency
- cues about emotional state
- cues about mental load
- social, identity, or accountability pressure
- missing facts that materially affect the decision

Also identify persona-weighted interpretation such as:

- what this persona is responsible for
- who absorbs downside
- what success and failure mean from this role
- what pressures are likely most salient

Mark each important item as one of:

- `explicit`
- `inferred`
- `uncertain`

For the underlying model, read `references/state-model.md`.

### 5. Resolve the emotional state

Resolve emotional interpretation into the existing emotion taxonomy only.

Rules:

- if the user explicitly names a valid taxonomy emotion, use it directly
- if the scenario implies emotion, map it to the closest valid taxonomy state
- if multiple taxonomy emotions are plausible, choose the highest-confidence one or note uncertainty
- do not invent blended system states outside the taxonomy

### 6. Score options across KPI categories

For each option, score it 0–2 against each relevant KPI category.

If the scenario is an edge case with mixed ethical, regulatory, operational, or clinical logic, add a scenario-specific scoring layer before the generic scorer. Use it to prevent obviously different options from collapsing into identical scores.

Then apply emotion-weighted scoring for all six emotion codes in parallel.

This produces:

- a baseline recommendation using equal weights
- six emotion-variant recommendations, one per code
- a divergence signal when a variant disagrees with the baseline

### 7. Assess adaptation pressure

Estimate how aggressively to compress or expand the output based on:

- urgency
- emotional intensity
- mental load
- stakes
- confidence in the inference quality

Do not force the output into rigid classes like `minimal` or `detailed`. Shape it dynamically.

For rendering rules, read `references/rendering-model.md`.

### 8. Render the output

Use the same response spine each time, but compress or expand it dynamically:

- `Decision Snapshot`
- `Persona Lens`
- `Public Role Context`
- `Relevant Facts`
- `Possible Options`
- `What Is Driving The Decision`
- `Key Trade-Offs`
- `Consequence Risk`
- `Blind Spots`
- `Missing But Important`
- `Inferred Assumptions`
- `Suggested Next Step`

Rules:

- keep `Decision Snapshot` and `Relevant Facts` in almost all cases
- show `Persona Lens` when persona meaningfully changes weighting
- show `Public Role Context` only when internet enrichment was actually used and it materially improves the framing
- show `Consequence Risk` to flag the bias risk of the active emotion mode
- show `Blind Spots` to surface under-weighted KPIs with risk signals
- omit sections that add no value in the current state

### 9. Keep information layers separate

Never mix these layers:

- scenario facts
- public role context
- inferred assumptions

If adding implied options or derived facts, label them clearly.

## Source Priority

When public role context is used, priority must be:

1. scenario facts supplied by the user
2. explicit persona details supplied by the user
3. public role context from internet research
4. internal inference

Public role context may sharpen interpretation, but it must never override direct scenario facts.

## Webapp Mode

When the skill is invoked via the local webapp (upload → analyze → render loop), the workflow is the same but inputs arrive as a parsed markdown file.

The uploaded file should contain at minimum:

- `Persona` section
- `Scenario` section

It may also include:

- `Time horizon`
- `Stakeholders`
- `KPI families`
- `Decision call`
- `Tension`
- `Role enrichment: true`

The backend parses the file, runs the full pipeline for all six emotion codes, and returns one JSON payload. The frontend renders an interactive decision console with an emotion switcher, KPI matrix, and blind spot panel.

If parsing fails or required fields are missing, the app renders a targeted clarification prompt rather than an empty result.

## Output Rules

### High urgency + high emotion + high mental load

- cut word count sharply
- lead with the decision and top facts
- reduce branching
- show only meaningfully distinct options
- emphasize immediate differences and consequences
- keep the persona lens very short
- use direct phrasing

### Low urgency + stable emotion + low mental load

- include more context
- include second-order trade-offs
- preserve nuance and uncertainty
- include broader implications when useful

### High stakes + low urgency

Preserve nuance even if the scenario is emotionally charged.

### Emotionally intense + low stakes

Reduce friction and tone pressure without overstating risk.

## Response Standard

Every answer should help the user decide faster by improving relevance, not by pretending certainty.

Prefer:

- fewer but sharper facts
- distinct options over exhaustive lists
- short explanations when the user is overloaded
- richer comparisons when the user has bandwidth
- persona-specific trade-off framing when it changes the decision

Avoid:

- generic motivational advice
- unsupported certainty
- long background summaries when the situation is urgent
- pretending to know the persona's state when the scenario does not support it
- presenting public role research as if it were scenario fact

## Confidence Behavior

- High confidence: render directly
- Medium confidence: render directly and note important uncertain inferences
- Low confidence: ask before adapting aggressively

## Close Call Behavior

When the top two options score within a small margin, note this explicitly. Do not force a clean recommendation when the scoring is ambiguous. Suggest one targeted fact-gather or sanity check instead.

## References

- `references/state-model.md`
Use for the internal decision map, emotion codes, KPI categories, persona-weighted valuation, and labeling rules.

- `references/rendering-model.md`
Use for adaptation logic across urgency, emotion, mental load, role-sensitive framing, and KPI slot ordering.

- `references/examples.md`
Use for worked examples across multiple personas, taxonomy states, and role-enrichment cases.

- `references/upload-format.md`
Use for the webapp markdown upload format, required and optional sections, and backend parsing behavior.
