# Adaptive Decision Framing Skill Design

Date: 2026-04-17
Status: Revised design draft for user review

## 0. Current Product Direction

This design now evolves beyond a simple adaptive recommendation app.

The product should be restructured into a **wizard-first dynamic decision matrix app** where:

- the backend decision framework remains the reasoning core
- the UI becomes the primary interaction layer
- users explore decisions through domain, platform, persona, perspectives, and emotional framework
- the system renders a clickable matrix and a question-aware decision insight panel

The target product shape is:

`Context Builder -> Emotion + Perspective Matrix -> Question-Aware Highlighting -> Decision Insight`

The first implementation should be grounded in the **Tata Steel UK Port Talbot EAF Transformation**
project context.

## 1. Purpose

Create a reusable decision-framing skill that can support any persona, in any role or life position, across any scenario, while adapting the framing of the decision to the user's emotional state using the existing emotion taxonomy already defined in the system.

The skill should:

- accept a persona as either a simple role label or a richer persona profile
- ask for the scenario only when it is missing or too incomplete to analyze
- map the scenario through a human decision-making model
- resolve emotional interpretation into the existing emotion taxonomy only
- adapt the structure, density, and tone of the output to the decision-maker's likely state
- help the decision-maker move toward action, delay, delegation, or clarification with less friction

The skill is not a generic advice bot. Its job is to make the decision legible for the specific persona in the specific situation.

For the current project, that legibility should be delivered through a decision matrix UI rather
than only through a single recommendation view.

## 2. Problem Statement

Most decision-support systems fail in one or more of these ways:

- they treat all users as if they process information the same way
- they assume a narrow set of personas such as founders, managers, or consumers
- they overfit to job title and underfit to actual scenario context
- they ignore the emotional state of the decision-maker
- they require too much upfront input before they can be useful

This design addresses those failures by making persona handling universal, scenario handling adaptive, and emotional adaptation constrained by the existing taxonomy rather than open-ended interpretation.

## 3. Design Goals

- Work across any persona, not only predefined archetypes
- Support both simple persona input and richer structured persona profiles
- Treat the scenario as the main source of truth once provided
- Ask for scenario details only when required for meaningful analysis
- Use the existing emotion taxonomy as the only emotion resolution layer
- Let persona influence how the same scenario is weighted and framed
- Keep explicit facts, inferred signals, and uncertain assumptions separate
- Stay interpretable, tunable, and auditable
- Preserve the current backend reasoning engine while restructuring the front-end into a matrix app
- Support clickable matrix cells and question-aware routing into a decision insight panel
- Ground the first product version in the Tata Steel UK Port Talbot transformation programme

## 4. Non-Goals

- Do not invent new emotion categories outside the existing taxonomy
- Do not require a fully structured persona object in every interaction
- Do not depend on a library of hardcoded persona templates to function
- Do not always force a recommendation when the better outcome is delay, delegation, or targeted clarification
- Do not pretend certainty when the scenario is thin or ambiguous

## 5. Primary Design Decision

Use a persona-as-profile pipeline with graceful fallback.

The framework should accept:

- a simple persona label such as `"CEO"`, `"student"`, `"single parent"`, `"doctor"`, `"team lead"`
- or a richer persona profile object when available

Regardless of input depth, the system should normalize persona into a common internal profile shape before analyzing the scenario.

## 6. Input Model

### 6.1 Required For Useful Analysis

At minimum, the system needs:

- `domain`
- `platform` unless already inferable
- `persona` or `persona_profile`
- `scenario` or project decision question

However, the interaction model should allow the user to provide these incrementally.

### 6.2 Interaction Rule

If persona is provided but scenario is missing, ask for the scenario.

If scenario is provided but too incomplete to support decision mapping, ask one short targeted follow-up question.

If persona and scenario are both sufficient, proceed without asking unnecessary questions.

For the matrix product, the full resolution order should be:

1. `domain`
2. `platform`
3. `persona`
4. `persona-dependent perspectives`
5. `two recommended emotional frameworks`
6. `selected emotional framework`

However, if any of these are already present from uploaded content or previous state, the system
should auto-fill and skip the prompt.

### 6.3 Accepted Inputs

- `domain`
- `platform`
- `project`
- `persona`: free-form string
- `persona_profile`: structured object when available
- `scenario`: free-form text
- `decision_goal`: optional
- `known_options`: optional
- `emotion_signal`: optional only if supplied explicitly by the user
- `role_enrichment_requested`: optional boolean for using public role research
- `perspectives`: selected persona-dependent perspectives
- `selected_emotional_framework`

