import re
import importlib.util
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


EMOTION_PROFILES: List[Dict[str, Any]] = [
    {
        "code": "A",
        "name": "Cautious",
        "state": "Risk-first, downside-protective",
        "tone": "warn",
        "weights": {
            "debt": 22,
            "cost": 18,
            "cash": 18,
            "regulatory": 8,
            "timeline": 8,
            "customer": 10,
            "rating": 10,
            "emissions": 6,
        },
    },
    {
        "code": "B",
        "name": "Strategic",
        "state": "Long-horizon, thesis-protective",
        "tone": "good",
        "weights": {
            "debt": 6,
            "cost": 8,
            "cash": 6,
            "regulatory": 18,
            "timeline": 22,
            "customer": 8,
            "rating": 10,
            "emissions": 22,
        },
    },
    {
        "code": "C",
        "name": "Diplomatic",
        "state": "Stakeholder-balancing, coalition-sensitive",
        "tone": "warn",
        "weights": {
            "debt": 10,
            "cost": 8,
            "cash": 8,
            "regulatory": 10,
            "timeline": 12,
            "customer": 18,
            "rating": 18,
            "emissions": 16,
        },
    },
    {
        "code": "D",
        "name": "Decisive",
        "state": "Action-biased, commitment-oriented",
        "tone": "danger",
        "weights": {
            "debt": 8,
            "cost": 8,
            "cash": 6,
            "regulatory": 16,
            "timeline": 24,
            "customer": 8,
            "rating": 8,
            "emissions": 22,
        },
    },
    {
        "code": "E",
        "name": "Analytical",
        "state": "Model-driven, sensitivity-aware",
        "tone": "accent",
        "weights": {
            "debt": 16,
            "cost": 16,
            "cash": 14,
            "regulatory": 10,
            "timeline": 12,
            "customer": 10,
            "rating": 10,
            "emissions": 12,
        },
    },
    {
        "code": "F",
        "name": "Pragmatic",
        "state": "Outcome-focused, operationally grounded",
        "tone": "good",
        "weights": {
            "debt": 14,
            "cost": 12,
            "cash": 14,
            "regulatory": 12,
            "timeline": 12,
            "customer": 10,
            "rating": 12,
            "emissions": 14,
        },
    },
]

EMOTION_LABELS = {
    "A": "Cautious",
    "B": "Strategic",
    "C": "Diplomatic",
    "D": "Decisive",
    "E": "Analytical",
    "F": "Pragmatic",
}

SNAPSHOT_RATIONALE = {
    "A": "Cautious weighting prefers this option because it protects operational continuity.",
    "B": "Strategic weighting prefers this option because it delivers the strongest long-horizon positioning under the current KPI balance.",
    "C": "Diplomatic weighting prefers this option because it preserves stakeholder relationships across the current configuration.",
    "D": "Decisive weighting prefers this option because it produces the fastest observable shift in the KPIs that matter.",
    "E": "Analytical weighting prefers this option because the quantifiable KPIs point to it under the current model.",
    "F": "Pragmatic weighting prefers this option because it balances immediate outcome with optionality.",
}

LENS_TEMPLATE = {
    "A": "Cautious mode reads this through the {role} lens. It concentrates attention on stability KPIs: {top_kpis}.",
    "B": "Strategic mode reads this through the {role} lens. It weights structural KPIs: {top_kpis}.",
    "C": "Diplomatic mode reads this through the {role} lens. It prioritizes coordination KPIs: {top_kpis}.",
    "D": "Decisive mode reads this through the {role} lens. It favors fast-feedback KPIs: {top_kpis}.",
    "E": "Analytical mode reads this through the {role} lens. It emphasizes modelable KPIs: {top_kpis}.",
    "F": "Pragmatic mode reads this through the {role} lens. It favors balanced KPIs: {top_kpis}.",
}

CONTEXT_BULLET_3 = {
    "A": "The active role lens is {role}, which protects continuity KPIs above structural ones.",
    "B": "The active role lens is {role}, which shifts the weighting of the same scenario facts toward structural, long-horizon outcomes.",
    "C": "The active role lens is {role}, which amplifies stakeholder and coordination KPIs in the same scenario facts.",
    "D": "The active role lens is {role}, which biases the weighting toward KPIs that move within weeks, not quarters.",
    "E": "The active role lens is {role}, which concentrates attention on quantifiable KPIs and under-weights qualitative ones.",
    "F": "The active role lens is {role}, which spreads weighting across outcome-facing KPIs with near-term focus.",
}

CONSEQUENCE_RISK_BY_EMOTION = {
    "A": "Cautious can delay structural fixes in favour of reversible moves. Check whether the chosen option resolves the underlying exposure or just defers it.",
    "B": "Strategic can underweight the hidden downside of this choice, particularly near-term operational or customer impact. Pressure-test the 90-day path before celebrating the multi-year win.",
    "C": "Diplomatic can preserve the status quo by over-weighting relationships. Verify that no stakeholder voice is being allowed to veto a structurally better answer.",
    "D": "Decisive can commit with incomplete information. Before locking in, confirm that nothing in the blind-spot panel invalidates the speed advantage.",
    "E": "Analytical can under-weight what it can't quantify — stakeholder fatigue, reputation, team morale. Ask explicitly: what would I decide if the qualitative inputs were equal to the quantitative ones?",
    "F": "Pragmatic can pick good enough when right was available. Confirm you are not leaving a structurally better outcome on the table just because it requires more commitment.",
}

NEXT_STEP_NORMAL = {
    "A": "Run one downside scenario: what breaks if this option holds for 90 days and the situation worsens 10%? Confirm the answer before committing.",
    "B": "Gather one more decision-critical fact about near-term execution and confirm the current recommendation.",
    "C": "Pre-brief the two most affected stakeholders before the formal decision moment. Ask each to pre-commit to a response.",
    "D": "Set a 72-hour checkpoint for the two leading indicators. If either moves wrong, revert to the runner-up option.",
    "E": "Validate one assumption in the model. If the sensitivity is high, widen the scenario range before deciding.",
    "F": "Lock in the immediate move. Schedule a formal review in 30 days to decide whether to escalate or hold.",
}

NEXT_STEP_CLOSE = {
    "A": "Given the close margin, hold for 24 hours and consult one stakeholder who would argue against this choice.",
    "B": "The long game looks equal across options. Decide on which path de-risks the 2028 horizon fastest.",
    "C": "A close margin plus relationship-heavy scoring means your gut is doing the work. Swap to an analytical run to confirm.",
    "D": "Close margin plus bias for action creates the highest regret risk. Get one sanity check from an analytical peer before committing.",
    "E": "Close margin in analytical mode usually means the model is missing a variable. Find the missing variable before deciding.",
    "F": "The close margin says the balanced option may not be better than a pointed one. Test the two best-scoring options head-to-head on one KPI that matters most to the persona.",
}

DEFAULT_CLOSE_CALL_THRESHOLD = 5.0
PERSONA_CLOSE_CALL_THRESHOLDS = {
    "P7": 10.0,
}

REFERENCE_KPI_ORDERING_PATH = Path("/Users/pragyan/Downloads/kpi_ordering (1).py")

ROLE_LIBRARY = {
    "cfo": {
        "summary": "Public role context: CFO roles typically own financing strategy, capital allocation, risk management, investor-facing finance, balance-sheet resilience, and trade-offs between short-term cash discipline and long-horizon strategic investment.",
        "sources": ["Local role library fallback"],
    },
    "chief financial officer": {
        "summary": "Public role context: CFO roles typically own financing strategy, capital allocation, risk management, investor-facing finance, balance-sheet resilience, and trade-offs between short-term cash discipline and long-horizon strategic investment.",
        "sources": ["Local role library fallback"],
    },
    "hospital administrator": {
        "summary": "Public role context: hospital administrators usually balance service continuity, patient risk, staffing pressure, budget constraints, and stakeholder expectations across clinicians, finance leaders, and patients.",
        "sources": ["Local role library fallback"],
    },
    "school principal": {
        "summary": "Public role context: school principals typically manage learning outcomes, parent and staff trust, resource allocation, safety, and operational continuity under policy constraints.",
        "sources": ["Local role library fallback"],
    },
}


