# Examples

## Example 1: Founder Under Pressure

### Input

Persona: founder

Scenario:
The product demo is in three days. The engineering team is exhausted and two serious bugs are still open. Investors are attending the demo. The founder is stressed, has barely slept, and is trying to decide whether to launch on time or delay by a week.

### Compressed Output

```text
Decision Snapshot
You need to decide whether to launch on time or delay the demo by one week.

Persona Lens
As the founder, you are likely optimizing for both external confidence and downside control.

Relevant Facts
- The demo is in 3 days.
- The team is already exhausted.
- Two serious bugs are still open.
- Investors will see the result directly.

Possible Options
- Launch on time: protects timing, higher quality risk.
- Delay one week: hurts momentum, lowers demo risk.

What Is Driving The Decision
- Explicit: investor timing pressure.
- Inferred: reputation risk seems more important than speed right now.

Consequence Risk
Cautious mode may push toward delay even when launching with a scoped demo would be stronger. Confirm whether the bugs affect the investor-critical path before anchoring on postponement.

Missing But Important
- Whether the bugs affect core demo flows.

Suggested Next Step
Confirm whether the bugs affect the demo-critical path. If they do, the delay option becomes materially stronger.
```

## Example 2: Calm Buyer With Time

### Input

Persona: home buyer

Scenario:
I am comparing two apartments. I am not in a rush and can wait another month if needed. One apartment is cheaper but farther from work. The other is more expensive but in a better location and closer to my parents. I feel calm and want to make a thoughtful decision.

### Expanded Output

```text
Decision Snapshot
You are comparing two apartments and have enough time to make a thoughtful choice.

Persona Lens
As the buyer, you are balancing affordability, day-to-day quality of life, and family proximity.

Relevant Facts
- Time pressure is low, so you can compare carefully.
- Price and commute are meaningful financial and lifestyle factors.
- Proximity to your parents adds relational value, not just convenience value.

Possible Options
- Choose the cheaper apartment and accept the commute.
- Choose the better-located apartment and accept the higher cost.
- Wait and keep searching for a third option.

What Is Driving The Decision
- Explicit: cost, commute, family proximity.
- Inferred: long-term lifestyle fit may matter as much as price.

Key Trade-Offs
- The cheaper option lowers financial pressure but increases commute cost and time.
- The better-located option improves daily life and family access but raises fixed cost.
- Waiting preserves optionality but delays certainty.

Consequence Risk
Analytical mode may under-weight the relational value of proximity, which is harder to quantify. Ask explicitly: would I regret this choice in two years if the commute became a daily source of friction?

Inferred Assumptions
- You have enough stability to tolerate a longer decision cycle.

Suggested Next Step
Compare the two apartments on total monthly cost, weekly commute time, and family proximity before deciding whether a third search cycle is worth it.
```

## Example 3: Ambiguous State Requiring Follow-Up

### Input

Persona: manager

Scenario:
I need to decide whether to move one team member to a different project. Both projects are important and there are trade-offs.

### Expected Behavior

Ask a short follow-up because urgency, emotional state, and mental load are too underspecified.

```text
Before I frame this, what is most true right now: is this urgent, and are you making it under pressure or with time to think?
```

## Example 4: Role Enrichment Used

### Input

Persona: hospital administrator

Role enrichment requested: true

Scenario:
Emergency department wait times are rising and the administrator must decide whether to redirect budget from elective program improvements into temporary staffing for the next six weeks.

### Output Shape

```text
Decision Snapshot
You need to decide whether to reallocate budget into short-term staffing to relieve emergency department pressure.

Persona Lens
In this role, the decision is not only financial. It is also about operational continuity, patient risk, and institutional trust.

Public Role Context
- Hospital administrators are typically accountable for service continuity, resource allocation, and balancing patient care pressures with operational constraints.
- Decisions often carry stakeholder pressure from clinicians, finance leaders, and patients or families.

Relevant Facts
- Wait times are rising now.
- The proposed staffing shift is temporary and time-bounded.
- Redirecting budget may delay planned elective program improvements.

Possible Options
- Reallocate budget now for temporary staffing.
- Hold the current plan and absorb near-term wait-time pressure.
- Partially reallocate budget and limit the staffing intervention.

Key Trade-Offs
- Reallocating now may reduce patient and operational risk but weakens planned improvement work.
- Holding the current plan protects the elective roadmap but raises near-term strain and service risk.
- A partial move spreads the pain but may under-solve the urgent problem.

Consequence Risk
Diplomatic mode may preserve the elective roadmap because stakeholder voices already invested in that plan carry weight. Verify that no internal coalition is blocking the structurally better answer.

Blind Spots
- Timeline KPI: temporary staffing takes days to onboard. If wait-time pressure is already critical, the relief window matters.
- Customer KPI: patient and family trust erodes quickly under sustained wait-time pressure — this is under-weighted in a cost-focused frame.

Inferred Assumptions
- Inferred from scenario: immediate continuity risk appears more salient than elective improvement timing.

Suggested Next Step
Quantify whether the temporary staffing move is enough to reduce the wait-time problem materially. If not, a partial reallocation may just add disruption without solving the pressure.
```

