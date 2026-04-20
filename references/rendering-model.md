# Rendering Model

## Purpose

Use this reference to shape the answer after the scenario has been mapped.

Adapt four things dynamically:

- information density
- structural complexity
- tone pressure
- persona-sensitive trade-off framing

Do not use rigid output classes. Use continuous judgment.

## Core Rendering Sections

The preferred response spine is:

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

Keep `Decision Snapshot` and `Relevant Facts` in almost all cases.

Show `Persona Lens` when the persona materially changes weighting.

Show `Public Role Context` only when role enrichment was used and the generic role context improves the framing.

Show `Consequence Risk` to name the specific bias introduced by the active emotion code.

Show `Blind Spots` when under-weighted KPIs carry meaningful risk signals.

## Section Rules

### Decision Snapshot

State:

- what decision is being made
- who is making it
- what matters most right now

### Persona Lens

Briefly explain why the decision looks the way it does for this persona.

Good content:

- what this persona is optimizing for
- what risks matter most from their position
- what accountability or identity pressure is shaping the choice

The template follows the active emotion code:

- Cautious: concentrates attention on stability KPIs
- Strategic: weights structural and long-horizon KPIs
- Diplomatic: prioritizes coordination and stakeholder KPIs
- Decisive: favors fast-feedback KPIs
- Analytical: emphasizes modelable KPIs
- Pragmatic: favors balanced, outcome-facing KPIs

### Public Role Context

Use only when browsing-backed role enrichment was used.

Keep it short and clearly separate from scenario facts.

Good content:

- what the role usually owns
- what the role is usually judged on
- what pressures commonly shape decisions in that role

### Relevant Facts

Show only facts that materially affect the decision. Prioritize by urgency, stakes, and salience.

### Possible Options

Include:

- options explicitly present in the scenario
- implied options when they add value

When many options exist, cluster or collapse similar ones and show only distinct paths.

### What Is Driving The Decision

Surface the forces shaping the choice, such as:

- emotional pressure
- mental exhaustion
- urgency pressure
- identity pressure
- social or stakeholder pressure
- accountability pressure

Separate observed signals from inferred interpretation.

### Key Trade-Offs

Explain what each option gains, risks, or sacrifices. Scale depth to current bandwidth.

### Consequence Risk

Name the specific blind side introduced by the active emotion code.

One short statement per emotion code:

- **A (Cautious)**: May delay structural fixes in favour of reversible moves. Check whether the chosen option resolves the underlying exposure or just defers it.
- **B (Strategic)**: May underweight near-term operational or customer impact. Pressure-test the 90-day path before relying on the multi-year thesis.
- **C (Diplomatic)**: May preserve the status quo by over-weighting relationships. Verify that no stakeholder voice is being allowed to veto a structurally better answer.
- **D (Decisive)**: May commit with incomplete information. Confirm that blind-spot KPIs do not invalidate the speed advantage before locking in.
- **E (Analytical)**: May under-weight what it cannot quantify — stakeholder fatigue, reputation, team morale. Ask explicitly what would change if qualitative inputs were treated as equally important.
- **F (Pragmatic)**: May pick good enough when the right answer was available. Confirm that a structurally better outcome is not being left on the table to avoid harder commitment.

This section should always be short — one to two sentences.

### Blind Spots

List under-weighted KPIs that carry a red or yellow risk signal under the active emotion code.

Use the slot-type system: if a KPI is scored as `blind_spot_warning`, it must appear here regardless of its weight in the current emotion code.

Good content:

- which KPI is at risk
- why it is being under-weighted by the current emotion mode
- what the downside looks like if it materializes

Keep to 2–4 bullets maximum.

### Missing But Important

Include this section only when a missing fact materially changes the quality of the decision.

### Inferred Assumptions

Always label assumptions explicitly. Never mix them into the fact layer.

### Suggested Next Step

Do not force a final recommendation when the better move is:

- decide now
- gather one missing fact
- delay for a defined reason
- delegate
- narrow the option set