### 6.4 Persona Profile Shape

The normalized internal persona profile should support these fields:

- `role_label`
- `life_or_work_domain`
- `responsibility_scope`
- `decision_authority`
- `primary_goals`
- `key_constraints`
- `risk_orientation`
- `default_time_horizon`
- `stakeholders_affected`
- `identity_pressures`

Not all fields need to be present in the input. The system may infer some of them, but must label those as inferred.

### 6.5 Optional Role Enrichment Layer

The framework may enrich a role-based persona with public internet context when:

- the user requests role enrichment
- or the scenario is too thin to understand the role well enough without additional context

This enrichment layer is optional and always subordinate to the scenario.

It may capture:

- common responsibilities of the role
- likely decision rights
- typical constraints
- common success metrics
- likely stakeholder groups
- common risks and accountability pressures

## 7. Core Conceptual Model

The skill should use the supplied human decision-making map as its backbone:

`context + trigger -> internal state -> salience -> valuation -> control mode -> threshold -> output`

This model stays internal. The final response should not explain theory unless the user asks for it.

For the matrix app, this conceptual model should feed a visible interaction model:

`resolved context -> selected emotional framework -> emotional sub-mode × perspective matrix -> active cell insight`

## 7.1 Matrix App Structure

The product should be organized into three layers:

1. `Context Builder`
   - domain
   - platform
   - persona
   - persona-dependent perspectives
   - two recommended emotional frameworks
   - one selected emotional framework

2. `Decision Matrix`
   - `X-axis = persona-dependent perspectives`
   - `Y-axis = sub-modes inside the selected emotional framework`

3. `Question-Aware Insight Panel`
   - user clicks a cell or asks a question
   - the system opens a cell-specific insight panel

The matrix should support both:

- `manual exploration`
- `question-aware routing`

## 8. Internal Decision Map

The framework should map each scenario into a normalized decision structure.

### 8.1 Extracted Fields

- decision context
- trigger
- active goal
- stakes
- constraints
- time pressure
- social environment
- explicit options
- implied options
- missing decision-critical facts
- likely blockers

### 8.2 Persona-Weighted Fields

These fields should reflect how the decision is experienced by this specific persona:

- authority level
- accountability exposure
- who absorbs downside
- what success looks like for this persona
- what failure threatens for this persona
- identity fit of each option
- stakeholder pressure

### 8.3 State Fields

These should be estimated from the scenario and any explicit user input:

- emotion from the existing taxonomy
- emotional intensity
- mental load
- urgency
- control mode
- likely decision threshold

### 8.4 Labeling Standard

Every important extracted item should be tagged as:

- `explicit`
- `inferred`
- `uncertain`

## 8.5 Matrix Cell Object

The matrix UI should assemble each cell as a structured object. Recommended shape:

- `emotion_framework`
- `emotion_mode`
- `perspective`
- `kpi_cluster`
- `data_requirements`
- `chart_type`
- `recommended_action_tendency`
- `risk_pattern`
- `consequence_pattern`
- `blind_spot_pattern`
- `supporting_backend_signals`

Each cell should be clickable. Clicking a cell should open the exact decision insight for that
intersection of emotional mode and persona perspective.

## 9. Emotion Handling

### 9.1 Taxonomy Constraint

All emotional interpretation must resolve into the existing emotion taxonomy already defined in the framework.

The skill may infer emotional signals from language or context, but it must map them into one or more existing taxonomy states rather than inventing new labels.

### 9.2 Emotion Rules

- if the user explicitly names an emotion from the taxonomy, use it directly
- if the scenario implies an emotion, map it to the closest valid taxonomy emotion
- if multiple emotions seem plausible, either choose the highest-confidence one or note uncertainty
- do not output invented blended emotions as system-level states

### 9.3 Example

If the scenario sounds like panic, shame, and defensiveness but the taxonomy only supports `fear` and `sadness`, the system must resolve to those existing states and label any nuance as interpretation, not as a new category.

## 9.4 Emotional Framework Recommendation

The app should not show a giant abstract list of emotional frameworks.

Instead, once domain, platform, persona, and perspectives are resolved, it should recommend exactly
two emotional frameworks and mark one as preferred.

Example logic:

- healthcare safety + ethics persona -> recommend `Cautious` and `Analytical`
- crisis operations + operations head -> recommend `Pragmatic` and `Decisive`
- board strategy + founder -> recommend `Strategic` and `Diplomatic`

The user then chooses one framework. The matrix is built only after that choice.

## 9.5 Framework Sub-Modes

The selected emotional framework should expand into operational sub-modes that populate the matrix
rows. These are not new taxonomy-level emotions. They are UI-operating dimensions within the chosen
framework.

Example:

- `Cautious` -> downside containment, reversibility, safety threshold, regret minimization
- `Strategic` -> long-horizon positioning, optionality preservation, institutional signaling, second-order effects

## 10. Persona Normalization

### 10.1 Why This Layer Exists

The same scenario should not be framed the same way for every persona.

For example, the same team layoff scenario may be evaluated differently by:

- a founder optimizing runway and reputation
- a people manager optimizing fairness and team trust
- an employee optimizing safety and income continuity

The scenario may be identical, but the weighting is not.

### 10.2 Normalization Rule

Normalize persona input into a profile that captures:

- what this person is responsible for
- what this person can control
- what consequences matter most to them
- whose approval or trust matters
- whether they are deciding for self, team, organization, family, or client

### 10.3 Fallback Rule

If the user provides only a simple persona label, use the scenario to infer the missing profile fields conservatively. Mark those inferred fields clearly.

### 10.4 Optional Public Role Enrichment

When the persona is role-based, the framework may use public internet sources to enrich the normalized persona profile.

This enrichment must be treated as contextual guidance, not identity truth.

The purpose is to improve understanding of:

- what the role is generally responsible for
- what authority the role often has
- what pressures and trade-offs commonly apply
- what kinds of consequences typically matter to that role

The framework should not assume that public role norms fully describe the user's exact case.

## 10.6 Persona-Dependent Perspectives

Perspectives should be persona-dependent, not universal.

Each persona should resolve to:

- 4 to 8 perspectives
- one recommended default perspective set
- ability for the UI to toggle or compare perspectives

Examples:

- Chief Medical & Ethics Officer
  - patient safety
  - clinical continuity
  - ethical disclosure
  - regulatory defensibility
  - institutional trust
  - access equity

- CFO
  - cash preservation
  - downside protection
  - investor confidence
  - regulatory exposure
  - operating resilience
  - capital efficiency

- Product Manager
  - user trust
  - adoption
  - retention
  - execution speed
  - technical feasibility
  - business viability

### 10.5 Source Priority Rule

When public role context is used, priority must be:

1. scenario facts supplied by the user
2. explicit persona details supplied by the user
3. public role context from internet research
4. internal inference

Public role context may sharpen interpretation, but it must never override direct scenario facts.

## 11. Processing Pipeline

Use a six-stage pipeline.

For the matrix app, the visible user flow should be:

1. `domain / industry`
2. `platform / context`
3. `persona`
4. `persona perspectives`
5. `recommended emotional frameworks`
6. `selected emotional framework`
7. `matrix construction`
8. `cell click or question routing`
9. `decision insight panel`

The backend reasoning engine should remain substantially intact. The major restructuring is in the
UI layer and in the structured outputs needed for matrix construction.

## 11.1 Tata Steel UK Grounding

The first implementation should be grounded in the Tata Steel UK Port Talbot EAF Transformation.

Default project context:

- `domain`: industrial transformation / steel / heavy manufacturing
- `project`: Tata Steel UK Port Talbot EAF Transformation
- `platform`: Port Talbot transformation programme

The first version should be optimized around Tata UK decision surfaces such as:

- construction and commissioning
- scrap supply and quality
- energy and grid readiness
- customer and grade capability
- workforce transition
- grant and milestone compliance
- community and political legitimacy
- decarbonization and strategic positioning

The architecture should remain reusable, but the initial product should be a Tata UK-aware matrix,
not a blank generic matrix.

### 11.1 Stage 1: Input Sufficiency Check

Determine whether the framework can proceed.

Cases:

- persona present, scenario present, both sufficient: proceed
- persona present, scenario missing: ask for scenario
- persona present, scenario too vague: ask one targeted question
- scenario present, persona missing: ask who the decision-maker is

### 11.2 Stage 2: Persona Normalization

Convert persona or persona_profile into a normalized persona model.

### 11.3 Stage 3: Optional Role Enrichment

If the persona is role-based and enrichment is requested or necessary, gather public role context from internet sources.

The enrichment stage should extract:

