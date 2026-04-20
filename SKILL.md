---
name: adaptive-decision-framing
description: This skill should be used when the user asks to "analyze this decision", "help me decide", "frame this decision", "break down this scenario", "show me only the important decision info", or provides a persona plus a scenario and wants the output adapted to role, emotion, mental load, urgency, or public role context.
version: 0.3.0
---

# Adaptive Decision Framing

Use this skill to turn a scenario into decision-ready information that matches the decision-maker's role, current state, and practical constraints.

The job is not to act like a generic advice engine. The job is to:

- normalize the persona into a usable profile
- parse the scenario into a human decision model
- identify what matters most right now for this specific persona
- resolve emotional interpretation into the existing emotion taxonomy only
- adapt information density, structure, and tone to the user's likely bandwidth
- score each option across weighted KPI categories to surface the strongest path
- optionally enrich a role-based persona with public internet context when requested or necessary
- keep scenario facts, public role context, and inferred assumptions clearly separated

## Inputs

Require for useful analysis:

- `persona` or `persona_profile`
- `scenario`

Accept when available:

- `decision_goal`
- `known_options`
- `emotion_signal`
- `kpi_families`
- `time_horizon`
- `stakeholders`
- `tension`
- `role_enrichment_requested`

Treat `scenario` as the main source of truth.

Treat `persona` as explicit input, then normalize it into a common internal profile shape.

If the user gives only a role label such as `CFO`, `school principal`, or `single parent`, that is enough to start. Build missing persona detail conservatively from the scenario and label any added detail as inferred.

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

The skill evaluates options across eight KPI categories. Each is scored 0–2 per option.

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

Each emotion code weights these categories differently. Cautious (A) concentrates on debt, cost, and cash. Strategic (B) and Decisive (D) shift weight toward timeline and emissions. Analytical (E) distributes weight more evenly across modelable categories.

When a scenario involves a domain with different natural KPIs (product, hiring, personal finance), map the scenario's actual dimensions into the closest available categories or note which categories are not applicable.

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
