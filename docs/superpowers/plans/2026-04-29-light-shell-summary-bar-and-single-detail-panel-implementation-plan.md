# Light Shell, Summary Bar, and Single Detail Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current dark, tabbed frontend shell with a light theme, compact top summary bar, and single persistent right detail panel while preserving the existing fixed-matrix and routing behavior.

**Architecture:** This is a shell-layer refactor centered in `app/static/index.html`. The work keeps the current frontend state model, matrix rendering, detail rendering, question routing hooks, and scenario modal behavior, but reshapes the DOM and CSS so the page matches the new light workspace design. The migration sequence keeps existing hooks alive until the single detail panel is fully wired, then removes obsolete tabbed chat affordances.

**Tech Stack:** Static HTML, CSS, and vanilla JavaScript in `app/static/index.html`; existing Python backend unchanged; browser verification via local server on `http://127.0.0.1:8010`.

---

## File Structure

- Modify: `app/static/index.html`
  - Replace dark shell tokens with light theme tokens
  - Rebuild top chrome into summary bar + compact scenario header
  - Convert right panel from tabbed detail/chat layout to one persistent detail surface
  - Move question input into the detail panel footer area
  - Preserve matrix rendering, selection, routing, and scenario modal hooks
- Create: `docs/superpowers/plans/2026-04-29-light-shell-summary-bar-and-single-detail-panel-implementation-plan.md`
  - Implementation plan document

## Task 1: Replace dark shell tokens with the light design system

**Files:**
- Modify: `app/static/index.html:708-1660`

- [ ] **Step 1: Write the failing visual expectation note in the plan comments**

Add this implementation comment near the shell token block so the refactor has an explicit target:

```html
<!-- Light shell target:
  - warm white page background
  - pale surfaces
  - low-contrast borders
  - restrained blue interaction accents
  - semantic lens tints recalibrated for light mode
-->
```

- [ ] **Step 2: Replace the current dark shell CSS variables with light-mode shell tokens**

Replace the current shell variable block with a light palette like:

```css
:root {
  --shell-bg: #f6f2ea;
  --shell-bg-soft: #fbf8f2;
  --shell-surface: rgba(255, 252, 246, 0.92);
  --shell-surface-strong: rgba(255, 253, 249, 0.98);
  --shell-raised: #fffdf9;
  --shell-lifted: #fffaf3;
  --shell-rim: rgba(18, 32, 51, 0.08);
  --shell-rim-strong: rgba(18, 32, 51, 0.12);
  --shell-text: #122033;
  --shell-muted: #5f6b7b;
  --shell-dim: #8892a1;
  --shell-blue: #2d6cdf;
  --shell-blue-dim: rgba(45, 108, 223, 0.10);
  --shell-amber: #b9832f;
  --shell-amber-dim: rgba(185, 131, 47, 0.10);
  --shell-red: #c15a4d;
  --shell-red-dim: rgba(193, 90, 77, 0.10);
  --shell-green: #2d8a66;
  --shell-green-dim: rgba(45, 138, 102, 0.10);
  --shell-violet: #7e68c8;
  --shell-violet-dim: rgba(126, 104, 200, 0.10);
  --shell-shadow: 0 18px 44px rgba(18, 32, 51, 0.06);
  --shell-font-display: "Avenir Next", "Segoe UI", sans-serif;
  --shell-font-body: "Avenir Next", "Segoe UI", sans-serif;
  --shell-font-mono: "IBM Plex Mono", monospace;
}
```

- [ ] **Step 3: Update global shell background and text styling**

Adjust the shell base so the app uses the new light background:

```css
html, body {
  background:
    radial-gradient(circle at 8% 0%, rgba(45, 108, 223, 0.08), transparent 28%),
    radial-gradient(circle at 92% 12%, rgba(193, 90, 77, 0.06), transparent 20%),
    linear-gradient(180deg, #f8f5ee 0%, #efe8db 100%);
  color: var(--shell-text);
  font-family: var(--shell-font-body);
  overflow: hidden;
}
```

- [ ] **Step 4: Re-style shared shell surfaces to use light cards**

Update shared shell panel classes so they no longer use dark fills:

```css
.matrix-cell,
.persp-label-shell,
.detail-card-shell,
.chat-foot-shell,
.scenario-modal-card-shell {
  background: var(--shell-raised);
  border: 1px solid var(--shell-rim);
  box-shadow: var(--shell-shadow);
}
```