- standard responsibilities
- likely reporting scope or authority
- common operational or organizational constraints
- common stakeholder exposure
- common performance expectations

All enriched items must be labeled as public role context, not scenario fact.

### 11.4 Stage 4: Decision Map Extraction

Extract context, state, options, constraints, and missing facts using the state model.

### 11.5 Stage 5: Taxonomy Resolution

Resolve emotional interpretation into the existing emotion taxonomy and estimate urgency, mental load, and control mode.

### 11.6 Stage 6: Adaptive Framing

Render the decision in a way that matches:

- persona profile
- public role context when used
- scenario stakes
- urgency
- mental load
- emotion taxonomy state
- confidence level

## 12. Adaptive Presentation Logic

The system should always preserve the same response spine but flex how much of it is shown and how dense it is.

### 12.1 Core Sections

- `Decision Snapshot`
- `Persona Lens`
- `Public Role Context`
- `Relevant Facts`
- `Possible Options`
- `What Is Driving The Decision`
- `Key Trade-Offs`
- `Missing But Important`
- `Inferred Assumptions`
- `Suggested Next Step`

### 12.2 New Section: Persona Lens

This section is what makes the framework universal.

It should briefly explain why the decision looks the way it does for this persona.

Examples:

- what this persona is likely optimizing for
- what risks matter most from their position
- what accountability or identity pressure is shaping the decision

### 12.3 Optional Section: Public Role Context

Show this section only when role enrichment was actually used and the context materially changes the framing.

This section should summarize:

- what the role usually owns
- what the role is usually accountable for
- what pressures commonly shape decisions in that role

This section must be clearly separated from scenario facts.

### 12.4 Suggested Next Step

The framework should not always force a final choice.

The next step may be:

- choose an option now
- gather one missing fact
- delay for a defined reason
- delegate to the right person
- narrow the option set

## 13. Dynamic Rendering Rules

### 13.1 High Urgency + High Emotion + High Mental Load

- compress heavily
- show only distinct options
- surface immediate consequences
- keep the persona lens very short
- bias toward action-enabling clarity

### 13.2 Low Urgency + Low Emotion + Low Mental Load

- expand trade-offs
- include second-order effects
- preserve ambiguity where useful
- show broader stakeholder implications

### 13.3 High Stakes + Low Urgency

- keep nuance
- do not over-compress
- compare long-term and short-term consequences clearly

### 13.4 Low Stakes + High Emotion

- reduce friction
- avoid amplifying the drama of the decision
- stabilize the framing

## 14. Clarification Rules

Ask a follow-up only when one of these is true:

- the scenario is missing
- the core decision is unclear
- the scenario is too incomplete to identify the decision map
- persona is missing and cannot be reasonably inferred as the decision-maker
- one missing fact blocks useful framing
- emotion, urgency, or mental load are too ambiguous to adapt safely

Clarification rules:

- ask one short question at a time
- ask only for the most decision-critical missing input
- do not ask for structured persona fields unless they materially improve the framing

When enrichment is not explicitly requested, prefer asking one scenario question before browsing if that question is likely to produce better context than generic role research.

## 15. Confidence Handling

### 15.1 High Confidence

- proceed directly
- adapt output fully

### 15.2 Medium Confidence

- proceed directly
- note the most important uncertain assumptions

### 15.3 Low Confidence

- avoid aggressive compression or interpretation
- ask one short clarifying question if needed

## 16. Output Principles

- scenario is the main source of truth
- persona shapes weighting, not reality itself
- public role enrichment is context, not truth
- emotion must resolve to the existing taxonomy
- explicit facts must stay separate from inferred interpretation
- public role context must stay separate from scenario facts
- the system should help the user move, not stall in analysis
- the framework should support action, delay, avoidance recognition, or delegation when appropriate

## 17. Recommended Skill Structure Updates

Keep the current package but update the references to reflect universal persona handling.

```text
adaptive-decision-framing/
├── SKILL.md
└── references/
    ├── state-model.md
    ├── rendering-model.md
    └── examples.md
```

### 17.1 SKILL.md Should Be Updated To Reflect

- persona normalization
- optional role enrichment workflow
- scenario sufficiency check
- fixed emotion taxonomy resolution
- persona lens output section
- public role context section
- adaptive next-step framing

### 17.2 state-model.md Should Be Extended To Cover

- persona-weighted valuation
- accountability and authority
- stakeholder exposure
- how persona changes what is salient
- how public role context can inform, but not replace, persona understanding

