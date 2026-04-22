# Upload Format

## Purpose

This reference shows the markdown format the webapp accepts as an uploaded file and explains how the backend processes each section.

## Required Sections

The uploaded file must contain at minimum:

- `Persona` — who is making the decision (role label or richer profile)
- `Scenario` — the situation and the decision being faced

If either is missing, the app returns a targeted clarification prompt rather than an empty result.

## Optional Sections

Include any of these to improve analysis quality:

- `Time Horizon` — how far out the decision effects should be considered
- `Stakeholders` — who is affected by the outcome
- `KPI Families` — which KPI categories matter most; maps to the eight standard categories
- `Decision Call` — the options being evaluated (e.g., "Fund now vs. defer vs. split")
- `Tension` — the core conflict or constraint driving urgency
- `Role enrichment: true` — request public role context enrichment

## Example File

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

## What the Backend Does With This File

1. Parses all labeled sections into structured fields
2. Normalizes the persona into the internal profile shape
3. Extracts options from the `Decision Call` section
4. Maps `KPI Families` to the eight standard categories
5. Scores each option across all KPIs under all six emotion codes
6. Returns a JSON payload with baseline + six emotion variants
7. The frontend renders an emotion switcher, KPI matrix, and blind spot panel

## Parsing Rules

The parser looks first for heading-based labeled sections (`## Persona`, `## Scenario`, etc.). When sections are absent or loosely structured, it falls back to heuristic extraction from headings, emphasis markers, and paragraph patterns.

## Clarification Behavior

If `Persona` or `Scenario` are missing, the webapp renders a targeted prompt:

```text
The uploaded file is missing a persona. Who is making this decision?
```