- [ ] **Step 5: Run a quick static sanity check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path("app/static/index.html").read_text()
assert "--shell-bg" in text
assert "linear-gradient(180deg, #f8f5ee 0%, #efe8db 100%)" in text
print("light shell tokens present")
PY
```

Expected: `light shell tokens present`

- [ ] **Step 6: Commit**

```bash
git add app/static/index.html
git commit -m "feat: add light shell design tokens"
```

## Task 2: Rebuild the top chrome into summary bar plus compact header

**Files:**
- Modify: `app/static/index.html:747-905`
- Modify: `app/static/index.html:1684-1708`
- Modify: `app/static/index.html:2310-2408`

- [ ] **Step 1: Replace the current topbar markup with a compact summary bar structure**

Update the top shell HTML to this structure:

```html
<div class="topbar-shell">
  <div class="brand-shell">PORT TALBOT · DECISION FRAMEWORK</div>
  <div class="summary-pill-shell" id="scenarioSummaryPill">—</div>
  <select id="scenarioSelect" class="topbar-select"></select>
  <select id="personaSwitcher" class="persona-switcher-shell" aria-label="Select persona"></select>
</div>
```

- [ ] **Step 2: Add compact scenario header styling**

Add or replace header CSS so it uses a lighter, compressed layout:

```css
.matrix-head-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  padding: 14px 18px 10px;
  border-bottom: 1px solid var(--shell-rim);
  background: rgba(255, 253, 249, 0.65);
}

.mh-name-shell {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.15;
  color: var(--shell-text);
}

.mh-role-shell,
.mh-stat-shell,
.eyebrow-shell {
  color: var(--shell-muted);
}
```

- [ ] **Step 3: Add a dedicated summary pill style**

Use a compact pill like:

```css
.summary-pill-shell {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  max-width: min(540px, 42vw);
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(45, 108, 223, 0.18);
  background: rgba(45, 108, 223, 0.08);
  color: var(--shell-green);
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

- [ ] **Step 4: Populate the summary pill from the active persona and scenario**

Inside the existing render path, add a helper like:

```js
function renderSummaryPill(persona, scenario) {
  if (!els.ctxChip) return;
  const personaCode = persona?.id || "";
  const scenarioTitle = scenario?.scenarioTitle || scenario?.label || "No active scenario";
  els.ctxChip.textContent = `${personaCode} · ${scenarioTitle}`;
}
```

Then call it from the main header render flow after persona and scenario are resolved.

- [ ] **Step 5: Keep modal-based scenario expansion and remove inline expansion pressure**

Preserve:

```js
els.toggleScenarioDescription?.addEventListener("click", () => {
  openScenarioModal();
});
```

Do not reintroduce inline description expansion.

- [ ] **Step 6: Run a static render hook check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path("app/static/index.html").read_text()
for needle in [
    'id="scenarioSummaryPill"',
    'function renderSummaryPill(',
    'openScenarioModal()'
]:
    assert needle in text, needle
print("summary bar hooks present")
PY
```

Expected: `summary bar hooks present`

- [ ] **Step 7: Commit**

```bash
git add app/static/index.html
git commit -m "feat: add summary bar and compact scenario header"
```

## Task 3: Convert the right side into one persistent decision detail panel

**Files:**
- Modify: `app/static/index.html:1208-1595`
- Modify: `app/static/index.html:1710-1742`
- Modify: `app/static/index.html:4812-4921`
- Modify: `app/static/index.html:5498-5515`

- [ ] **Step 1: Replace the tabbed right-panel markup with a single panel**

Replace the current tabbed right-panel HTML with:

```html
<aside class="right-panel-shell">
  <div class="detail-panel-head-shell">Decision Detail</div>
  <div class="detail-scroll-shell" id="detailScroll">
    <div class="detail-empty-shell">
      <div class="detail-empty-glyph-shell">◈</div>
      <div class="detail-empty-text-shell">Click any cell to inspect the full decision view, risk, consequences, and recommended move for that perspective × decision-lens combination.</div>
    </div>
  </div>
  <div class="detail-question-shell">
    <div class="ctx-line-shell">
      <span>Ask a question</span>
    </div>
    <div class="question-assist" id="questionAssist" hidden></div>
    <div class="inp-row-shell">
      <div class="inp-wrap-shell">
        <textarea id="questionInput" rows="1" placeholder="What is my best decision?"></textarea>
      </div>
      <button class="send-shell" id="routeQuestionButton" type="button" aria-label="Send question">
        <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/></svg>
      </button>
    </div>
  </div>
</aside>
```

- [ ] **Step 2: Remove tab CSS and add single-panel styling**

Delete or stop using:

```css
.rp-tabs-shell {}
.rp-tab-shell {}
.right-tab-shell {}
```

Replace with:

```css
.right-panel-shell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 0;
  min-height: 0;
  background: rgba(255, 253, 249, 0.7);
  border-left: 1px solid var(--shell-rim);
}

