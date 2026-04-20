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
