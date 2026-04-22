# Cross-Context Question Intelligence Design

Date: 2026-04-22
Status: Revised design draft for user review

## 0. Context

The current Tata UK decision matrix app is already structured around:

- a wizard-first context builder
- persona and scenario catalogs
- persona-dependent perspectives
- emotional framework selection
- a clickable decision matrix
- a cell-driven insight panel

The current question box is still too narrow. It mostly behaves like a local route helper inside the
currently selected context. The next product step is to turn that box into a cross-context question
layer that can search across the full decision inventory, switch context when needed, and ask a short
clarifying follow-up when the question is ambiguous.

This is not a freeform chatbot redesign. The matrix remains the primary product object. The question
layer becomes the intelligence layer that routes the user into the right matrix cell.

## 1. Purpose

Add a `Question Intelligence Layer` that can:

- search across all personas and scenarios
- infer the intended decision context from the user’s question
- decide whether the question belongs to the current context or a different one
- ask one short clarifying follow-up when confidence is low
- switch the UI context when confidence is high and a different context is the best match
- highlight the best-fit matrix cell
- populate the insight panel from that selected cell

The output must stay matrix-anchored and explainable.

## 2. Product Positioning

The question input should not become a general-purpose chat assistant.

It should remain a structured decision router with these outcomes:

1. `direct route`
   - current persona, scenario, and framework are already the best match

2. `context switch + route`
   - a different persona or scenario is the clear best match

3. `clarify first`
   - the question is too ambiguous to route safely

This keeps the system deterministic and grounded in the existing decision framework.

## 3. Search Scope

The router should search across the full decision inventory, not just the visible matrix.

Search scope includes:

- all personas
- all persona-bound scenarios
- all shared scenarios such as `VO112`
- all supported emotional frameworks
- all framework sub-modes
- all matrix cells produced for those contexts

The searchable object is:

`question -> persona -> scenario -> framework -> emotional sub-mode -> perspective -> matrix cell`

This means the question layer can route into a different matrix than the one the user is currently
viewing.

## 4. Matching Model

Question routing should use a layered resolver rather than a single keyword score.

### 4.1 Matching layers

The router should resolve in this order:

1. `scenario detection`
   - scenario names
   - counterparties
   - milestones
   - contracts
   - programme terms
   - stakeholder names
   - scenario-specific KPI language

2. `persona detection`
   - persona names
   - role titles
   - authority and decision-right cues
   - stakeholder responsibility cues

3. `question intent`
   - action
   - comparison
   - disclosure
   - timing
   - threshold
   - risk
   - consequence
   - data needed
   - escalation
   - stakeholder communication

4. `framework or emotional mode affinity`
   - downside containment
   - reversibility
   - safety threshold
   - regret minimization
   - long-horizon positioning
   - optionality preservation
   - institutional signaling
   - second-order effects
   - or equivalent sub-modes for the active framework family

5. `perspective affinity`
   - KPI language
   - trade-off language
   - stakeholder language
   - business-object language
   - constraints and consequence language

6. `cell ranking`
   - rank candidate cells using combined evidence

### 4.2 Weighted evidence

The final route decision should combine:

- scenario fit
- persona fit
- question-intent fit
- framework or sub-mode fit
- perspective fit
- KPI fit

No single layer should decide the route on its own unless the evidence is explicit and dominant.

## 5. Clarification Behavior

When confidence is too low, the system should ask one short clarification inside the UI before
highlighting anything.

### 5.1 Clarification triggers

Clarification should happen when:

- two or more scenarios are similarly strong matches
- persona is ambiguous
- the question is too short or underspecified
- the question uses weak pronouns like `this`, `it`, `they`, or `now` without enough context
- multiple perspectives score similarly
- the top candidate cell score is below the routing threshold

### 5.2 Clarification format

Clarification must be:

- short
- singular
- inline in the question area
- quickly answerable

The follow-up should ask only the highest-value distinction.

Examples:

- `Do you mean the BMW commercial scenario or the VO112 variation-order scenario?`
- `Are you asking from the CFO lens or the Commercial Director lens?`
- `Do you want the safest path or the most defensible disclosure path?`

### 5.3 Clarification rules

- ask one clarification at a time
- preserve the original user question
- do not highlight a cell before the ambiguity is resolved
- after the user answers, continue routing automatically

Clarification is a routing step, not a separate chat mode.

## 6. Context Switching Behavior

When the best answer lives in a different context, the UI should switch there automatically and tell
the user what changed.

### 6.1 What may change

The router may switch:

- persona
- scenario
- emotional framework
- active matrix cell

### 6.2 User-facing routing message

After a switch, the UI should show a concise banner such as:

- `Switched to P10 Commercial Director -> BMW offtake scenario -> Strategic framework`
- `Switched to P4 CFO -> capital programme scenario -> Cautious framework`

### 6.3 Switching rules

- if scenario is clear and current persona is wrong, switch persona
- if persona is clear and current scenario is wrong, switch scenario
- if both are clear, switch both
- if framework is strongly implied by the question, switch framework
- otherwise keep the recommended or default framework for the resolved context

### 6.4 Safety rule

Do not switch when confidence is low. Clarify first.

## 7. Response Model After Routing

Once a question is resolved, the app should do four things.

### 7.1 Highlight the best-fit cell

The highlighted cell is the primary answer location.

### 7.2 Populate the insight panel

The insight panel should continue to use the matrix cell as the source of truth for:

- recommended action
- primary risk
- likely consequence
- top KPIs
- data to inspect
- chart or evidence block
- blind spot
- next step

### 7.3 Explain why the cell was chosen

The route explanation should say:

- which persona, scenario, and framework were selected
- which perspective matched
- which emotional mode matched
- why the question maps to that cell

### 7.4 Optionally show related cells

If confidence is strong but nearby alternatives are still useful, the UI may softly indicate:

- one neighboring perspective
- one neighboring emotional mode
- one secondary candidate cell

But the system must still commit to one primary highlighted cell.

## 8. Backend and UI Boundary

The backend decision framework remains the reasoning core. The new routing layer should not replace it.

### 8.1 Backend remains responsible for

- persona catalog
- scenario catalog
- KPI families
- framework definitions
- framework sub-modes
- matrix cell construction inputs
- scenario-specific and persona-specific logic
- insight panel content ingredients

### 8.2 Routing layer becomes responsible for

- full-catalog search across personas and scenarios
- question parsing
- ambiguity detection
- clarification generation
- candidate ranking
- context-switch decision
- final cell selection
- route explanation metadata

### 8.3 UI remains responsible for

- question input
- clarification prompt rendering
- context-switch banner
- matrix highlight state
- insight panel update
- preserving the original question across clarification turns

### 8.4 Recommended near-term boundary

Because the app is currently static-first, the recommended near-term implementation is:

- backend exports the catalog and routing metadata
- frontend runs the question resolver using that structured metadata
- clarification and context switching stay UI-controlled

This avoids introducing a new chat backend while still delivering the new behavior.

## 9. Confidence Model

The router should return explicit route confidence states:

- `high`
- `medium`
- `low`

Expected behavior:

- `high`: route directly
- `medium`: route only if the leading candidate is clearly ahead and explain the assumption
- `low`: ask a clarifying follow-up before routing

Confidence should be based on:

- top candidate score
- gap to second candidate
- explicitness of persona or scenario cues
- ambiguity of the question intent
- ambiguity of perspective fit

## 10. UI Behavior

The matrix remains the main workspace.

The question experience should feel like:

1. user asks a question
2. system searches across all contexts
3. system either asks one clarification or switches context and routes
4. matrix highlights the correct cell
5. insight panel populates from that cell

The UI should not feel like a separate chat product or a modal wizard.

### 10.1 Inline clarification

Clarifications should appear directly in the question area, not in a modal.

### 10.2 Context-switch banner

The banner should appear directly above or near the matrix so the user understands what changed.

### 10.3 Question preservation

The original question should remain visible after routing so the user can refine it.

## 11. First Implementation Scope

The first implementation should focus on replacing the current question box with a cross-context
router while leaving the rest of the matrix app stable.

### 11.1 In scope

- search across all personas and scenarios
- detect whether the question belongs to the current context or another one
- switch context automatically when confidence is high
- ask one short clarifying follow-up when confidence is low
- highlight the best-fit matrix cell
- populate the insight panel from that cell
- show a concise route explanation
- preserve existing matrix logic
- preserve existing persona/scenario KPI logic
- keep `VO112` special handling while letting the new router search beyond it

### 11.2 Out of scope

- full conversational chat history
- long-form multi-turn AI chat
- LLM-generated freeform answers outside the matrix
- replacing the current decision engine
- changing the existing persona/scenario KPI models
- live external search
- streamed answer generation

## 12. Success Criteria

The new question layer is successful when:

- users can ask a question from the wrong context and still land in the right matrix
- ambiguous questions trigger one short clarification instead of a bad guess
- the highlighted matrix cell and insight panel feel relevant to the question
- the system explains its routing choice clearly
- the matrix remains the primary decision workspace

## 13. Implementation Constraint

This design must be implemented without degrading the currently working persona, scenario, KPI, and
cell logic. The question layer is an orchestration enhancement on top of the existing matrix product,
not a replacement for the current reasoning engine.