.detail-panel-head-shell {
  padding: 16px 18px 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.3px;
  text-transform: uppercase;
  color: var(--shell-blue);
  border-bottom: 1px solid var(--shell-rim);
}

.detail-question-shell {
  padding: 14px;
  border-top: 1px solid var(--shell-rim);
  background: rgba(255, 253, 249, 0.92);
}
```

- [ ] **Step 3: Make `switchTab` a no-op compatibility shim**

Replace tab switching logic with:

```js
function switchTab() {
  state.activeTab = "detail";
}
```

This keeps existing callers from breaking while removing visual mode switching.

- [ ] **Step 4: Route both question answers and manual cell clicks into the same detail surface**

Keep these lines active in the click and question flows:

```js
renderDecisionDetail(cell, backendAnswer);
state.backendAnswer = usesFixedMatrixScenario(getScenario()) ? buildBackendAnswerFromFixedCell(activeCell) : null;
```

Remove calls that depend on a separate chat tab becoming visible.

- [ ] **Step 5: Remove tab button event listeners**

Delete:

```js
els.tabButtonDetail?.addEventListener("click", () => switchTab("detail"));
els.tabButtonChat?.addEventListener("click", () => switchTab("chat"));
```

Keep the rest of the routing listeners intact.

- [ ] **Step 6: Run a structural compatibility check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path("app/static/index.html").read_text()
assert "detail-panel-head-shell" in text
assert 'id="detailScroll"' in text
assert 'id="questionInput"' in text
assert 'id="routeQuestionButton"' in text
assert "tabButtonChat" not in text
assert "tabButtonDetail" not in text
print("single detail panel structure present")
PY
```

Expected: `single detail panel structure present`

- [ ] **Step 7: Commit**

```bash
git add app/static/index.html
git commit -m "feat: replace tabbed right panel with single detail surface"
```

## Task 4: Restyle the matrix and detail cards for the light workspace

**Files:**
- Modify: `app/static/index.html:1038-1406`
- Modify: `app/static/index.html:4366-4887`

- [ ] **Step 1: Re-style matrix headers, perspective rail, and cells**

Update matrix card styles to lighter surfaces:

```css
.matrix-head.cautious { background: rgba(185, 131, 47, 0.10); color: var(--shell-amber); border: 1px solid rgba(185, 131, 47, 0.18); }
.matrix-head.strategic { background: rgba(45, 108, 223, 0.08); color: var(--shell-blue); border: 1px solid rgba(45, 108, 223, 0.16); }
.matrix-head.decisive { background: rgba(193, 90, 77, 0.08); color: var(--shell-red); border: 1px solid rgba(193, 90, 77, 0.16); }
.matrix-head.analytical { background: rgba(126, 104, 200, 0.08); color: var(--shell-violet); border: 1px solid rgba(126, 104, 200, 0.16); }

.matrix-cell.active {
  border-color: var(--shell-blue);
  background: rgba(45, 108, 223, 0.08);
}

.matrix-cell.routed {
  border-color: var(--shell-amber);
  background: rgba(185, 131, 47, 0.08);
  box-shadow: none;
}
```

- [ ] **Step 2: Tighten matrix data legibility for light mode**

Keep the one-line alignment rules and ensure readable contrast:

```css
.cell-data-value {
  color: var(--shell-text);
  font-weight: 700;
}

.cell-data-label {
  color: #2f5c9f;
  font-weight: 600;
}

.cell-meta {
  color: var(--shell-muted);
}
```

- [ ] **Step 3: Re-style decision detail cards to stacked light panels**

Update detail card visuals like:

```css
.detail-card-shell {
  padding: 16px;
  background: var(--shell-surface-strong);
  border: 1px solid var(--shell-rim);
  border-radius: 16px;
  gap: 10px;
}

.detail-title-shell {
  color: var(--shell-text);
  font-size: 20px;
}

.detail-copy-shell,
.detail-list-shell li,
.detail-bar-copy-shell,
.metric-value-shell {
  color: var(--shell-muted);
}
```