When scoring is close (close call), suggest one sanity check before committing. Tailor the next step to the active emotion code:

- **A**: Run one downside scenario before committing.
- **B**: Gather one more decision-critical fact about near-term execution.
- **C**: Pre-brief the two most affected stakeholders before the formal decision.
- **D**: Set a 72-hour checkpoint for the two leading indicators.
- **E**: Validate one assumption in the model, then widen the scenario range if sensitivity is high.
- **F**: Lock in the immediate move and schedule a 30-day review.

## KPI Matrix Rendering

When rendering a KPI matrix (webapp or structured output):

1. Order KPIs by slot type: `priority` first, then `blind_spot_warning`, then `primary`, then `secondary`
2. Within each slot, order by descending weight percentage
3. Show risk color for each KPI: red (0 on best option), yellow (1 on best option), green (2 on best option)
4. Surface blind_spot_warning KPIs prominently even when they are low-weight for the active emotion
5. Collapse `secondary` KPIs behind a "show more" control when space is limited

## Compression Rules

### When urgency is high

- lead with the decision immediately
- show the top facts first
- avoid background detail unless it changes the decision

### When emotional intensity is high

- reduce abstract explanation
- avoid interpretive overload
- keep phrasing steady and direct
- avoid piling on too many options

### When mental load is high

- reduce the number of ideas per section
- reduce option count to distinct paths
- shorten trade-off language
- prefer short bullets over descriptive paragraphs

## Expansion Rules

### When urgency is low

- include broader context
- include longer-range effects
- include more comparative framing

### When emotional intensity is low

- include nuance and ambiguity where useful
- include secondary considerations

### When mental load is low

- include more than the minimum viable facts
- preserve richer option analysis
- include second-order trade-offs

### When stakes are high and time is available

- preserve nuance
- compare long-term and short-term implications clearly
- do not over-compress for the sake of brevity

## Combined Cases

### High urgency + high emotion + high mental load

Target:

- minimal branching
- sharp prioritization
- fast scan

Preferred shape:

- short `Decision Snapshot`
- short `Persona Lens` if it changes the framing
- 2-4 `Relevant Facts`
- 2-3 distinct options
- 1-3 trade-offs
- 1 short `Consequence Risk`
- `Blind Spots` only if a critical KPI is at risk
- 1 short assumptions block if needed

### Low urgency + stable emotion + low mental load

Target:

- richer understanding
- better comparison
- more nuance

Preferred shape:

- fuller snapshot
- broader persona lens
- broader facts set
- expanded options
- richer trade-off section
- full `Consequence Risk` and `Blind Spots` panels
- explicit uncertainty where useful

### High stakes + low urgency

Do not over-compress. High stakes justify more detail.

### Emotionally intense + low stakes

Keep the output calm and compressed, but do not inflate risk.

## Emotion Switcher Behavior (Webapp)

When the user switches between emotion codes in the webapp:

- re-order KPIs by the new code's weight profile
- update the active recommendation
- update the `Persona Lens`, `Consequence Risk`, and `Suggested Next Step` to match the new code
- show a divergence signal when the new code recommends a different option than the baseline

The baseline (equal-weight) recommendation serves as a neutral anchor. Any emotion variant that diverges from it should be flagged.

## Tone Rules

Prefer:

- direct phrasing
- low-friction language
- matter-of-fact structure

Avoid:

- theatrical urgency
- vague reassurance
- generic life coaching language

## Separation Rules

Never blur:

- scenario facts
- public role context
- inferred assumptions

If the answer adds missing but obvious decision-relevant facts or options:

- keep them separate from explicit facts
- label them as inferred
- note uncertainty when confidence is not high

## Clarification Threshold

Ask a follow-up only when:

- the state estimate is too weak to adapt safely
- the decision itself is unclear
- one missing fact blocks meaningful framing
- the scenario is too thin to model the role even conservatively

Prefer one short question over a list.

When enrichment is not explicitly requested, prefer a targeted scenario question before browsing if that is likely to give better context than generic role research.