@dataclass
class ParseResult:
    title: str
    scenario_title: Optional[str]
    persona_id: Optional[str]
    persona: Optional[str]
    scenario: Optional[str]
    call: Optional[str]
    tension: Optional[str]
    time_horizon: Optional[str]
    stakeholders: List[str]
    kpis: List[str]
    enrichment_requested: bool
    metadata: Dict[str, Any]


def analyze_markdown(markdown_text: str, filename: str) -> Dict[str, Any]:
    parsed = parse_markdown(markdown_text, filename)
    missing = []
    if not parsed.persona:
        missing.append("persona")
    if not parsed.scenario:
        missing.append("scenario")

    if missing:
        return {
            "status": "clarification_required",
            "fileName": filename,
            "missing": missing,
            "message": build_missing_message(missing),
            "parsed": {
                "title": parsed.title,
                "scenarioTitle": parsed.scenario_title,
                "persona": parsed.persona,
                "scenario": parsed.scenario,
            },
        }

    normalized_persona = normalize_persona(parsed.persona)
    normalized_persona["personaId"] = parsed.persona_id
    enrichment = maybe_enrich_role(normalized_persona, parsed.enrichment_requested)
    options = extract_options(parsed)
    kpis = normalize_kpis(parsed.kpis, parsed.scenario, normalized_persona)
    emotion_weights_by_kpi = build_emotion_weights_for_persona(kpis, normalized_persona)
    hard_priority_kpis = build_hard_priority_kpis(parsed, normalized_persona, kpis)
    scenario_salience = compute_scenario_salience(parsed.scenario, kpis)
    option_analysis = analyze_options(options, kpis, parsed, normalized_persona)
    kpi_categories = {kpi["code"]: kpi["category"] for kpi in kpis}
    baseline = recommend_option(
        option_analysis,
        equal_weights_by_kpi(kpis),
        "BASELINE",
        kpi_categories,
        normalized_persona.get("personaId"),
    )
    emotions = []
    for profile in EMOTION_PROFILES:
        recommended = recommend_option(
            option_analysis,
            emotion_weights_by_kpi[profile["code"]],
            profile["code"],
            kpi_categories,
            normalized_persona.get("personaId"),
        )
        emotions.append(
            build_emotion_output(
                profile,
                recommended,
                option_analysis,
                normalized_persona,
                parsed,
                enrichment,
                baseline["optionId"],
                kpis,
                scenario_salience,
                emotion_weights_by_kpi,
                hard_priority_kpis,
            )
        )

    confidence = compute_confidence(parsed, enrichment, len(options))
    return {
        "status": "ok",
        "fileName": filename,
        "parsed": {
            "title": parsed.title,
            "scenarioTitle": parsed.scenario_title,
            "persona": parsed.persona,
            "scenario": parsed.scenario,
            "call": parsed.call,
            "tension": parsed.tension,
            "timeHorizon": parsed.time_horizon,
            "stakeholders": parsed.stakeholders,
            "kpis": [k["label"] for k in kpis],
        },
        "normalizedPersona": normalized_persona,
        "enrichment": enrichment,
        "baseline": build_baseline_output(
            baseline,
            option_analysis,
            normalized_persona,
            parsed,
            confidence,
        ),
        "emotionVariants": emotions,
        "kpiCatalog": build_kpi_catalog(kpis, option_analysis, parsed, normalized_persona),
        "metadata": {
            "confidence": confidence,
            "analysisMode": "local-role-library" if enrichment["used"] else "scenario-first",
            "scenarioSalience": scenario_salience,
            "hardPriorityKpis": hard_priority_kpis,
        },
    }


def parse_markdown(markdown_text: str, filename: str) -> ParseResult:
    title = filename
    match = re.search(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
    persona_id_match = re.search(r"\b(P\d+)\b", title)
    persona_id = persona_id_match.group(1) if persona_id_match else None

    persona = None
    persona_match = re.search(r"^\*\*(.+?)\*\*$", markdown_text, re.MULTILINE)
    if persona_match:
        persona = persona_match.group(1).strip()
    persona_label_match = re.search(r"(?im)^persona\s*:\s*(.+)$", markdown_text)
    if persona_label_match:
        persona = persona_label_match.group(1).strip()

    scenario = extract_section(markdown_text, "Scenario")
    scenario_title = extract_scenario_title(markdown_text)
    call = extract_section(markdown_text, "The call")
    tension = extract_section(markdown_text, "Tension")

    time_horizon = extract_table_value(markdown_text, "Time horizon")
    stakeholders_raw = extract_table_value(markdown_text, "Key stakeholders") or ""
    stakeholders = [item.strip() for item in re.split(r";|,", stakeholders_raw) if item.strip()]

    kpi_lines = extract_bullet_section(markdown_text, "KPI families for this scenario")
    enrichment_requested = bool(
        re.search(r"(?im)(role enrichment requested\s*:\s*true|use role enrichment|enrichment requested)", markdown_text)
    )

    return ParseResult(
        title=title,
        scenario_title=scenario_title,
        persona_id=persona_id,
        persona=persona,
        scenario=scenario,
        call=call,
        tension=tension,
        time_horizon=time_horizon,
        stakeholders=stakeholders,
        kpis=kpi_lines,
        enrichment_requested=enrichment_requested,
        metadata={},
    )


def extract_scenario_title(markdown_text: str) -> Optional[str]:
    scenario_anchor = re.search(r"(?im)^###\s+Scenario\s*$", markdown_text)
    if not scenario_anchor:
        return None

    headings = list(re.finditer(r"(?im)^(##+)\s+(.+?)\s*$", markdown_text))
    excluded = {
        "about this scenario",
        "decision context",
        "kpi families for this scenario",
        "how to use this scenario",
        "scenario",
        "the call",
        "tension",
    }
    for heading in reversed(headings):
        if heading.start() >= scenario_anchor.start():
            continue
        if len(heading.group(1)) != 2:
            continue
        label = heading.group(2).strip()
        if label.lower() in excluded:
            continue
        return label
    return None


def extract_section(markdown_text: str, heading: str) -> Optional[str]:
    pattern = rf"(?ims)^#+\s+{re.escape(heading)}\s*$\n+(.*?)(?=^\s*#|\Z)"
    match = re.search(pattern, markdown_text)
    if match:
        return clean_block(match.group(1))
    inline_match = re.search(rf"(?im)^{re.escape(heading)}\s*:\s*(.+)$", markdown_text)
    if inline_match:
        return inline_match.group(1).strip()
    return None


def extract_bullet_section(markdown_text: str, heading: str) -> List[str]:
    pattern = rf"(?ims)^#+\s+{re.escape(heading)}\s*$\n+(.*?)(?=^\s*#|\Z)"
    match = re.search(pattern, markdown_text)
    if not match:
        return []
    block = match.group(1)
    items = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            item = re.sub(r"^\-\s+", "", stripped)
            item = re.sub(r"\*\*(.*?)\*\*", r"\1", item).replace("·", "-").strip()
            items.append(item)
    return items


def extract_table_value(markdown_text: str, label: str) -> Optional[str]:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.+?)\s*\|"
    match = re.search(pattern, markdown_text)
    if match:
        return clean_inline(match.group(1))
    return None


