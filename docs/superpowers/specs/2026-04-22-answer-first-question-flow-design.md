# Answer-First Question Flow Design

## Purpose

Shift the product from a matrix-first interaction model to a question-first decision workflow.

The user should be able to ask a question in natural business language, receive a direct answer grounded in:

- selected persona
- selected scenario
- selected matrix context
- Tata Steel UK project context
- live public web context only when needed

The matrix remains important, but as a supporting evidence surface rather than the primary thing the user must decode first.

---

## 1. Product flow

The new primary flow is:

```text
Question
→ Interpret question
→ Retrieve scenario + persona + matrix context
→ Generate direct answer
→ Highlight supporting matrix cell
→ Show evidence / implications
→ Offer follow-up questions
```

The user experience becomes:

1. ask a question
2. get an answer
3. see which matrix cell supports that answer
4. use follow-up questions to move toward a decision

The matrix is still the structured decision model, but not the first thing the user has to interpret.

---

## 2. Supported question styles

The system must support both:

- well-formed decision questions
- shorthand executive questions

Examples:

- `What is my commercials?`
- `What is my variance?`
- `Where is the exposure?`
- `What is the real issue?`
- `Should I disclose this now?`
- `What happens if we wait 30 days?`

Interpretation rule:

- if shorthand is understandable in the active scenario, answer directly
- if it is ambiguous between 2 plausible business meanings, ask 1 short clarification
- if it is too broad, do not fake an answer; offer 3 to 5 better scenario-specific questions

The system should not require polished grammar to work.

---

## 3. Answer generation pipeline

### Inputs

For each question, the answer engine should combine:

- selected persona
- selected scenario
- visible matrix rows and columns
- visible matrix cells
- scenario KPIs
- persona tension and role context
- stored Tata Steel UK project context
- live public web context only when required

### Pipeline

1. `Question interpretation`
   - intent
   - shorthand meaning
   - likely KPI family
   - likely perspective
   - likely emotional mode

2. `Context retrieval`
   - relevant scenario facts
   - relevant matrix cells
   - relevant KPI stack
   - relevant Tata UK project context

3. `Answer synthesis`
   - short direct answer
   - rationale
   - best-fit matrix cell
   - evidence list
   - confidence level

4. `Decision follow-up generation`
   - 3 to 5 follow-up questions that help the user refine the decision

### Output shape

Each resolved question should produce:

- `direct_answer`
- `why_this_answer`
- `supporting_kpis`
- `supporting_matrix_cell`
- `evidence_used`
- `confidence`
- `follow_up_questions`

---

## 4. Web-backed Tata UK context

Web lookup is optional support, not the main answer engine.

### Use web retrieval when the question requires:

- current government stance
- current public Tata Steel UK updates
- current funding, transition, or policy announcements
- recent Port Talbot public context
- external facts not contained in the scenario pack

### Do not use web retrieval when the answer is already grounded in:

- selected scenario
- persona
- matrix
- stored Tata UK project context

Examples that usually should not require web:

- `What is my variance?`
- `Should I tell BMW now or wait?`
- `Which KPI is dominant here?`

### When web is used

The answer should:

- state that current public context was included
- show source links
- stay anchored to the scenario rather than drifting into general news summary

---

## 5. Answer panel structure

The current insight panel should be reorganized into an `Answer Panel`.

### Top

1. `Direct Answer`
   - concise answer sentence or short paragraph

2. `Why`
   - short explanation of why this answer is correct in this scenario

3. `Confidence`
   - high / medium / low

### Middle

4. `Supporting Matrix Cell`
   - emotion mode
   - perspective
   - active KPI focus

5. `Evidence Used`
   - scenario facts
   - KPI signals
   - optional live web sources

### Decision section

6. `What This Implies`
   - recommended action
   - primary risk
   - likely consequence

### Follow-up section

7. `Next Questions`
   - 3 to 5 follow-up questions aimed at clarifying or stress-testing the decision

The panel should feel like:

- the system answered first
- then showed the reasoning surface

not:

- the user must decode the matrix to discover the answer

---

## 6. Clarification and shorthand rules

### If shorthand is understandable

Answer directly.

Examples:

- `What is my commercials?`
- `What is my variance?`
- `Where is the exposure?`
- `What is the real issue?`

### If ambiguous

Ask one short clarification.

Examples:

- `Do you mean commercial variance or schedule variance?`
- `Are you asking about disclosure exposure or financial exposure?`

### If too broad

Do not generate a vague answer.

Instead:

- explain that it is too broad
- offer 3 to 5 better scenario-specific questions

Shorthand business language should usually map to:

- an answer
or
- one clarification

not a vague fallback.

---

## 7. Backend / frontend boundary

### Backend should own

- question interpretation
- scenario-aware answer synthesis
- web retrieval when required
- confidence assessment
- suggested follow-up question generation

### Frontend should own

- question input UI
- answer panel rendering
- matrix highlight state
- clarification rendering
- suggestion chip rendering
- follow-up question chip interactions

### Matrix rule

The matrix remains the structured evidence model.

The answer panel is primary.

The matrix highlight is supporting proof.

---

## 8. First implementation scope

### In scope

- question becomes the primary interaction
- answer panel becomes the primary output
- matrix becomes supporting evidence
- support shorthand executive questions
- support direct answer, clarification, and suggested better questions
- use selected scenario + persona + matrix data as primary context
- optionally enrich with live public web retrieval for Tata UK context
- generate follow-up questions from the produced answer

### Out of scope

- full open-ended chatbot
- general web search on every query
- replacing the matrix logic
- replacing the persona/scenario framework
- long conversational memory across many turns

---

## 9. Success criteria

The flow is successful when:

- stakeholders can ask natural or shorthand business questions
- the system gives a direct answer before showing matrix detail
- the highlighted matrix cell supports the answer clearly
- follow-up questions help narrow toward a decision
- live web sources appear only when the question genuinely needs current external context

The target interaction is:

```text
Ask question
→ get answer
→ see why
→ inspect supporting matrix cell
→ use follow-ups to move toward the decision
```
