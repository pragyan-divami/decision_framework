# Adaptive Decision Framing

Adaptive Decision Framing is a specialized Open Agent Skill and decision-support backend built to tackle decision paralysis by evaluating scenarios through multiple weighted emotional and cognitive lenses.

## What It Does
1. **Persona & Scenario Ingestion:** It ingests your specific persona (e.g., "CFO", "Single Parent", "Project Manager") and your complex scenario, ensuring that recommendations aren't just generic advice, but tailored exactly to your accountabilities.
2. **Emotional Taxonomy Mapping:** The system applies 6 different "emotional/cognitive" lenses to your decision:
   - **A. Cautious:** Risk-first, downside-protective
   - **B. Strategic:** Long-horizon, thesis-protective
   - **C. Diplomatic:** Stakeholder-balancing, coalition-sensitive
   - **D. Decisive:** Action-biased, commitment-oriented
   - **E. Analytical:** Model-driven, sensitivity-aware
   - **F. Pragmatic:** Outcome-focused, operationally grounded

3. **Adaptive KPI Output & Blind Spot Detection:** Each of these 6 states mathematically re-weights 8 core KPIs (debt, cost, cash, regulatory, timeline, customer, rating, emissions). The engine identifies not only the most mathematical "best" choice but flags dangerous **blind spots**. If the current emotion is over-indexing on timeline, what long-term systemic risks are you missing?
4. **Agent Skill Integration:** Since it operates out of the box as an Open Agent Skill (with `SKILL.md`), any LLM agent can use it to help you frame choices, interactively switching lenses and pointing out risk factors you haven't considered.

## Architecture
The system consists of two tightly integrated layers:
- **Instruction Prompt (Agent Skill)**: A canonical `SKILL.md` allows LLMs like Claude or Cursor to natively run the framing exercise alongside you in a text interface.
- **Python Deterministic Engine**: The core logic is powered by a robust Python HTTP backend (`app/server.py` and `app/decision_engine.py`) which acts as the mathematical engine parsing Markdown scenarios, applying the exact KPI score weights dynamically, and returning a localized decision matrix.

## Installation & Usage

**As an AI Agent Skill:**
You can natively install this repository into any compatible agent environment (via `skills.sh`) by running:
```bash
npx skills add pragyan-divami/decision_framework
```

**Running the Web Interface Locally:**
If you prefer a standalone deterministic web app instead of a chat-based LLM skill:
1. Ensure you have Python installed.
2. Run the server:
```bash
python app/server.py
```
3. The engine will serve the static UI where you can upload Markdown decision documents for interactive, multi-lens matrix rendering and analysis.