### 17.3 rendering-model.md Should Be Extended To Cover

- the `Persona Lens` section
- the optional `Public Role Context` section
- how role and authority change trade-off framing
- when the next best move is not immediate commitment

### 17.4 examples.md Should Include

- the same scenario rendered for multiple personas
- the same persona under different emotions from the taxonomy
- role-enriched and non-enriched versions of the same persona
- incomplete-input cases where the skill asks for scenario or one missing fact

## 18. Example Normalized Shape

```text
persona_profile:
  role_label: "operations manager"
  life_or_work_domain: "work"
  responsibility_scope: "team delivery and client continuity"
  decision_authority: "recommendation with limited approval authority"
  primary_goals: ["protect service continuity", "avoid team burnout"]
  key_constraints: ["budget freeze", "deadline this week"]
  stakeholders_affected: ["team", "client", "director"]
  identity_pressures: ["seen as reliable", "avoid avoidable failure"]

scenario: "A key team member is out unexpectedly and the manager must decide whether to delay delivery, redistribute work, or cut scope."

emotion_state: fear
mental_load: high
urgency: high
control_mode: fast-leaning
known_options: ["delay delivery", "redistribute work", "cut scope"]
missing_data: ["which work items are truly non-negotiable for the client"]
inferred_assumptions: ["the manager is optimizing for continuity over elegance"]
```

## 19. Acceptance Criteria

The design is successful if the final skill:

- works with any persona label or richer persona profile
- asks for scenario only when missing or too incomplete to analyze
- uses scenario as the primary source of truth
- can optionally enrich a role-based persona with public internet context
- resolves emotional interpretation into the existing taxonomy only
- adapts output to persona, urgency, mental load, and stakes
- makes persona-specific weighting visible through a `Persona Lens`
- keeps public role context separate from scenario facts and inferred assumptions
- separates explicit facts, inferred assumptions, and uncertainty
- supports recommendations, delay, delegation, or clarification as valid outcomes
- remains interpretable and easy to tune

## 20. Risks And Safeguards

### Risks

- over-inferring persona details from a thin role label
- over-trusting generic internet descriptions of a role
- mapping emotional nuance too aggressively into the wrong taxonomy state
- letting persona overwhelm scenario truth
- over-compressing high-stakes cases

### Safeguards

- conservative persona inference
- source-priority rules that keep scenario facts above role enrichment
- explicit labeling of inferred profile fields
- explicit labeling of public role context
- scenario-first fact extraction
- confidence-based clarification
- no emotion labels outside the approved taxonomy
- fixed response spine with adaptive expansion and compression

## 21. Webapp Extension

Extend the design from a documentation-first skill into a local webapp that can ingest one uploaded markdown file, perform backend analysis, optionally enrich role context, and render the result inside the same web interface.

This extension replaces the current static-scenario-only workflow with a reusable decision console.

## 22. Product Flow

The app should work like this:

1. User opens the local decision app.
2. User uploads one markdown file containing both persona and scenario.
3. Backend parses the file into:
   - persona
   - scenario
   - optional metadata such as stakeholders, KPI lists, time horizon, decision type, and explicit enrichment request
4. Backend checks whether the input is sufficient.
5. Backend optionally performs role enrichment only when:
   - the file explicitly requests enrichment
   - or the parsed role is too underspecified to analyze well
6. Backend runs the decision framework.
7. App renders the result in the same webapp.

The output should stay inside one app session rather than generating one-off static HTML pages for every scenario.

## 23. Backend Service Shape

Use a small local HTTP service.

The backend should have three responsibilities:

### 23.1 Parse Upload

Accept one uploaded markdown file and extract:

- title
- persona label or persona profile
- scenario
- optional metadata like decision type, stakeholders, KPI lists, time horizon, decision call, and explicit enrichment request

### 23.2 Analyze Scenario

Build a normalized decision object containing:

- persona profile
- scenario facts
- optional public role context
- baseline recommendation
- all 6 emotion variants
- KPI prioritization
- KPI risk flags
- blind spots
- confidence notes
- divergence from baseline

### 23.3 Serve Result

Return a stable JSON payload for the frontend to render.

Recommended routes:

- `GET /` -> upload page
- `POST /analyze` -> upload markdown, parse, analyze, return JSON
- `GET /health` -> simple service health check

No database, auth, or persistence is required in the first version.

## 24. Upload File Rules

The app should accept one markdown file that contains both persona and scenario.