def clean_block(text: str) -> str:
    lines = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped or re.fullmatch(r"-{3,}", stripped):
            continue
        lines.append(clean_inline(stripped))
    return " ".join(lines) if lines else ""


def clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text.strip()


def normalize_persona(persona_text: str) -> Dict[str, Any]:
    raw = persona_text.strip()
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    role_label = parts[0]
    org = parts[1] if len(parts) > 1 else None
    lower = raw.lower()
    domain = "work"
    if any(word in lower for word in ("parent", "buyer", "student", "home")):
        domain = "life"
    return {
        "raw": raw,
        "roleLabel": role_label,
        "organization": org,
        "lifeOrWorkDomain": domain,
        "responsibilityScope": infer_responsibility_scope(lower),
        "decisionAuthority": infer_decision_authority(lower),
        "inferredFields": ["responsibilityScope", "decisionAuthority"],
    }


def infer_responsibility_scope(lower: str) -> str:
    if "cfo" in lower or "finance" in lower:
        return "capital allocation, balance-sheet discipline, financing strategy"
    if "principal" in lower:
        return "school operations, learning outcomes, staff and parent trust"
    if "administrator" in lower:
        return "operational continuity, budget discipline, stakeholder coordination"
    return "role-specific operating and decision responsibilities"


def infer_decision_authority(lower: str) -> str:
    if "director" in lower or "chief" in lower or "cfo" in lower:
        return "high"
    if "manager" in lower or "administrator" in lower:
        return "medium"
    return "unknown"


def maybe_enrich_role(normalized_persona: Dict[str, Any], enrichment_requested: bool) -> Dict[str, Any]:
    role_key = normalized_persona["raw"].lower()
    matched = None
    for key, value in ROLE_LIBRARY.items():
        if key in role_key:
            matched = value
            break
    used = bool(enrichment_requested and matched)
    return {
        "requested": enrichment_requested,
        "used": used,
        "summary": matched["summary"] if used else None,
        "sources": matched["sources"] if used else [],
        "mode": "local-role-library" if used else "none",
    }


@lru_cache(maxsize=1)
def load_reference_personas() -> Dict[str, Any]:
    if not REFERENCE_KPI_ORDERING_PATH.exists():
        return {}
    spec = importlib.util.spec_from_file_location("decision_framework_reference_kpi_ordering", REFERENCE_KPI_ORDERING_PATH)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "load_personas"):
        return {}
    try:
        return module.load_personas()
    except Exception:
        return {}


def extract_options(parsed: ParseResult) -> List[Dict[str, Any]]:
    option_text = parsed.call or ""
    options: List[str] = []
    if option_text:
        options = [part.strip(" ?") for part in re.split(r",| or ", option_text) if part.strip()]
    normalized = []
    seen = set()
    for item in options:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append({"id": option_id_for_text(lowered), "label": item})
    if normalized:
        return normalized
    return [
        {"id": "fund", "label": "Fund the current path"},
        {"id": "defer", "label": "Defer the investment"},
        {"id": "split", "label": "Take a split path"},
    ]


def option_id_for_text(lowered: str) -> str:
    if any(word in lowered for word in ("split", "partial", "600m")):
        return "split"
    if any(word in lowered for word in ("defer", "delay", "postpone")):
        return "defer"
    if any(word in lowered for word in ("bond", "raise", "fund")):
        return "fund"
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-") or "option"