## Example 5: Same Scenario, Different Persona

### Shared Scenario

A company is considering delaying a customer rollout by two weeks after a reliability issue was discovered.

### Persona A

Persona: customer success leader

### Persona B

Persona: CTO

### Expected Difference

The same scenario should be framed differently.

- For the customer success leader, the lens should emphasize trust, expectation management, and downstream customer fallout.
- For the CTO, the lens should emphasize system reliability, engineering risk, and failure containment.

The scenario facts remain the same. The weighting changes.

## Example 6: Same Scenario, Different Emotion Code

### Input

Persona: CFO

Scenario:
The company must decide whether to refinance its existing debt facility at a higher rate now, wait six months hoping rates improve, or convert part of the debt to equity to reduce leverage. A covenant review is due in eight weeks.

### Cautious (A) Output Shape

```text
Decision Snapshot
You need to decide between refinancing now at higher cost, waiting on rates, or converting debt to equity before the covenant review.

Persona Lens
Cautious mode reads this through the CFO lens. It concentrates attention on debt, cost, and cash — the three KPIs most exposed to a covenant breach.

Relevant Facts
- Covenant review is due in eight weeks.
- Refinancing now locks in higher cost but removes near-term breach risk.
- Waiting six months preserves optionality but carries rate and covenant uncertainty.
- Equity conversion reduces leverage but dilutes ownership.

Key Trade-Offs
- Refinance now: higher cost, lower breach risk.
- Wait: lower cost if rates drop, higher covenant risk.
- Convert to equity: removes leverage risk, introduces dilution.

Consequence Risk
Cautious mode may lock in the reversible option (refinancing) to avoid uncertainty even when the equity path produces better long-term balance-sheet health. Confirm whether the covenant risk is immediate or manageable before committing to the higher-cost refinance.

Suggested Next Step
Run one downside scenario: what happens to liquidity if refinancing is delayed 30 days and rates rise a further 50bp? Confirm the answer before committing.
```

### Decisive (D) Output Shape

```text
Decision Snapshot
Refinance now or delay — the covenant clock is ticking.

Persona Lens
Decisive mode reads this through the CFO lens. It weights timeline and regulatory KPIs over cost and debt structure nuance.

Key Trade-Offs
- Refinancing now clears the covenant risk and creates a known cost baseline.
- Waiting introduces rate and review uncertainty with limited upside.

Consequence Risk
Decisive mode can commit with incomplete information. Confirm that the equity conversion path does not produce a better outcome before locking in refinancing speed.

Suggested Next Step
Set a 72-hour checkpoint: confirm covenant headroom and rate desk availability. If both are in range, execute refinancing. If equity terms have improved, test that path head-to-head first.
```

### Key Difference

Same facts. Cautious (A) prioritises avoiding the downside of the wrong move. Decisive (D) prioritises removing the uncertainty quickly. The KPI weight shift produces a different emphasis even when the recommended option is the same.

## Example 7: Webapp Upload Format

### Purpose

Show the markdown format the webapp accepts as an uploaded file.

### Example File

```markdown
# Scenario: Infrastructure Investment Decision

## Persona

CFO of a mid-size manufacturing company. Responsible for capital allocation, balance-sheet management, and investor relations. Risk-oriented. Time horizon is typically 12–36 months.

## Scenario

The company is evaluating whether to fund a EUR 40M green infrastructure upgrade now using project finance, defer the investment by 18 months until cash flow improves, or pursue a hybrid split-funded approach combining 50% project finance and 50% balance-sheet debt.

## Time Horizon

3 years

## Stakeholders

Board, investors, operations team, sustainability committee

## KPI Families

Debt capacity, cost of capital, cash flow, regulatory compliance, emissions reduction, customer rating

## Decision Call

Fund now vs. defer vs. split

## Tension

Emissions reduction targets are tied to regulatory compliance deadlines. Deferring risks non-compliance penalties and rating exposure.

## Role enrichment

false
```

### What the Backend Does With This File

1. Parses all labeled sections into structured fields
2. Normalizes the persona into the internal profile shape
3. Extracts options from the `Decision Call` section
4. Maps `KPI Families` to the eight standard categories
5. Scores each option across all KPIs under all six emotion codes
6. Returns a JSON payload with baseline + six emotion variants
7. The frontend renders an emotion switcher, KPI matrix, and blind spot panel

### Clarification Behavior

If `Persona` or `Scenario` sections are missing from the uploaded file, the webapp renders a targeted prompt instead of an empty result.

```text
The uploaded file is missing a persona. Who is making this decision?
```