The uploaded file should be treated as the primary source of truth.

Useful sections may include:

- persona
- scenario
- time horizon
- stakeholders
- KPI families
- decision call
- tension
- explicit enrichment request

The app should not require all of these sections to exist if the scenario is still analyzable.

## 25. Parsing Rules

The markdown parser should:

- prefer heading-based and labeled-section extraction first
- fall back to heuristic extraction when the document is loosely structured
- preserve useful metadata when present rather than discarding it
- produce a normalized parse result even when some fields are missing

The parser should look first for explicit sections such as:

- `Persona`
- `Scenario`
- `Decision context`
- `Key stakeholders`
- `KPI families`
- `How to use this scenario`

When these sections are absent, the parser should infer structure conservatively from headings, emphasis markers, and paragraph patterns.

## 26. Enrichment Rules For Uploaded Files

Do not browse automatically on every upload.

Browse only when:

- the uploaded file explicitly requests role enrichment
- or the parsed role is too thin to analyze well without public context

Role enrichment applies only to role-based personas, not named real-person profiling.

When enrichment is used, keep these layers separate:

- uploaded scenario facts
- uploaded persona details
- public role context
- inferred assumptions

Source priority must remain:

1. uploaded scenario facts
2. uploaded persona details
3. public role context
4. internal inference

This prevents generic internet role descriptions from overriding the uploaded scenario.

## 27. Analysis Engine For The Webapp

The backend analysis engine should stay deterministic and inspectable.

Core stages:

1. parse uploaded markdown into structured fields
2. check sufficiency
3. normalize persona
4. optionally enrich role context
5. build normalized decision object
6. compute:
   - baseline recommendation
   - all 6 emotion variants
   - KPI prioritization
   - risk flags
   - blind spots
   - divergence from baseline
7. return one stable JSON payload for rendering

The frontend must not contain scenario-specific analysis logic.

## 28. Frontend Shape

The webapp should become one reusable decision console rather than a set of fixed scenario pages.

### 28.1 Upload Flow

The UI should:

- accept one markdown upload
- show parsing status
- show enrichment status only if browsing is used
- render the result without forcing a page reload

### 28.2 Result Screen

The result screen should include:

- uploaded file name
- parsed persona
- scenario summary
- baseline recommendation
- emotion switcher for all 6 emotions
- KPI matrix with risk flags
- persona lens
- public role context when used
- blind spots
- suggested next step
- confidence and divergence from baseline

### 28.3 Error And Partial-State Handling

If parsing fails, the app should show exactly what is missing.

If enrichment is skipped, the UI should say that clearly.

If enrichment is used, the public context section must be visibly labeled as public role context.

If the scenario is incomplete, the app should render a targeted clarification prompt instead of pretending a full result exists.

## 29. Failure Behavior

The backend should degrade gracefully.

Rules:

- if persona is missing, return a targeted prompt asking who the decision-maker is
- if scenario is missing, return a targeted prompt asking for the scenario
- if the role is too vague, return either:
  - a clarification prompt
  - or enriched role context if enrichment is allowed and useful
- if browsing fails, continue without enrichment and label the result as non-enriched
- if analysis confidence is low, render uncertainty notes rather than blocking entirely

## 30. Module Boundaries

Keep the implementation modular.

Recommended modules:

- upload parser
- persona normalization
- optional role enrichment
- decision analysis engine
- JSON response builder
- frontend renderer

Do not:

- hardwire specific personas into the code
- bake scenario-specific KPI math into the UI layer
- couple parsing logic directly to browser rendering code

## 31. First Implementation Scope

The first implementation should include:

- one local server
- one upload page
- one markdown parser with labeled-section and heuristic fallback
- one analysis endpoint
- one reusable decision-result screen
- one initial role-enrichment path using public web research
- no database
- no auth
- no persistence

This keeps the first version focused on proving the upload -> parse -> enrich -> analyze -> render loop end to end.

## 32. Acceptance Criteria For The Webapp Extension

The webapp extension is successful if it:

- accepts one markdown file containing persona and scenario
- parses structured and semi-structured markdown inputs reliably
- asks for clarification only when analysis is genuinely blocked
- performs role enrichment only when explicitly requested or when the role is too underspecified
- keeps uploaded facts, public role context, and inferred assumptions separate
- computes baseline and 6-emotion outputs server-side
- renders the result inside one reusable interactive webapp
- remains usable even when enrichment fails or confidence is low
