# Question Recovery And Follow-Ups Design

Date: 2026-04-22
Status: Revised design draft for user review

## 0. Context

The Tata UK decision matrix app already supports:

- a wizard-first context builder
- persona and scenario selection
- emotional framework selection
- a clickable decision matrix
- a question router that can highlight a matrix cell
- a clarification step when the router is too uncertain

The remaining gap is the failure mode of the question box.

When users type a weak, random, or poorly formed question, the current behavior is still too brittle.
Instead of helping the user ask a better question, the UI risks producing a vague route explanation or a
low-value miss.

This design adds a guided assistance layer to the question box so it behaves more like a useful decision
guide without becoming a freeform chat product.

## 1. Purpose

Improve the question experience by adding two new behaviors:

1. `recovery suggestions`
   - when the entered question is weak, malformed, or unrelated to the current scenario

2. `follow-up questions`
   - after a successful answer is routed and shown in the matrix

The goal is to help the user move toward a better decision question rather than leaving them with a vague
failure or dead-end route.

## 2. Product Positioning

This is not a chatbot redesign.

The matrix remains the primary answer surface.

The question area becomes a guided interaction strip with four possible outcomes:

1. `direct answer`
2. `clarification`
3. `recovery suggestions`
4. `follow-up suggestions`

The product stays matrix-first and decision-structured.

## 3. Assistance Model

The question box should support three assistance states in addition to normal routing.

### 3.1 Direct answer state

If the question routes well:

- highlight the best-fit matrix cell
- populate the insight panel
- show follow-up questions beneath the route explanation

### 3.2 Clarification state

If the question is relevant but ambiguous:

- ask one short clarification
- preserve the original question
- do not highlight a cell yet

### 3.3 Recovery suggestion state

If the question is weak, random, malformed, or unrelated to the current scenario:

- do not produce a vague answer
- do not pretend the route is meaningful
- instead show 3 to 5 better questions based on:
  - the current scenario
  - the current persona
  - the active framework
  - active perspectives
  - the words the user typed

The user can tap one of these suggestions to continue immediately.

## 4. Recovery Suggestion Generation

Recovery suggestions should be generated only from the current scenario.

This is an explicit product rule. Recovery must not switch the user into another scenario or persona.

### 4.1 Inputs

Recovery suggestions should use:

- current scenario
- current persona
- active framework
- active scenario perspectives
- likely active matrix cells
- the words the user typed

### 4.2 Generation rule

The app should avoid generic fallback prompts such as:

- `What should we do?`
- `What is the risk?`

Instead it should produce concrete scenario-shaped prompts such as:

- `Should the CFO escalate DBET now or wait for stronger evidence?`
- `Which KPI becomes dominant if Tenova suspends work for 14 days?`
- `What is the safest disclosure sequence for the Board Chair under VO112?`

### 4.3 Use of entered words

The entered text acts as a hint, not a direct command.

Examples:

- input: `risk BMW delay`
  - suggested questions:
    - `How does a commissioning delay change BMW disclosure timing?`
    - `Which cell best handles customer qualification risk if the delay extends?`

- input: `what now`
  - rely more heavily on scenario and persona context to produce useful next questions

### 4.4 Output rule

Recovery suggestions must:

- stay inside the current scenario
- be concrete
- be answerable by the matrix
- imply one likely perspective and emotional mode
- help the user ask a better next question

## 5. Follow-Up Question Generation

After the app successfully routes a question and shows an answer, it should offer follow-up questions
that help the user decide better.

### 5.1 Purpose

Follow-up questions should help the user explore:

- adjacent risks
- missing data
- neighboring perspectives
- alternative emotional modes
- decision thresholds
- consequences of acting or waiting

### 5.2 Inputs

Follow-ups should be generated from:

- the active scenario
- the active persona
- the selected emotional mode
- the selected perspective
- the highlighted matrix cell
- the primary KPI
- the primary risk
- the likely consequence
- the blind spot

### 5.3 Follow-up types

The app should usually offer a mix of:

1. `adjacent perspective`
   - `How does this look from the grant-defensibility perspective instead?`

2. `adjacent emotional mode`
   - `What changes if this is viewed through Reversibility instead of Downside Containment?`

3. `risk probe`
   - `What becomes the dominant risk if Tata waits 14 more days?`

4. `data probe`
   - `Which additional data would confirm this recommendation?`

5. `threshold probe`
   - `At what point does this become a board-level issue?`

### 5.4 Output rule

Follow-up questions must:

- stay in the same scenario
- be concise
- be one tap away
- help the user move toward a stronger decision

## 6. Trigger Logic

The app needs a clear rule for when to:

- answer directly
- clarify
- recover with better questions
- show follow-up questions

### 6.1 Direct answer

Use when:

- confidence is high enough
- one route clearly wins
- the question is answerable inside the current scenario

Result:

- highlight the cell
- populate the insight panel
- show follow-up questions

### 6.2 Clarification

Use when:

- the question is relevant
- but multiple routes are plausible
- or the user’s intent is incomplete

Result:

- ask one short clarification
- do not highlight yet

### 6.3 Recovery suggestions

Use when:

- the question is weak, random, unrelated, or malformed
- the router cannot safely map it
- the wording is too generic to produce a meaningful answer

Result:

- do not pretend to answer
- show 3 to 5 better questions inside the current scenario

### 6.4 Follow-up suggestions

Use only after:

- a successful route and answer

Result:

- show 3 to 5 next questions based on the highlighted cell

### 6.5 Clarification vs recovery

This distinction must remain explicit:

- `clarification`
  - the system probably understands the question space, but needs one missing distinction

- `recovery`
  - the system does not have enough meaningful signal to route safely, so it offers better questions

This protects trust and keeps the UI understandable.

## 7. UI Behavior

The question area should remain compact and matrix-adjacent. It should not turn into a full chat window.

### 7.1 Question states

1. `idle`
   - input field
   - route button
   - optional starter prompts

2. `clarification`
   - one short clarification prompt below the input
   - no highlight yet

3. `recovery suggestions`
   - short note that the question could not be routed confidently
   - 3 to 5 suggestion chips

4. `answered`
   - matrix highlighted
   - insight panel updated
   - follow-up suggestion chips shown below the route explanation

### 7.2 Suggestion chip behavior

- tapping a recovery suggestion should fill and route it immediately
- tapping a follow-up question should do the same
- chips must wrap cleanly
- chips should remain concise
- chips should not dominate vertical space

### 7.3 Message tone

The UI should use different tones for:

- `clarification`
  - `Do you mean the BMW customer question or the grant-covenant question?`

- `recovery`
  - `That question is too broad for this scenario. Try one of these instead.`

- `follow-up`
  - `You may also want to ask:`

This makes the system state legible.

## 8. Scope

The first implementation should improve the question box without changing the rest of the matrix app.

### 8.1 In scope

- add `recovery suggestion` mode for weak or unrelated questions
- add `follow-up question` mode after a successful answer
- keep `clarification` mode for ambiguous questions
- generate all suggestions only from the current scenario
- keep the matrix as the primary answer surface
- let users tap suggestion chips to route immediately
- support this especially well for `VO112`, while keeping the pattern reusable

### 8.2 Out of scope

- full chat history
- cross-scenario recovery suggestions
- LLM-generated freeform chat answers
- changes to scenario or KPI logic
- backend redesign
- replacement of the existing router with a separate AI agent

## 9. Success Criteria

The feature is successful when:

- unrelated or weak questions no longer produce vague pseudo-answers
- users are guided toward better questions inside the current scenario
- follow-up questions help users inspect adjacent decision paths
- the matrix remains the primary answer location
- the UI remains compact and low-cognitive-load

## 10. Implementation Constraint

This enhancement must sit on top of the current frontend routing layer.

The expected implementation shape is:

- new routing outcome: `recovery`
- new post-answer output: `followUps`

The backend decision framework, scenario logic, KPI logic, and existing matrix rendering should remain
unchanged.