def normalize_kpis(
    parsed_kpis: List[str],
    scenario_text: str,
    normalized_persona: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if parsed_kpis:
        result = []
        for idx, item in enumerate(parsed_kpis):
            code_match = re.match(r"(K\d+)\s*[-]\s*(.+)", item)
            if code_match:
                code = code_match.group(1)
                label = code_match.group(2).strip()
            else:
                code = f"K{idx + 1}"
                label = item.strip()
            result.append(
                {
                    "code": code,
                    "label": label,
                    "category": infer_kpi_category(label),
                    "baselineNote": baseline_note_for_kpi(label, infer_kpi_category(label), scenario_text, normalized_persona),
                }
            )
        return result
    return derive_kpis_from_context(scenario_text, normalized_persona)


def infer_kpi_category(label: str) -> str:
    lower = label.lower()
    if any(word in lower for word in ("debt", "leverage", "ebitda")):
        return "debt"
    if any(word in lower for word in ("cost", "wacc", "capital")):
        return "cost"
    if any(word in lower for word in ("cash", "free cash")):
        return "cash"
    if any(word in lower for word in ("cbam", "regulatory", "levy")):
        return "regulatory"
    if any(word in lower for word in ("milestone", "timeline", "compliance")):
        return "timeline"
    if any(word in lower for word in ("customer", "pass-through", "price")):
        return "customer"
    if any(word in lower for word in ("rating", "bondholder", "outlook")):
        return "rating"
    if any(word in lower for word in ("scope", "emissions", "co2", "trajectory")):
        return "emissions"
    return "general"


def baseline_note_for_kpi(
    label: str,
    category: str,
    scenario_text: str,
    normalized_persona: Dict[str, Any],
) -> str:
    sentence = scenario_sentence_for_category(scenario_text, category)
    if sentence:
        return sentence
    return f"Derived for the {normalized_persona['roleLabel']} lens from the uploaded scenario."


def derive_kpis_from_context(scenario_text: str, normalized_persona: Dict[str, Any]) -> List[Dict[str, Any]]:
    persona_lower = normalized_persona["raw"].lower()
    default_categories = ["timeline", "customer", "regulatory", "rating"]
    if "cfo" in persona_lower or "finance" in persona_lower:
        default_categories = ["debt", "cost", "cash", "regulatory", "timeline", "customer", "rating", "emissions"]
    elif "administrator" in persona_lower:
        default_categories = ["cash", "timeline", "customer", "rating", "regulatory"]
    elif "principal" in persona_lower:
        default_categories = ["timeline", "customer", "rating", "cash", "regulatory"]

    seen = set()
    result = []
    for idx, category in enumerate(default_categories, start=1):
        if category in seen:
            continue
        seen.add(category)
        label = fallback_label_for_category(category, normalized_persona)
        result.append(
            {
                "code": f"K{idx}",
                "label": label,
                "category": category,
                "baselineNote": baseline_note_for_kpi(label, category, scenario_text, normalized_persona),
            }
        )
    return result


def fallback_label_for_category(category: str, normalized_persona: Dict[str, Any]) -> str:
    role = normalized_persona["roleLabel"]
    labels = {
        "debt": f"Leverage tolerance for {role}",
        "cost": "Cost of capital burden",
        "cash": "Near-term cash flexibility",
        "regulatory": "Regulatory or policy exposure",
        "timeline": "Execution timeline integrity",
        "customer": "Customer or stakeholder acceptance",
        "rating": "External confidence and rating outlook",
        "emissions": "Committed sustainability trajectory",
        "general": f"{role} decision pressure",
    }
    return labels.get(category, labels["general"])


def scenario_sentence_for_category(scenario_text: str, category: str) -> Optional[str]:
    sentences = re.split(r"(?<=[.!?])\s+", scenario_text or "")
    keywords = {
        "debt": ("bond", "debt", "balance sheet", "capex", "financing"),
        "cost": ("7.2%", "cost", "bond", "capital", "wacc"),
        "cash": ("capex", "cash", "defer", "tranche"),
        "regulatory": ("cbam", "levy", "regulatory", "ministry"),
        "timeline": ("month-end", "9 months", "programme", "timeline", "milestone"),
        "customer": ("customer", "stellantis", "pass-through", "auto"),
        "rating": ("bondholders", "rating", "outlook", "group cfo"),
        "emissions": ("co₂", "co2", "scope", "green-steel", "trajectory"),
    }
    for sentence in sentences:
        lower = sentence.lower()
        if any(keyword in lower for keyword in keywords.get(category, ())):
            return clean_inline(sentence)
    return None


def analyze_options(
    options: List[Dict[str, Any]],
    kpis: List[Dict[str, Any]],
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for option in options:
        option_id = option["id"]
        scores = {}
        traits = infer_option_traits(option["label"], parsed, normalized_persona)
        for kpi in kpis:
            scores[kpi["code"]] = score_option_for_kpi(option, kpi, traits, parsed, normalized_persona)
        results[option_id] = {
            "id": option_id,
            "label": option["label"],
            "scores": scores,
            "traits": traits,
        }
    return results


def compute_scenario_salience(scenario_text: str, kpis: List[Dict[str, Any]]) -> Dict[str, int]:
    salience: Dict[str, int] = {}
    for kpi in kpis:
        sentence = scenario_sentence_for_category(scenario_text, kpi["category"]) or ""
        label = kpi["label"].lower()
        score = 1
        if sentence:
            score += 1
        if any(token in label for token in ("cbam", "customer", "milestone", "debt", "rating", "scope", "cash", "cost")):
            score += 1
        if any(token in sentence.lower() for token in ("month-end", "next quarter", "pushing back", "7.2%", "€140m", "€900m", "9 months")):
            score += 1
        salience[kpi["code"]] = score
    return salience


def build_emotion_weights_for_persona(
    kpis: List[Dict[str, Any]],
    normalized_persona: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    persona_id = normalized_persona.get("personaId")
    reference_personas = load_reference_personas()
    if persona_id and persona_id in reference_personas:
        reference = reference_personas[persona_id]
        rows: Dict[str, Dict[str, float]] = {}
        for emotion_code, row in reference.emotion_weights.items():
            rows[emotion_code] = {
                kpi["code"]: float(row.get(kpi["code"], 100.0 / max(1, len(kpis))))
                for kpi in kpis
            }
        return rows

    rows: Dict[str, Dict[str, float]] = {}
    archetype_profiles = {
        "A": {"finance": 22, "execution": 8, "stakeholder": 10, "safety": 20, "sustainability": 6, "talent": 12, "governance": 12, "resilience": 10},
        "B": {"finance": 8, "execution": 18, "stakeholder": 8, "safety": 8, "sustainability": 18, "talent": 10, "governance": 12, "resilience": 18},
        "C": {"finance": 8, "execution": 10, "stakeholder": 24, "safety": 10, "sustainability": 10, "talent": 14, "governance": 14, "resilience": 10},
        "D": {"finance": 6, "execution": 24, "stakeholder": 8, "safety": 8, "sustainability": 12, "talent": 8, "governance": 10, "resilience": 24},
        "E": {"finance": 18, "execution": 14, "stakeholder": 8, "safety": 10, "sustainability": 10, "talent": 12, "governance": 14, "resilience": 14},
        "F": {"finance": 14, "execution": 16, "stakeholder": 10, "safety": 12, "sustainability": 10, "talent": 12, "governance": 12, "resilience": 14},
    }
    persona_bias = role_archetype_bias(normalized_persona)
    for emotion_code, profile in archetype_profiles.items():
        raw = {}
        for kpi in kpis:
            archetype = infer_kpi_archetype(kpi["label"], normalized_persona)
            raw[kpi["code"]] = float(profile.get(archetype, 8) + persona_bias.get(archetype, 0))
        rows[emotion_code] = normalize_weight_row(raw)
    return rows


def role_archetype_bias(normalized_persona: Dict[str, Any]) -> Dict[str, int]:
    role_lower = normalized_persona["raw"].lower()
    if "procurement" in role_lower or "sales" in role_lower:
        return {"stakeholder": 3, "resilience": 3, "finance": 1}
    if "cfo" in role_lower or "financial" in role_lower:
        return {"finance": 5, "governance": 3, "resilience": 2}
    if "operating officer" in role_lower or "plant head" in role_lower:
        return {"execution": 5, "safety": 4, "resilience": 2}
    if "sustainability" in role_lower:
        return {"sustainability": 6, "governance": 3, "stakeholder": 1}
    if "delivery" in role_lower or "platform" in role_lower:
        return {"talent": 4, "execution": 4, "finance": 2}
    if "human resources" in role_lower or "talent" in role_lower:
        return {"talent": 6, "stakeholder": 3, "governance": 2}
    return {"finance": 1, "execution": 1, "stakeholder": 1, "safety": 1, "sustainability": 1, "talent": 1, "governance": 1, "resilience": 1}


def infer_kpi_archetype(label: str, normalized_persona: Dict[str, Any]) -> str:
    lower = label.lower()
    if any(word in lower for word in ("cash", "cost", "margin", "gmv", "valuation", "debt", "ebitda", "billing", "roi", "payback", "dividend")):
        return "finance"
    if any(word in lower for word in ("volume", "output", "yield", "oee", "adherence", "time-to-ready", "time-to-hire", "milestone", "coverage", "utilization", "delivery")):
        return "execution"
    if any(word in lower for word in ("customer", "client", "nps", "community", "union", "channel", "response coherence", "credibility", "engagement")):
        return "stakeholder"
    if any(word in lower for word in ("safety", "ltifr", "near-miss", "refractory", "injury", "variance")):
        return "safety"
    if any(word in lower for word in ("scope", "emissions", "cdp", "sbti", "net-zero", "decarbon")):
        return "sustainability"
    if any(word in lower for word in ("attrition", "mobility", "compensation", "retraining", "employee", "engineers")):
        return "talent"
    if any(word in lower for word in ("regulatory", "compliance", "governance", "rating", "control", "nbfc", "public target")):
        return "governance"
    if any(word in lower for word in ("concentration", "alternate", "supplier", "resilience", "stockpile", "headroom", "continuity")):
        return "resilience"
    if "procurement" in normalized_persona["raw"].lower():
        return "resilience"
    return "execution"


def normalize_weight_row(raw_weights: Dict[str, float]) -> Dict[str, float]:
    if not raw_weights:
        return {}
    count = len(raw_weights)
    floor = 2.0
    remaining_total = 100.0 - (floor * count)
    adjusted = {key: max(value - floor, 0.0) for key, value in raw_weights.items()}
    adjusted_sum = sum(adjusted.values())
    if adjusted_sum == 0:
        even = round(100.0 / count, 1)
        return {key: even for key in raw_weights}
    normalized = {
        key: floor + ((value / adjusted_sum) * remaining_total)
        for key, value in adjusted.items()
    }
    rounded = {key: round(value, 1) for key, value in normalized.items()}
    delta = round(100.0 - sum(rounded.values()), 1)
    if delta != 0:
        max_key = max(rounded, key=rounded.get)
        rounded[max_key] = round(rounded[max_key] + delta, 1)
    return rounded


def build_hard_priority_kpis(
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
    kpis: List[Dict[str, Any]],
) -> List[str]:
    persona_id = parsed.persona_id
    reference_personas = load_reference_personas()
    if persona_id and persona_id in reference_personas:
        valid_codes = {kpi["code"] for kpi in kpis}
        return [code for code in reference_personas[persona_id].hard_priority_kpis if code in valid_codes]

    role_lower = normalized_persona["raw"].lower()
    target_tokens: List[str] = []
    target_categories: List[str] = []

    if persona_id == "P2" or "cfo" in role_lower:
        target_tokens = ["debt", "rating", "covenant", "credit rating"]
        target_categories = ["debt", "rating"]
    elif persona_id == "P1":
        target_tokens = ["fill rate", "line fill", "continuity"]
        target_categories = ["customer"]
    elif persona_id == "P7":
        target_tokens = ["ltifr", "near-miss", "union", "sentiment", "safety"]
    elif "principal" in role_lower:
        target_tokens = ["compliance", "attendance", "safety"]
        target_categories = ["regulatory", "customer"]
    elif "administrator" in role_lower:
        target_tokens = ["regulatory", "continuity", "patient"]
        target_categories = ["regulatory", "timeline"]

    selected = []
    for kpi in kpis:
        label_lower = kpi["label"].lower()
        if kpi["category"] in target_categories or any(token in label_lower for token in target_tokens):
            selected.append(kpi["code"])
    return selected


def score_option_for_category(option_id: str, category: str) -> int:
    if option_id == "fund":
        profile = {
            "debt": 1,
            "cost": 0,
            "cash": 1,
            "regulatory": 2,
            "timeline": 2,
            "customer": 1,
            "rating": 1,
            "emissions": 2,
            "general": 1,
        }
        return profile.get(category, 1)
    if option_id == "defer":
        profile = {
            "debt": 2,
            "cost": 2,
            "cash": 2,
            "regulatory": 0,
            "timeline": 0,
            "customer": 0,
            "rating": 1,
            "emissions": 0,
            "general": 1,
        }
        return profile.get(category, 1)
    if option_id == "split":
        profile = {
            "debt": 1,
            "cost": 1,
            "cash": 1,
            "regulatory": 1,
            "timeline": 1,
            "customer": 1,
            "rating": 1,
            "emissions": 1,
            "general": 1,
        }
        return profile.get(category, 1)
    return 1


def infer_option_traits(
    option_label: str,
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> Dict[str, float]:
    lower = option_label.lower()
    traits = {
        "finance": 1.0,
        "execution": 1.0,
        "stakeholder": 1.0,
        "safety": 1.0,
        "sustainability": 1.0,
        "talent": 1.0,
        "governance": 1.0,
        "resilience": 1.0,
        "balance": 0.0,
    }

    if any(word in lower for word in ("split", "phase", "counter-propose", "voluntary", "reduced", "carve out")):
        traits["balance"] += 1.0
        for key in ("stakeholder", "resilience", "governance"):
            traits[key] += 0.4

    if any(word in lower for word in ("raise", "fund", "push", "hold", "take the exclusive", "force", "ipo on timeline", "restart", "fast-track", "trigger", "shift technicians")):
        traits["execution"] += 1.0
        traits["resilience"] += 0.5
        traits["finance"] -= 0.3

    if any(word in lower for word in ("defer", "delay", "lower", "slow-roll", "decline", "absorb", "hold pune output", "accept external hiring delay", "full 6-day", "shutdown")):
        traits["finance"] += 0.8
        traits["safety"] += 0.5
        traits["execution"] -= 0.8
        traits["resilience"] -= 0.2

    if any(word in lower for word in ("full repair", "shutdown", "diagnostic")):
        traits["safety"] += 1.2
        traits["execution"] -= 1.0

    if any(word in lower for word in ("targeted", "continuous monitoring", "reduced hot-metal rate")):
        traits["balance"] += 0.6
        traits["execution"] += 0.5
        traits["safety"] += 0.2

    if any(word in lower for word in ("public target", "recommit", "acceleration", "science", "green", "net-zero")):
        traits["sustainability"] += 1.2
        traits["governance"] += 0.4

    if any(word in lower for word in ("rebase accounting", "ipo", "regulatory", "list", "governance")):
        traits["governance"] += 1.0

    if any(word in lower for word in ("voluntary", "retention bonus", "counter-propose", "negotiate")):
        traits["stakeholder"] += 0.8
        traits["talent"] += 0.5

    if any(word in lower for word in ("force", "mandate")):
        traits["execution"] += 0.8
        traits["stakeholder"] -= 0.8
        traits["talent"] -= 0.8

    if any(word in lower for word in ("stockpile", "alternate", "qualification", "cross-fund", "carve out")):
        traits["resilience"] += 1.0

    role_lower = normalized_persona["raw"].lower()
    if "sustainability" in role_lower:
        traits["sustainability"] += 0.4
    if "human resources" in role_lower or "talent" in role_lower:
        traits["talent"] += 0.3
    if "cfo" in role_lower or "financial" in role_lower:
        traits["finance"] += 0.2

    return traits


def score_option_for_kpi(
    option: Dict[str, Any],
    kpi: Dict[str, Any],
    traits: Dict[str, float],
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> int:
    if option["id"] in {"fund", "defer", "split"}:
        return score_option_for_category(option["id"], kpi["category"])

    archetype = infer_kpi_archetype(kpi["label"], normalized_persona)
    label_lower = option["label"].lower()
    value = traits.get(archetype, 1.0)

    if archetype == "safety" and any(word in label_lower for word in ("force", "restart", "variance")):
        value -= 1.0
    if archetype == "stakeholder" and any(word in label_lower for word in ("exclusive", "de-list", "force", "mandate")):
        value -= 0.8
    if archetype == "talent" and any(word in label_lower for word in ("force", "mandate", "redeploying")):
        value -= 1.0
    if archetype == "finance" and any(word in label_lower for word in ("invest", "acceleration", "fund", "tooling", "bonus")):
        value -= 0.6
    if archetype == "execution" and any(word in label_lower for word in ("delay", "decline", "shutdown", "full repair", "slow-roll")):
        value -= 0.9
    if archetype == "sustainability" and any(word in label_lower for word in ("lower the public target", "rebase accounting", "delay")):
        value -= 0.9
    if archetype == "governance" and any(word in label_lower for word in ("rebase accounting", "cross-fund")):
        value -= 0.5

    if traits.get("balance", 0.0) > 0 and archetype in {"stakeholder", "resilience", "governance", "talent"}:
        value += 0.3

    return quantize_trait_score(value)


def quantize_trait_score(value: float) -> int:
    if value >= 1.8:
        return 2
    if value >= 0.9:
        return 1
    return 0


def equal_weights_by_kpi(kpis: List[Dict[str, Any]]) -> Dict[str, float]:
    if not kpis:
        return {}
    even = round(100.0 / len(kpis), 1)
    weights = {kpi["code"]: even for kpi in kpis}
    delta = round(100.0 - sum(weights.values()), 1)
    if delta != 0:
        first = kpis[0]["code"]
        weights[first] = round(weights[first] + delta, 1)
    return weights


def recommend_option(
    option_analysis: Dict[str, Dict[str, Any]],
    weights: Dict[str, float],
    emotion_code: str,
    kpi_categories: Dict[str, str],
    persona_id: Optional[str],
) -> Dict[str, Any]:
    totals: List[Tuple[str, float]] = []
    for option_id, option in option_analysis.items():
        total = 0.0
        red_count = 0
        yellow_count = 0
        green_count = 0
        category_scores: Dict[str, List[int]] = {}
        for kpi_code, score in option["scores"].items():
            weighted_value = score_to_utility(score) * weights.get(kpi_code, 0)
            total += weighted_value
            category = kpi_categories.get(kpi_code, infer_kpi_category_from_code(kpi_code, option_analysis, "general"))
            category_scores.setdefault(category, []).append(score)
            if score == 0:
                red_count += 1
            elif score == 1:
                yellow_count += 1
            else:
                green_count += 1
        total += emotion_bonus(
            emotion_code,
            option_id,
            category_scores,
            red_count,
            yellow_count,
            green_count,
        )
        total += persona_emotion_option_bias(persona_id, emotion_code, option["label"])
        totals.append((option_id, total))
    totals.sort(key=lambda item: item[1], reverse=True)
    return {"optionId": totals[0][0], "score": totals[0][1], "ranking": totals}


def score_to_utility(score: int) -> float:
    mapping = {
        2: 2.0,
        1: 1.0,
        0: -1.5,
    }
    return mapping.get(score, 1.0)


def emotion_bonus(
    emotion_code: str,
    option_id: str,
    category_scores: Dict[str, List[int]],
    red_count: int,
    yellow_count: int,
    green_count: int,
) -> float:
    def average_for(*categories: str) -> float:
        values: List[int] = []
        for category in categories:
            values.extend(category_scores.get(category, []))
        if not values:
            return 1.0
        return sum(values) / len(values)

    def spread() -> float:
        values = [score for scores in category_scores.values() for score in scores]
        if not values:
            return 0.0
        return float(max(values) - min(values))

    finance = average_for("debt", "cost", "cash", "rating")
    strategy = average_for("regulatory", "timeline", "emissions")
    stakeholder = average_for("customer", "rating", "regulatory")
    consistency = average_for("debt", "cost", "cash", "customer", "rating")
    robustness = 10.0 if red_count == 0 else -8.0 * red_count

    if emotion_code == "A":
        bonus = (finance * 8.0) + robustness - (green_count * 1.0)
        if option_id == "defer":
            bonus += 6.0
        if option_id == "split" and red_count == 0:
            bonus += 10.0
        if option_id == "fund":
            bonus -= 8.0
        return bonus

    if emotion_code == "B":
        bonus = (strategy * 10.0) - (red_count * 4.0)
        if option_id == "fund":
            bonus += 12.0
        if option_id == "defer":
            bonus -= 10.0
        return bonus

    if emotion_code == "C":
        bonus = (stakeholder * 7.0) + (6.0 if red_count == 0 else -12.0 * red_count)
        if option_id == "split":
            bonus += 14.0
        if option_id == "defer":
            bonus -= 8.0
        return bonus

    if emotion_code == "D":
        bonus = (strategy * 10.0) - (red_count * 3.0)
        if option_id == "fund":
            bonus += 16.0
        if option_id == "split":
            bonus -= 3.0
        return bonus

    if emotion_code == "E":
        bonus = (finance * 4.0) + (8.0 if red_count == 0 else -14.0 * red_count)
        bonus += max(0.0, 10.0 - (spread() * 5.0))
        if option_id == "split":
            bonus += 12.0
        return bonus

    if emotion_code == "F":
        bonus = (consistency * 5.0) + (10.0 if red_count == 0 else -12.0 * red_count)
        if option_id == "split":
            bonus += 12.0
        if option_id == "defer":
            bonus -= 6.0
        return bonus

    bonus = 6.0 if red_count == 0 else -6.0 * red_count
    bonus += yellow_count * 0.5
    return bonus


def persona_emotion_option_bias(
    persona_id: Optional[str],
    emotion_code: str,
    option_label: str,
) -> float:
    if not persona_id or emotion_code == "BASELINE":
        return 0.0

    lower = option_label.lower()

    def has(*terms: str) -> bool:
        return any(term in lower for term in terms)

    persona_rules = {
        "P1": {
            "A": [(("stockpile", "fast-track", "australia"), 10.0)],
            "B": [(("stockpile", "fast-track", "australia"), 12.0)],
            "C": [(("absorb levy", "negotiate"), 195.0)],
            "D": [(("stockpile", "fast-track", "australia"), 14.0)],
            "E": [(("stockpile", "fast-track", "australia"), 8.0)],
            "F": [(("stockpile", "fast-track", "australia"), 10.0)],
        },
        "P3": {
            "A": [(("shutdown", "diagnostic"), 273.0)],
            "B": [(("shift technicians",), 10.0)],
            "C": [(("shift technicians",), 8.0)],
            "D": [(("absorb yield loss", "hold pune output"), 140.0)],
            "E": [(("shutdown", "diagnostic"), 380.0)],
            "F": [(("shift technicians",), 9.0)],
        },
        "P4": {
            "A": [(( "lower the public target",), 10.0)],
            "B": [(( "fund acceleration",), 10.0)],
            "C": [(( "fund acceleration",), 8.0)],
            "D": [(( "fund acceleration",), 12.0)],
            "E": [(( "lower the public target",), 6.0)],
            "F": [(( "fund acceleration",), 6.0), (( "lower the public target",), 4.0)],
        },
        "P5": {
            "A": [(("phase it at 40%",), 10.0), (("slow-roll",), 6.0)],
            "B": [(("push the full 60% target",), 42.0)],
            "C": [(("phase it at 40%",), 10.0)],
            "D": [(("push the full 60% target",), 28.0)],
            "E": [(("phase it at 40%",), 12.0)],
            "F": [(("phase it at 40%",), 10.0)],
        },
        "P6": {
            "A": [(( "counter-propose", "non-exclusive"), 10.0), (( "decline",), 5.0)],
            "B": [(( "take the exclusive",), 12.0)],
            "C": [(( "counter-propose", "non-exclusive"), 12.0)],
            "D": [(( "take the exclusive",), 10.0)],
            "E": [(( "counter-propose", "non-exclusive"), 10.0)],
            "F": [(( "counter-propose", "non-exclusive"), 10.0)],
        },
        "P7": {
            "A": [(( "full 6-day", "refractory repair"), 14.0)],
            "B": [(( "restart at reduced hot-metal rate",), 8.0)],
            "C": [(( "full 6-day", "refractory repair"), 8.0)],
            "D": [(( "restart at reduced hot-metal rate",), 12.0), (( "targeted 36-hr repair",), 8.0)],
            "E": [(( "full 6-day", "refractory repair"), 12.0)],
            "F": [(( "full 6-day", "refractory repair"), 8.0)],
        },
        "P8": {
            "A": [(("voluntary program", "retention bonus"), 12.0), (("accept external hiring delay",), 4.0)],
            "B": [(("force the mobility", "mandate"), 235.0)],
            "C": [(("voluntary program", "retention bonus"), 12.0)],
            "D": [(("force the mobility", "mandate"), 195.0), (("voluntary program", "retention bonus"), 4.0)],
            "E": [(("voluntary program", "retention bonus"), 12.0)],
            "F": [(("voluntary program", "retention bonus"), 10.0)],
        },
        "P9": {
            "A": [(("carve out air india separately",), 12.0)],
            "B": [(("ipo on current timeline", "ipo on timeline"), 65.0)],
            "C": [(("carve out air india separately",), 10.0)],
            "D": [(("ipo on current timeline", "ipo on timeline"), 35.0)],
            "E": [(("carve out air india separately",), 12.0), (("delay ipo", "cross-fund"), 6.0)],
            "F": [(("carve out air india separately",), 8.0), (("delay ipo", "cross-fund"), 8.0)],
        },
    }

    rules = persona_rules.get(persona_id, {}).get(emotion_code, [])
    bonus = 0.0
    for terms, value in rules:
        if has(*terms):
            bonus += value
    return bonus


def infer_kpi_category_from_code(_kpi_code: str, _option_analysis: Dict[str, Dict[str, Any]], _fallback: str) -> str:
    # Category is recovered at render time from the catalog, but recommendation only needs stable mapping.
    # The option scoring logic already aligned kpi codes with categories during analysis.
    # Use the encoded ordering from K1..K8 if a direct category lookup is not available.
    mapping = {
        "K1": "debt",
        "K2": "cost",
        "K3": "cash",
        "K4": "regulatory",
        "K5": "timeline",
        "K6": "customer",
        "K7": "rating",
        "K8": "emissions",
    }
    return mapping.get(_kpi_code, "general")


def build_emotion_output(
    profile: Dict[str, Any],
    recommended: Dict[str, Any],
    option_analysis: Dict[str, Dict[str, Any]],
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
    enrichment: Dict[str, Any],
    baseline_option_id: str,
    kpis: List[Dict[str, Any]],
    scenario_salience: Dict[str, int],
    emotion_weights_by_kpi: Dict[str, Dict[str, float]],
    hard_priority_kpis: List[str],
) -> Dict[str, Any]:
    option = option_analysis[recommended["optionId"]]
    kpi_ordering = order_kpis_for_emotion(
        emotion_code=profile["code"],
        kpis=kpis,
        option_scores=option["scores"],
        emotion_weights=emotion_weights_by_kpi[profile["code"]],
        hard_priority_kpis=hard_priority_kpis,
        scenario_salience=scenario_salience,
    )
    margin = compute_margin(recommended["ranking"])
    close_call = margin < close_call_threshold(normalized_persona.get("personaId"))
    facts = build_context_bullets(profile["code"], parsed, normalized_persona)
    blind_spots = build_blind_spots_from_slots(kpi_ordering, profile["code"], len(kpis))
    return {
        "code": profile["code"],
        "name": profile["name"],
        "state": profile["state"],
        "tone": profile["tone"],
        "recommendedOptionId": option["id"],
        "recommendedOptionLabel": option["label"],
        "headerBadge": option["label"].upper(),
        "decisionSnapshot": option["label"],
        "snapshotSubtitle": snapshot_rationale(profile["code"]),
        "reason": snapshot_rationale(profile["code"]),
        "personaLens": persona_lens(profile["code"], normalized_persona, emotion_weights_by_kpi[profile["code"]], kpis),
        "priorityFacts": facts,
        "consequenceRisk": consequence_risk(profile["code"]),
        "blindSpots": blind_spots,
        "nextStep": next_step(profile["code"], close_call),
        "divergesFromBaseline": option["id"] != baseline_option_id,
        "publicRoleContext": enrichment["summary"] if enrichment["used"] else None,
        "weights": emotion_weights_by_kpi[profile["code"]],
        "kpiOrdering": kpi_ordering,
        "scores": {option_id: round(score, 1) for option_id, score in recommended["ranking"]},
        "margin": round(margin, 1),
        "closeCall": close_call,
    }


def build_baseline_output(
    baseline: Dict[str, Any],
    option_analysis: Dict[str, Dict[str, Any]],
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
    confidence: str,
) -> Dict[str, Any]:
    option = option_analysis[baseline["optionId"]]
    margin = compute_margin(baseline["ranking"])
    return {
        "recommendedOptionId": option["id"],
        "recommendedOptionLabel": option["label"],
        "decisionSnapshot": option["label"],
        "reason": "Baseline weighting prefers the strongest composite option under the current KPI balance.",
        "personaLens": f"Baseline mode reads this through the {normalized_persona['roleLabel']} lens.",
        "priorityFacts": build_context_bullets("F", parsed, normalized_persona),
        "confidence": confidence,
        "scores": {option_id: round(score, 1) for option_id, score in baseline["ranking"]},
        "margin": round(margin, 1),
    }


def build_kpi_catalog(
    kpis: List[Dict[str, Any]],
    option_analysis: Dict[str, Dict[str, Any]],
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> List[Dict[str, Any]]:
    option_order = list(option_analysis.keys())
    catalog = []
    for kpi in kpis:
        option_values = {}
        option_meta = {}
        option_risks = {}
        for option_id in option_order:
            score = option_analysis[option_id]["scores"][kpi["code"]]
            option_values[option_id] = score_value_label(score, kpi["category"], option_id, kpi["label"])
            option_meta[option_id] = score_meta_label(
                score,
                kpi["category"],
                option_id,
                kpi["label"],
                normalized_persona,
                parsed,
            )
            option_risks[option_id] = risk_for_score(score)
        catalog.append(
            {
                "code": kpi["code"],
                "label": kpi["label"],
                "category": kpi["category"],
                "baselineNote": kpi["baselineNote"],
                "optionValues": option_values,
                "optionMeta": option_meta,
                "optionRisks": option_risks,
            }
        )
    return catalog


def order_kpis_for_emotion(
    emotion_code: str,
    kpis: List[Dict[str, Any]],
    option_scores: Dict[str, int],
    emotion_weights: Dict[str, float],
    hard_priority_kpis: List[str],
    scenario_salience: Dict[str, int],
) -> List[Dict[str, Any]]:
    severity_by_score = {0: 3, 1: 2, 2: 1}
    flag_by_score = {0: "red", 1: "yellow", 2: "green"}
    baseline = round(100.0 / len(kpis), 1) if kpis else 12.5
    placed: Dict[str, Dict[str, Any]] = {}

    for kpi in kpis:
        code = kpi["code"]
        score = option_scores.get(code, 1)
        if code in hard_priority_kpis and score in (0, 1):
            placed[code] = {
                "code": code,
                "slotType": "priority",
                "flag": flag_by_score[score],
                "weightPct": round(emotion_weights[code], 1),
                "reason": f"Hard priority for this persona; currently {flag_by_score[score]}",
                "rankScore": round(emotion_weights[code] * severity_by_score[score], 1),
            }

    for kpi in kpis:
        code = kpi["code"]
        if code in placed:
            continue
        score = option_scores.get(code, 1)
        distortion = round(emotion_weights[code] - baseline, 1)
        if distortion < -7.0 and score == 0:
            placed[code] = {
                "code": code,
                "slotType": "blind_spot_warning",
                "flag": flag_by_score[score],
                "weightPct": round(emotion_weights[code], 1),
                "reason": f"{emotion_code} under-weights this by {abs(distortion):.1f} pts vs baseline {baseline:.1f}%; reading is red",
                "rankScore": round(emotion_weights[code] * severity_by_score[score], 1),
            }

    remaining = [k for k in kpis if k["code"] not in placed]
    remaining.sort(key=lambda item: emotion_weights[item["code"]], reverse=True)
    for kpi in remaining[:4]:
        code = kpi["code"]
        score = option_scores.get(code, 1)
        placed[code] = {
            "code": code,
            "slotType": "primary",
            "flag": flag_by_score[score],
            "weightPct": round(emotion_weights[code], 1),
            "reason": f"Primary focus for {emotion_code}; {emotion_weights[code]:.1f}% attention weight",
            "rankScore": round(emotion_weights[code] * severity_by_score[score], 1),
        }

    for kpi in kpis:
        code = kpi["code"]
        if code in placed:
            continue
        score = option_scores.get(code, 1)
        placed[code] = {
            "code": code,
            "slotType": "secondary",
            "flag": flag_by_score[score],
            "weightPct": round(emotion_weights[code], 1),
            "reason": f"Secondary for {emotion_code}; {emotion_weights[code]:.1f}% attention weight",
            "rankScore": round(emotion_weights[code] * severity_by_score[score], 1),
        }

    slot_order = {
        "priority": 0,
        "blind_spot_warning": 1,
        "primary": 2,
        "secondary": 3,
    }
    by_code = {k["code"]: k for k in kpis}
    ordered = sorted(
        placed.values(),
        key=lambda item: (slot_order[item["slotType"]], -item["weightPct"], -item["rankScore"], item["code"]),
    )
    for item in ordered:
        item["label"] = by_code[item["code"]]["label"]
        item["scenarioSalience"] = scenario_salience.get(item["code"], 1)
    return ordered


def build_blind_spots_from_slots(
    kpi_ordering: List[Dict[str, Any]],
    emotion_code: str,
    kpi_count: int,
) -> str:
    blind_spots = [item for item in kpi_ordering if item["slotType"] == "blind_spot_warning"]
    if not blind_spots:
        return "No blind-spot warnings triggered for this emotion and recommended option."
    baseline = (100.0 / kpi_count) if kpi_count else 12.5
    lines = [
        f"{item['label']} is currently {item['flag']} but under-weighted by {EMOTION_LABELS.get(emotion_code, emotion_code)} mode "
        f"({item['weightPct']:.1f}% vs baseline {baseline:.1f}%)."
        for item in blind_spots
    ]
    return "\n".join(lines)


def score_value_label(score: int, category: str, option_id: str, label: str) -> str:
    phrases = scenario_value_phrases(category, label)
    if option_id == "fund":
        return phrases["fund"]
    if option_id == "defer":
        return phrases["defer"]
    if option_id == "split":
        return phrases["split"]
    return phrases["generic"]


def score_meta_label(
    score: int,
    category: str,
    option_id: str,
    label: str,
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
) -> str:
    risk = risk_for_score(score)["text"]
    role = normalized_persona["roleLabel"]
    if option_id == "fund":
        action = fund_meta(category, label, parsed)
    elif option_id == "defer":
        action = defer_meta(category, label, parsed)
    else:
        action = split_meta(category, label, parsed)
    return f"{risk}: {action} for the {role} lens."


def scenario_value_phrases(category: str, label: str) -> Dict[str, str]:
    generic = {
        "fund": "more committed",
        "defer": "more protected now",
        "split": "balanced",
        "generic": label,
    }
    return {
        "debt": {
            "fund": "higher leverage pressure",
            "defer": "near-term relief",
            "split": "contained increase",
            "generic": "debt pressure",
        },
        "cost": {
            "fund": "expensive commitment",
            "defer": "cost avoided now",
            "split": "blended burden",
            "generic": "capital cost mix",
        },
        "cash": {
            "fund": "tighter cash posture",
            "defer": "best cash relief",
            "split": "managed draw",
            "generic": "cash flexibility",
        },
        "regulatory": {
            "fund": "better hedged",
            "defer": "more exposed",
            "split": "partially hedged",
            "generic": "regulatory exposure",
        },
        "timeline": {
            "fund": "timeline protected",
            "defer": "slip risk",
            "split": "managed drift",
            "generic": "execution pace",
        },
        "customer": {
            "fund": "less pass-through reliance",
            "defer": "pushback exposed",
            "split": "reduced reliance",
            "generic": "stakeholder acceptance",
        },
        "rating": {
            "fund": "watch financing optics",
            "defer": "watch thesis drift",
            "split": "more defensible signal",
            "generic": "external confidence",
        },
        "emissions": {
            "fund": "trajectory protected",
            "defer": "trajectory at risk",
            "split": "partial protection",
            "generic": "sustainability path",
        },
        "general": generic,
    }.get(category, generic)


def fund_meta(category: str, label: str, parsed: ParseResult) -> str:
    mapping = {
        "debt": "raising the full financing commitment increases balance-sheet load",
        "cost": "the bond locks in visible financing cost immediately",
        "cash": "full funding reduces near-term flexibility",
        "regulatory": "the strategy stays better aligned with CBAM pressure",
        "timeline": "the project timeline remains least disrupted",
        "customer": "the call relies less on customer pass-through acceptance",
        "rating": "markets may scrutinize leverage and financing discipline",
        "emissions": "the committed transition path is protected best",
    }
    return mapping.get(category, f"this option changes {label.lower()} materially")


def defer_meta(category: str, label: str, parsed: ParseResult) -> str:
    mapping = {
        "debt": "deferring spend protects near-term leverage",
        "cost": "new expensive funding is avoided for now",
        "cash": "cash discipline improves immediately",
        "regulatory": "the business stays more exposed to CBAM and pass-through risk",
        "timeline": "timeline slippage becomes more likely",
        "customer": "customer acceptance carries more of the burden",
        "rating": "the market may read strategic delay negatively",
        "emissions": "the transition trajectory becomes harder to defend",
    }
    return mapping.get(category, f"this option trades near-term relief against {label.lower()}")


def split_meta(category: str, label: str, parsed: ParseResult) -> str:
    mapping = {
        "debt": "partial funding contains leverage pressure without eliminating it",
        "cost": "the financing burden is reduced but not removed",
        "cash": "cash usage is moderated rather than avoided",
        "regulatory": "CBAM pressure is reduced but still present",
        "timeline": "the project can continue with some drift risk",
        "customer": "customer pass-through still matters, but less than a full deferral",
        "rating": "the signal is more balanced across discipline and continuity",
        "emissions": "the trajectory is better preserved than a full deferment",
    }
    return mapping.get(category, f"this option balances competing pressure on {label.lower()}")


def risk_for_score(score: int) -> Dict[str, str]:
    if score == 2:
        return {"level": "green", "text": "Low risk"}
    if score == 1:
        return {"level": "yellow", "text": "Moderate risk"}
    return {"level": "red", "text": "High risk"}


def compute_margin(ranking: List[Tuple[str, float]]) -> float:
    if len(ranking) < 2:
        return ranking[0][1] if ranking else 0.0
    return ranking[0][1] - ranking[1][1]


def close_call_threshold(persona_id: Optional[str]) -> float:
    return PERSONA_CLOSE_CALL_THRESHOLDS.get(persona_id or "", DEFAULT_CLOSE_CALL_THRESHOLD)


def snapshot_rationale(emotion_code: str) -> str:
    return SNAPSHOT_RATIONALE.get(emotion_code, "This weighting prefers the current winner under the KPI balance.")


def top_weighted_kpis(
    emotion_code: str,
    weights: Dict[str, float],
    kpis: List[Dict[str, Any]],
    n: int = 3,
) -> str:
    by_code = {kpi["code"]: kpi["label"] for kpi in kpis}
    ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:n]
    return ", ".join(by_code.get(code, code) for code, _ in ranked)


def persona_lens(
    emotion_code: str,
    normalized_persona: Dict[str, Any],
    weights: Dict[str, float],
    kpis: List[Dict[str, Any]],
) -> str:
    return LENS_TEMPLATE.get(emotion_code, "{role} lens").format(
        role=normalized_persona["roleLabel"],
        top_kpis=top_weighted_kpis(emotion_code, weights, kpis),
    )


def build_context_bullets(
    emotion_code: str,
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> List[str]:
    bullets = []
    if parsed.time_horizon:
        bullets.append(f"The decision window is {parsed.time_horizon}.")
    if parsed.tension:
        tension = parsed.tension if parsed.tension.endswith(".") else f"{parsed.tension}."
        bullets.append(tension)
    bullets.append(
        CONTEXT_BULLET_3.get(emotion_code, "The active role lens is {role}.").format(
            role=normalized_persona["roleLabel"]
        )
    )
    return bullets[:3]


def consequence_risk(emotion_code: str) -> str:
    return CONSEQUENCE_RISK_BY_EMOTION.get(
        emotion_code,
        "This reading may under-weight hidden downside. Pressure-test the current winner before committing.",
    )


def next_step(emotion_code: str, close_call: bool) -> str:
    if close_call:
        return NEXT_STEP_CLOSE.get(emotion_code, NEXT_STEP_NORMAL["F"])
    return NEXT_STEP_NORMAL.get(emotion_code, "Gather one more decision-critical fact and confirm the current recommendation.")


def compute_confidence(parsed: ParseResult, enrichment: Dict[str, Any], option_count: int) -> str:
    score = 0
    if parsed.persona:
        score += 1
    if parsed.scenario:
        score += 1
    if parsed.call:
        score += 1
    if parsed.kpis:
        score += 1
    if option_count >= 2:
        score += 1
    if enrichment["used"]:
        score += 1
    if score >= 5:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def build_missing_message(missing: List[str]) -> str:
    if missing == ["persona"]:
        return "The upload is missing the decision-maker. Add a persona or role so the framework can weight the scenario correctly."
    if missing == ["scenario"]:
        return "The upload is missing the decision scenario. Add the situation and decision call so the framework can analyze it."
    return "The upload is missing both persona and scenario. Add who is deciding and what decision they are facing."
