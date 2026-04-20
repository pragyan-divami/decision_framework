# State Model

## Purpose

Use this reference to translate a scenario into a structured human decision map for a specific persona.

The operating model is:

`context + trigger -> internal state -> salience -> valuation -> control mode -> threshold -> output`

This model should be interpreted through the persona profile, not as a purely generic human model.

## Source Layers

Keep these information layers separate:

- `scenario facts`: what the user directly says is true
- `public role context`: generic context about a role gathered from public sources
- `inferred interpretation`: what the system concludes from the first two layers

Priority order:

1. scenario facts
2. explicit persona details
3. public role context
4. internal inference

## Persona Profile Layer

Before mapping the decision, normalize the persona into a usable profile.

Useful fields:

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

This layer changes what the same situation means to the decision-maker.

## Emotion Taxonomy

All emotional interpretation must resolve into one of these six codes. Do not invent blended states.

| Code | Name       | Orientation                                | KPI Concentration                |
|------|------------|--------------------------------------------|----------------------------------|
| A    | Cautious   | Risk-first, downside-protective            | debt, cost, cash                 |
| B    | Strategic  | Long-horizon, thesis-protective            | regulatory, timeline, emissions  |
| C    | Diplomatic | Stakeholder-balancing, coalition-sensitive | customer, rating, emissions      |
| D    | Decisive   | Action-biased, commitment-oriented         | timeline, emissions, regulatory  |
| E    | Analytical | Model-driven, sensitivity-aware            | debt, cost, cash, timeline (balanced) |
| F    | Pragmatic  | Outcome-focused, operationally grounded    | debt, cash, emissions, cost (balanced) |

Each code produces a different KPI weight profile. The same scenario scored under Cautious (A) will rank options differently than under Decisive (D). The recommendation per code reflects how a person in that emotional state would most naturally weight the trade-offs.

## KPI Categories

The skill evaluates options across eight categories. Each is scored 0–2 per option.

| Category   | What it measures                                        |
|------------|---------------------------------------------------------|
| debt       | Leverage, balance-sheet risk, refinancing exposure      |
| cost       | Immediate cost increase or reduction                    |
| cash       | Short-term liquidity and cash flow impact               |
| regulatory | Compliance, legal, and regulatory risk                  |
| timeline   | Speed of execution and time-to-observable-outcome       |
| customer   | Customer trust, retention, and relationship risk        |
| rating     | Credit rating, reputation, and market perception        |
| emissions  | Environmental impact, ESG exposure                      |

When a scenario does not map cleanly to these categories, apply the closest available ones and note which are not applicable. The categories are domain defaults; persona and scenario context can shift which ones are most relevant.

## KPI Scoring

Score each option against each KPI on a 0–2 scale:

- `0` — option performs poorly on this KPI (increases risk, worsens the metric)
- `1` — option is neutral or mixed on this KPI
- `2` — option performs well on this KPI (reduces risk, improves the metric)

Apply persona-weighted interpretation when scoring. A score of 2 on `debt` means different things for a CFO managing covenant triggers versus a founder with flexible VC debt.

## KPI Slot Types

After scoring and weighting, KPIs are ordered into display slots. Slot order determines what the reader sees first.

| Slot                | Selection rule                                                         |
|---------------------|------------------------------------------------------------------------|
| priority            | Highest-weight KPIs for the active emotion code                        |
| blind_spot_warning  | Under-weighted KPIs that have a red or yellow risk score on any option |
| primary             | Remaining moderately weighted KPIs                                     |
| secondary           | Lower-weight KPIs included for completeness                            |

Always surface blind_spot_warning slots even when the current emotion code assigns them low weight. A Cautious reader under-weighting timeline could miss a deadline that collapses the decision space.

## Layers

### 1. Context Layer

Identify the outside-world conditions:

- situation
- available options
- time pressure
- social environment
- stakes and consequences

### 2. Trigger Layer

Identify what started the decision:

- opportunity
- threat
- need
- conflict
- prompt or cue

### 3. Internal State Layer

Estimate the current human state:

- emotion from the existing taxonomy (resolve to A–F)
- emotional intensity
- stress
- energy
- attention
- cognitive load

This layer is central to output adaptation.

### 4. Motivation Layer

Identify what the person is trying to gain or avoid:

- safety
- reward
- loss avoidance
- belonging
- status
- control
- meaning
- identity protection

### 5. Salience Layer

Identify what is likely standing out most:

- recent information
- emotional cues
- social proof
- urgent cues
- reward cues
- threat cues
- persona-specific accountability cues

Also identify what is likely being ignored:

- long-term consequences
- low-visibility details
- complex trade-offs
- delayed rewards

### 6. Valuation Layer

For each option, estimate how the mind is likely scoring it:

- safety
- reward
- ease
- speed
- social acceptability
- identity fit
- downside risk
- total cost

Common hidden weights:

- emotion weight
- loss aversion
- effort cost
- delay discounting
- uncertainty tolerance
- identity fit
- social approval value

### 7. Persona-Weighted Valuation

Also evaluate each option through the persona lens:

- what this role is responsible for
- what this role can actually control
- who absorbs the downside
- what success looks like for this persona
- what failure threatens for this persona
- which stakeholders matter most
- which trade-offs this persona is likely to care about first

Public role context can inform this layer, but it must not replace explicit scenario truth.

### 8. Control Mode Layer

Estimate whether the person is operating in:

- fast mode
  - habit
  - impulse
  - intuition
  - social imitation
- slow mode
  - deliberation
  - comparison
  - forecasting
  - rule-based reasoning
  - trade-off analysis

### 9. Threshold Layer

Look for what will cause action or non-action.

Action becomes more likely when the person has:

- enough certainty
- enough emotional relief
- enough reward expectation
- enough urgency
- enough social validation
- low enough friction

If threshold is not crossed, likely outputs are:

- decide now
- delay
- avoid
- delegate
- overthink
- ask for one more fact

## Operational Definitions

### Urgency

Estimate from deadlines, immediate consequences, shrinking windows, or explicit time pressure.

### Emotion

Estimate from scenario language, conflict, fear, frustration, shame, panic, relief-seeking, or calmness, then map the signal into the existing emotion taxonomy only (A–F).

### Mental Load

Estimate from exhaustion, competing demands, complexity, overload, decision fatigue, or fragmented attention.

### Stakes

Estimate from the downside and upside consequences of choosing poorly or delaying.

### Salience

Estimate what the person will notice first and what they are likely to neglect.

### Control Mode

Estimate whether the person has bandwidth for deliberation or is more likely to choose through impulse, habit, or fast relief.

### Accountability Exposure

Estimate who will judge the outcome, who bears the downside, and what reputation or trust is on the line for this persona.

## Close Call Detection

When the top two options score within a small weighted margin, flag this as a close call.

In a close call:

- do not force a clean recommendation
- note what would tip the decision toward each option
- suggest one targeted fact-gather or sanity check
- in Decisive (D) mode, always recommend a sanity check from an analytical peer before committing

## Labeling Standard

For every important extracted item, keep the distinction between:

- `explicit`: directly stated in the scenario
- `inferred`: strongly implied by the scenario or persona context
- `uncertain`: plausible but weakly supported

If public role context is used, identify it separately rather than folding it into the fact layer.