- [ ] **Step 4: Keep the visual signals block but re-style it for light mode**

Update the bar track and fill styles:

```css
.detail-bar-track-shell {
  background: rgba(18, 32, 51, 0.06);
  border: 1px solid rgba(18, 32, 51, 0.06);
}

.detail-bar-fill-shell {
  background: linear-gradient(90deg, #4f8dff, #7e68c8);
}
```

- [ ] **Step 5: Run a static light-mode class check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path("app/static/index.html").read_text()
for needle in [
    "background: rgba(45, 108, 223, 0.08);",
    "background: var(--shell-surface-strong);",
    "linear-gradient(90deg, #4f8dff, #7e68c8)"
]:
    assert needle in text, needle
print("light matrix and detail styling present")
PY
```

Expected: `light matrix and detail styling present`

- [ ] **Step 6: Commit**

```bash
git add app/static/index.html
git commit -m "feat: restyle matrix and decision detail for light workspace"
```

## Task 5: Responsive polish and runtime verification

**Files:**
- Modify: `app/static/index.html:1595-1660`

- [ ] **Step 1: Make the topbar wrap safely before overflowing**

Use responsive rules like:

```css
@media (max-width: 1280px) {
  .topbar-shell {
    flex-wrap: wrap;
    align-content: center;
    row-gap: 8px;
    padding: 10px 12px;
    height: auto;
  }

  .summary-pill-shell,
  .topbar-select,
  .persona-switcher-shell {
    width: 100%;
    max-width: none;
  }
}
```

- [ ] **Step 2: Keep the right panel height-bounded and usable**

Use:

```css
.right-panel-shell,
.detail-scroll-shell {
  min-height: 0;
  overflow: hidden;
}

.detail-scroll-shell {
  overflow: auto;
}
```

- [ ] **Step 3: Keep matrix rows compact on laptop screens**

Adjust the matrix row and cell sizing so the matrix remains visible:

```css
@media (max-width: 1400px) {
  .matrix-row {
    grid-template-columns: 160px repeat(4, minmax(0, 1fr));
  }

  .matrix-cell {
    padding: 8px 10px;
  }
}
```

- [ ] **Step 4: Run JS parse verification**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import re
text = Path("app/static/index.html").read_text()
match = re.search(r"<script>([\s\S]*)</script>\s*</body>", text)
assert match, "script block missing"
script = match.group(1)
compile(script, "inline-script", "exec")
print("inline script parses")
PY
```

Expected: `inline script parses`

- [ ] **Step 5: Run local server health verification**

Run:

```bash
curl -s http://127.0.0.1:8010/health
```

Expected: a healthy JSON response such as:

```json
{"ok": true}
```

- [ ] **Step 6: Run matrix bootstrap verification**

Run:

```bash
curl -s http://127.0.0.1:8010/matrix-bootstrap
```

Expected:

- a valid JSON payload
- personas present
- scenarios present
- fixed decision framework present

- [ ] **Step 7: Manual browser verification**

Check in `http://127.0.0.1:8010`:

- summary bar is visible and compact
- page is clearly light mode
- scenario modal still opens from `Expand scenario`
- matrix remains the dominant surface
- right detail panel is always visible
- clicking a cell updates the detail panel
- asking a question updates the same detail panel
- no separate tabbed assistant UI remains

- [ ] **Step 8: Commit**

```bash
git add app/static/index.html
git commit -m "feat: finish light shell responsive polish"
```

## Self-Review

### Spec coverage

Covered requirements:

- light theme conversion: Tasks 1 and 4
- compact top summary bar: Task 2
- compressed scenario header: Task 2
- modal-based scenario expansion preserved: Task 2
- matrix remains dominant: Tasks 2, 4, and 5
- single right detail panel: Task 3
- question input moved into the detail panel: Task 3
- responsive overflow control: Task 5
- no backend behavior change: all tasks stay within `app/static/index.html`

No spec sections are currently uncovered.

### Placeholder scan

Checked for:

- `TBD`
- `TODO`
- “appropriate error handling”
- “write tests for the above”
- “similar to Task N”

None are present in this plan.

### Type consistency

This plan consistently uses the current frontend identifiers:

- `scenarioSelect`
- `personaSwitcher`
- `detailScroll`
- `questionInput`
- `routeQuestionButton`
- `openScenarioModal`
- `renderDecisionDetail`

The plan intentionally removes:

- `tabButtonDetail`
- `tabButtonChat`
- separate chat-tab dependencies

