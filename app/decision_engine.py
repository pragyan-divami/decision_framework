import re
import importlib.util
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .ml_interface import WeightPredictor  # type: ignore
except Exception:  # pragma: no cover
    try:
        from ml_interface import WeightPredictor  # type: ignore
    except Exception:  # pragma: no cover
        WeightPredictor = None


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

# (missed_class, favoured_class, failure_verb) — used to derive data-driven consequence risk copy
EMOTION_FAILURE_MODES: Dict[str, Tuple[str, str, str]] = {
    "A": ("structural fixes", "reversible moves", "deferring the underlying exposure"),
    "B": ("near-term operational KPIs", "long-horizon thesis", "the 90-day path"),
    "C": ("structural KPIs", "stakeholder relationships", "a structurally better answer being blocked"),
    "D": ("qualitative and slow-signal KPIs", "fast-moving KPIs", "committing before all signals are in"),
    "E": ("qualitative inputs", "what the model can quantify", "stakeholder fatigue or reputation risk"),
    "F": ("structurally better options", "balanced outcome", "settling when a stronger path was available"),
}

EMOTION_POSTURE: Dict[str, str] = {
    "A": "concentrates attention on continuity and reversibility",
    "B": "weights structural and long-horizon KPIs",
    "C": "prioritises coordination and stakeholder KPIs",
    "D": "favours fast-feedback execution KPIs",
    "E": "emphasises quantifiable and modelable KPIs",
    "F": "balances immediate outcomes with optionality",
}

EMOTION_NEXT_STEP_ACTIONS: Dict[str, str] = {
    "A": "run one downside stress-test (what breaks at -10%) and confirm before committing",
    "B": "gather one fact about near-term execution risk and confirm the long-game bet",
    "C": "pre-brief the two most affected stakeholders and ask each to pre-commit",
    "D": "set a 72-hour checkpoint on the top two leading indicators; revert to runner-up if either moves wrong",
    "E": "validate the sensitivity of the top-weighted KPI; widen the scenario range if it is high",
    "F": "lock in the move, schedule a 30-day review to escalate or hold",
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


SCENARIO_KPI_SIGNALS: Dict[str, List[str]] = {
    "debt": ["debt", "leverage", "balance sheet", "loan", "bond", "financing", "refinanc", "covenant", "credit", "borrow", "capex", "ebitda"],
    "cost": ["cost", "expense", "capital cost", "rate", "wacc", "pricing", "budget", "fee", "opex", "spend"],
    "cash": ["cash", "liquidity", "working capital", "free cash", "cash flow", "runway", "drawdown", "payment", "tranche"],
    "regulatory": ["regulat", "compliance", "legal", "policy", "permit", "penalty", "fine", "law", "cbam", "levy", "ministry", "audit"],
    "timeline": ["deadline", "timeline", "milestone", "schedule", "delay", "launch", "delivery", "days", "weeks", "months", "quarter", "urgency"],
    "customer": ["customer", "client", "partner", "trust", "relationship", "satisfaction", "churn", "nps", "user", "stakeholder", "pass-through"],
    "rating": ["rating", "reputation", "perception", "confidence", "credibility", "outlook", "review", "signal", "bondholder", "investor"],
    "emissions": ["emission", "carbon", "co2", "co₂", "green", "sustainab", "esg", "net zero", "climate", "scope", "trajectory"],
}

CATEGORY_BASELINE_NOTES: Dict[str, str] = {
    "debt": "Measures how each option affects leverage and covenant headroom.",
    "cost": "Captures the total cost burden each path would impose.",
    "cash": "Assesses near-term liquidity impact and cash draw.",
    "regulatory": "Tracks compliance and policy exposure across each path.",
    "timeline": "Measures how quickly each option delivers observable outcomes.",
    "customer": "Evaluates customer or stakeholder trust and acceptance risk.",
    "rating": "Tracks external confidence and credit or reputation signals.",
    "emissions": "Assesses ESG trajectory and sustainability commitment.",
}

FAMILY_BASELINE_NOTES: Dict[str, str] = {
    "safety_harm": "Tracks direct harm, severity, and immediate downside if the scenario worsens.",
    "financial_impact": "Measures cost, revenue, or economic burden created by each path.",
    "resource_pressure": "Captures liquidity, staffing, or other near-term capacity pressure.",
    "regulatory_legal": "Tracks compliance, disclosure, and legal exposure across options.",
    "urgency_time": "Measures how delay changes the outcome and how quickly action matters.",
    "stakeholder_trust": "Assesses trust, acceptance, and relationship strain among affected groups.",
    "institutional_reputation": "Tracks credibility, reputation, and external confidence risk.",
    "continuity_disruption": "Measures operational, clinical, or service continuity disruption.",
    "evidence_quality": "Captures uncertainty, sufficiency of evidence, and confidence in the signal.",
    "reversibility_optionality": "Measures how reversible the decision is and how much optionality remains.",
    "ethics_disclosure": "Tracks ethical transparency and disclosure integrity.",
    "equity_access": "Assesses affordability, access, and uneven downside across vulnerable groups.",
}

LEGACY_CATEGORY_TO_FAMILY: Dict[str, str] = {
    "debt": "financial_impact",
    "cost": "financial_impact",
    "cash": "resource_pressure",
    "regulatory": "regulatory_legal",
    "timeline": "urgency_time",
    "customer": "stakeholder_trust",
    "rating": "institutional_reputation",
    "emissions": "continuity_disruption",
    "general": "continuity_disruption",
}

FAMILY_TO_LEGACY_CATEGORY: Dict[str, str] = {
    "safety_harm": "regulatory",
    "financial_impact": "cost",
    "resource_pressure": "cash",
    "regulatory_legal": "regulatory",
    "urgency_time": "timeline",
    "stakeholder_trust": "customer",
    "institutional_reputation": "rating",
    "continuity_disruption": "timeline",
    "evidence_quality": "regulatory",
    "reversibility_optionality": "timeline",
    "ethics_disclosure": "regulatory",
    "equity_access": "customer",
}

FAMILY_TO_TRAIT: Dict[str, str] = {
    "safety_harm": "safety",
    "financial_impact": "finance",
    "resource_pressure": "finance",
    "regulatory_legal": "governance",
    "urgency_time": "execution",
    "stakeholder_trust": "stakeholder",
    "institutional_reputation": "stakeholder",
    "continuity_disruption": "resilience",
    "evidence_quality": "governance",
    "reversibility_optionality": "resilience",
    "ethics_disclosure": "governance",
    "equity_access": "stakeholder",
}

EMOTION_FAMILY_WEIGHTS: Dict[str, Dict[str, float]] = {
    "A": {"safety_harm": 18, "financial_impact": 12, "resource_pressure": 12, "regulatory_legal": 10, "urgency_time": 8, "stakeholder_trust": 6, "institutional_reputation": 6, "continuity_disruption": 8, "evidence_quality": 6, "reversibility_optionality": 8, "ethics_disclosure": 4, "equity_access": 2},
    "B": {"safety_harm": 6, "financial_impact": 8, "resource_pressure": 6, "regulatory_legal": 10, "urgency_time": 10, "stakeholder_trust": 8, "institutional_reputation": 12, "continuity_disruption": 10, "evidence_quality": 8, "reversibility_optionality": 10, "ethics_disclosure": 4, "equity_access": 8},
    "C": {"safety_harm": 8, "financial_impact": 6, "resource_pressure": 6, "regulatory_legal": 8, "urgency_time": 8, "stakeholder_trust": 16, "institutional_reputation": 14, "continuity_disruption": 8, "evidence_quality": 6, "reversibility_optionality": 6, "ethics_disclosure": 6, "equity_access": 8},
    "D": {"safety_harm": 8, "financial_impact": 6, "resource_pressure": 6, "regulatory_legal": 10, "urgency_time": 18, "stakeholder_trust": 6, "institutional_reputation": 6, "continuity_disruption": 14, "evidence_quality": 6, "reversibility_optionality": 6, "ethics_disclosure": 4, "equity_access": 4},
    "E": {"safety_harm": 8, "financial_impact": 10, "resource_pressure": 8, "regulatory_legal": 8, "urgency_time": 8, "stakeholder_trust": 6, "institutional_reputation": 6, "continuity_disruption": 8, "evidence_quality": 16, "reversibility_optionality": 8, "ethics_disclosure": 8, "equity_access": 6},
    "F": {"safety_harm": 10, "financial_impact": 10, "resource_pressure": 8, "regulatory_legal": 8, "urgency_time": 10, "stakeholder_trust": 8, "institutional_reputation": 8, "continuity_disruption": 10, "evidence_quality": 6, "reversibility_optionality": 8, "ethics_disclosure": 6, "equity_access": 8},
}

DOMAIN_PACKS: Dict[str, Dict[str, Any]] = {
    "healthcare_safety": {
        "signals": ["medical", "clinical", "patient", "pharmacovigilance", "therapy", "drug", "hospital", "diagnostic", "adverse event"],
        "familyBias": {"safety_harm": 4, "regulatory_legal": 4, "evidence_quality": 3, "ethics_disclosure": 4, "equity_access": 3, "continuity_disruption": 2},
    },
    "finance_balance_sheet": {
        "signals": ["cfo", "debt", "bond", "ebitda", "capex", "rating", "cash flow", "financing"],
        "familyBias": {"financial_impact": 4, "resource_pressure": 3, "institutional_reputation": 2, "regulatory_legal": 1},
    },
    "operations_supply_chain": {
        "signals": ["supply", "stockpile", "plant", "shutdown", "qualification", "supplier", "inventory", "production"],
        "familyBias": {"continuity_disruption": 4, "urgency_time": 3, "resource_pressure": 2, "stakeholder_trust": 1},
    },
    "hr_org_behavior": {
        "signals": ["employee", "talent", "mobility", "attrition", "hiring", "compensation", "org"],
        "familyBias": {"stakeholder_trust": 3, "continuity_disruption": 2, "institutional_reputation": 2, "equity_access": 1},
    },
    "strategy_governance": {
        "signals": ["strategy", "governance", "board", "ipo", "target", "portfolio", "group strategy"],
        "familyBias": {"institutional_reputation": 3, "reversibility_optionality": 3, "regulatory_legal": 2, "financial_impact": 1},
    },
    "ethics_public_trust": {
        "signals": ["ethics", "disclosure", "trust", "public-interest", "transparency", "media", "philanthropic"],
        "familyBias": {"ethics_disclosure": 4, "institutional_reputation": 3, "stakeholder_trust": 3, "equity_access": 2},
    },
}

# (low_score, mid_score, high_score) phrase tiers for custom options
SCORE_VALUE_PHRASES: Dict[str, Tuple[str, str, str]] = {
    "debt": ("leverage strained", "leverage elevated", "leverage contained"),
    "cost": ("cost burden is high", "cost burden is moderate", "cost well managed"),
    "cash": ("cash constrained", "cash under pressure", "cash position solid"),
    "regulatory": ("compliance risk is high", "moderate exposure", "well positioned"),
    "timeline": ("timeline at risk", "timeline stretched", "timeline intact"),
    "customer": ("trust at risk", "relationship strained", "stakeholder aligned"),
    "rating": ("outlook under pressure", "perception mixed", "confidence strong"),
    "emissions": ("trajectory exposed", "partial commitment", "trajectory protected"),
}

SCORE_META_PHRASES: Dict[str, Tuple[str, str, str]] = {
    "debt": (
        "balance-sheet pressure is high on this path",
        "moderate balance-sheet impact across this path",
        "leverage risk is well contained here",
    ),
    "cost": (
        "cost burden is material and will need active management",
        "cost impact is moderate and manageable with monitoring",
        "cost profile is favourable relative to other paths",
    ),
    "cash": (
        "liquidity is constrained — cash headroom needs watching",
        "cash draw is moderate and within expected tolerance",
        "cash position remains healthy on this path",
    ),
    "regulatory": (
        "compliance exposure is significant and should be tracked",
        "regulatory risk is present but manageable",
        "regulatory position is sound on this path",
    ),
    "timeline": (
        "timeline pressure is high — slippage risk is real",
        "some timeline stretch is likely but recoverable",
        "execution timeline is intact on this path",
    ),
    "customer": (
        "stakeholder trust is at risk and needs proactive management",
        "relationship strain is possible — monitor closely",
        "stakeholder alignment is solid on this path",
    ),
    "rating": (
        "external confidence is under pressure",
        "market perception is mixed — signal carefully",
        "rating outlook is stable on this path",
    ),
    "emissions": (
        "sustainability trajectory is in doubt on this path",
        "ESG commitment is partially maintained",
        "emissions trajectory is protected on this path",
    ),
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


@lru_cache(maxsize=1)
def get_ml_predictor():
    if WeightPredictor is None:
        return None
    try:
        predictor = WeightPredictor.load()
    except Exception:
        return None
    return predictor if getattr(predictor, "available", False) else None


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
    domain_pack = classify_domain_pack(parsed, normalized_persona)
    normalized_persona["domainPack"] = domain_pack
    enrichment = maybe_enrich_role(normalized_persona, parsed.enrichment_requested)
    options = extract_options(parsed)
    urgency_profile = classify_urgency_and_bandwidth(parsed, normalized_persona)
    kpis = normalize_kpis(parsed.kpis, parsed.scenario, normalized_persona)
    emotion_weights_by_kpi, ml_metadata = build_emotion_weights_for_persona(
        kpis, normalized_persona, parsed, len(options)
    )
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
                option_analysis,
                urgency_profile,
            )
        )

    confidence = compute_confidence(parsed, enrichment, len(options), ml_metadata)
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
            "nativeKpis": [
                {
                    "code": k["code"],
                    "label": k["label"],
                    "nativeLabel": k.get("nativeLabel", k["label"]),
                    "family": k.get("family"),
                    "unit": k.get("unit"),
                    "nativeScale": k.get("nativeScale"),
                }
                for k in kpis
            ],
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
            "confidenceBreakdown": confidence,
            "analysisMode": "local-role-library" if enrichment["used"] else "scenario-first",
            "scenarioSalience": scenario_salience,
            "hardPriorityKpis": hard_priority_kpis,
            "selectedFamilies": sorted({k.get("family") for k in kpis if k.get("family")}),
            "domainPack": domain_pack,
            "urgency": urgency_profile,
            "ml": ml_metadata,
            "topKpisNow": [item["code"] for item in emotions[0]["kpiOrdering"][: urgency_profile["topKpiCount"]]] if emotions else [],
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
    persona_match = re.search(r"(?m)^\s*\*\*(.+?)\*\*\s*$", markdown_text)
    if persona_match:
        persona = persona_match.group(1).strip()
    persona_label_match = re.search(r"(?im)^persona\s*:\s*(.+)$", markdown_text)
    if persona_label_match:
        persona = persona_label_match.group(1).strip()
    if not persona:
        persona = extract_persona_from_role_section(markdown_text)

    scenario = extract_section(markdown_text, "Scenario")
    scenario_title = extract_scenario_title(markdown_text)
    call = extract_section(markdown_text, "The call")
    if not call:
        call = extract_section(markdown_text, "Option Set")
    tension = extract_section(markdown_text, "Tension")
    if not tension:
        tension = extract_core_tensions(markdown_text)

    time_horizon = extract_table_value(markdown_text, "Time horizon")
    stakeholders_raw = extract_table_value(markdown_text, "Key stakeholders") or ""
    stakeholders = [item.strip() for item in re.split(r";|,", stakeholders_raw) if item.strip()]

    kpi_lines = extract_bullet_section(markdown_text, "KPI families for this scenario")
    option_blocks = extract_option_blocks(markdown_text)
    if option_blocks:
        call = "Should the decision-maker choose " + ", ".join(
            f"{block['code']}. {block['label']}" for block in option_blocks
        ) + "?"
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
        metadata={"optionBlocks": option_blocks},
    )


def extract_scenario_title(markdown_text: str) -> Optional[str]:
    scenario_block = extract_section_block(markdown_text, "Scenario")
    if scenario_block:
        title_match = re.search(r"(?im)^\s*#+\s+(.+?)\s*$", scenario_block)
        if title_match:
            label = title_match.group(1).strip()
            if label.lower() != "scenario":
                return label

    scenario_anchor = re.search(r"(?im)^#+\s+Scenario\s*$", markdown_text)
    if scenario_anchor:
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


def extract_option_blocks(markdown_text: str) -> List[Dict[str, str]]:
    section = extract_section_block(markdown_text, "Options in play") or extract_section_block(markdown_text, "Option Set")
    if not section:
        return []
    pattern = r"(?ms)^##+\s+([A-Z])\s+[—\-·]\s+(.+?)\n+(.*?)(?=^##+\s+[A-Z]\s+[—\-·]\s+|\Z)"
    blocks = []
    for match in re.finditer(pattern, section):
        blocks.append(
            {
                "code": match.group(1).strip(),
                "label": clean_inline(match.group(2)),
                "description": clean_block(match.group(3)),
            }
        )
    return blocks


def extract_section(markdown_text: str, heading: str) -> Optional[str]:
    block = extract_section_block(markdown_text, heading)
    if block is not None:
        cleaned = clean_block(block)
        if cleaned:
            return cleaned
    inline_match = re.search(rf"(?im)^{re.escape(heading)}\s*:\s*(.+)$", markdown_text)
    if inline_match:
        return inline_match.group(1).strip()
    return None


def extract_bullet_section(markdown_text: str, heading: str) -> List[str]:
    block = extract_section_block(markdown_text, heading)
    if not block:
        return []
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


def extract_section_block(markdown_text: str, heading: str) -> Optional[str]:
    heading_match = re.search(rf"(?im)^(\#+)\s+{re.escape(heading)}\s*$", markdown_text)
    if not heading_match:
        return None
    level = len(heading_match.group(1))
    remainder = markdown_text[heading_match.end():]
    lines = remainder.splitlines()
    collected: List[str] = []
    seen_substantive = False

    for line in lines:
        stripped = line.strip()
        heading_line = re.match(r"^(#+)\s+(.+?)\s*$", stripped)
        if heading_line:
            next_level = len(heading_line.group(1))
            heading_text = heading_line.group(2).strip()
            is_option_subheading = heading.lower() == "option set" and bool(re.match(r"^[A-Z]\s+[—\-·]", heading_text))
            if next_level <= level and seen_substantive and not is_option_subheading:
                break
            collected.append(line)
            seen_substantive = True
            continue
        if stripped:
            seen_substantive = True
        collected.append(line)

    block = "\n".join(collected).strip()
    return block or None


def extract_persona_from_role_section(markdown_text: str) -> Optional[str]:
    role_block = extract_section_block(markdown_text, "Role")
    if not role_block:
        return None
    lines = [line.strip() for line in role_block.splitlines() if line.strip() and not re.fullmatch(r"-{3,}", line.strip())]
    if not lines:
        return None
    role_line = clean_inline(lines[0])
    org_line = clean_inline(lines[1]) if len(lines) > 1 else ""
    if role_line and org_line:
        return f"{role_line}, {org_line}"
    return role_line or None


def extract_core_tensions(markdown_text: str) -> Optional[str]:
    block = extract_section_block(markdown_text, "Core internal tensions")
    if not block:
        return None
    tensions = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            tensions.append(clean_inline(re.sub(r"^\-\s+", "", stripped)))
    return "; ".join(tensions) if tensions else clean_block(block)


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


def infer_risk_orientation(lower: str) -> str:
    conservative = ["compliance", "regulatory", "audit", "risk management", "cfo", "finance", "treasury", "governance", "control"]
    growth = ["growth", "ceo", "cto", "founder", "product", "innovation", "startup", "venture", "scale"]
    c = sum(1 for s in conservative if s in lower)
    g = sum(1 for s in growth if s in lower)
    if c > g:
        return "conservative"
    if g > c:
        return "growth_oriented"
    return "moderate"


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
        "riskOrientation": infer_risk_orientation(lower),
        "inferredFields": ["responsibilityScope", "decisionAuthority", "riskOrientation"],
    }


def classify_domain_pack(parsed: "ParseResult", normalized_persona: Dict[str, Any]) -> str:
    combined = " ".join(
        filter(
            None,
            [
                normalized_persona.get("raw"),
                parsed.title,
                parsed.scenario_title,
                parsed.scenario,
                parsed.tension,
                parsed.call,
            ],
        )
    ).lower()
    ranked: List[Tuple[str, int]] = []
    for name, config in DOMAIN_PACKS.items():
        score = sum(1 for signal in config["signals"] if signal in combined)
        ranked.append((name, score))
    ranked.sort(key=lambda item: item[1], reverse=True)
    if ranked and ranked[0][1] > 0:
        return ranked[0][0]
    return "strategy_governance"


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
    option_blocks = parsed.metadata.get("optionBlocks") if parsed.metadata else None
    if option_blocks:
        normalized = []
        seen = set()
        for block in option_blocks:
            label = f"{block['code']}. {block['label']}"
            option_id = option_id_for_text(label.lower())
            if option_id in seen:
                continue
            seen.add(option_id)
            normalized.append(
                {
                    "id": option_id,
                    "label": label,
                    "description": block.get("description", ""),
                    "code": block.get("code"),
                }
            )
        if normalized:
            return normalized

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
        normalized.append({"id": option_id_for_text(lowered), "label": item, "description": ""})
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
            native_fields = parse_native_kpi_fields(label)
            family = native_fields["family"]
            legacy_category = map_family_to_legacy_category(family)
            result.append(
                {
                    "code": code,
                    "label": native_fields["displayLabel"],
                    "nativeLabel": native_fields["nativeLabel"],
                    "category": legacy_category,
                    "family": family,
                    "unit": native_fields["unit"],
                    "nativeScale": native_fields["nativeScale"],
                    "thresholdHints": native_fields["thresholdHints"],
                    "baselineNote": baseline_note_for_kpi(
                        native_fields["displayLabel"],
                        legacy_category,
                        scenario_text,
                        normalized_persona,
                        family=family,
                    ),
                }
            )
        return result
    return derive_kpis_from_context(scenario_text, normalized_persona)


def parse_native_kpi_fields(label: str) -> Dict[str, Any]:
    native_label = label.strip()
    unit = None
    native_scale = "qualitative"
    threshold_hints: List[str] = []
    paren_match = re.search(r"\(([^)]+)\)\s*$", native_label)
    display_label = native_label
    if paren_match:
        unit = clean_inline(paren_match.group(1))
        display_label = native_label[:paren_match.start()].strip()
        native_scale = infer_native_scale(unit)
        threshold_hints = infer_threshold_hints(display_label, unit)
    family = map_native_kpi_to_family(native_label)
    return {
        "displayLabel": display_label,
        "nativeLabel": native_label,
        "unit": unit,
        "nativeScale": native_scale,
        "thresholdHints": threshold_hints,
        "family": family,
    }


def infer_native_scale(unit: str) -> str:
    lower = unit.lower()
    if any(token in lower for token in ("count", "patients", "outlets", "days", "weeks", "months", "hours")):
        return "count_or_duration"
    if any(token in lower for token in ("%", "percent", "per 10,000", "per 1000", "yoy")):
        return "rate_or_percent"
    if any(token in lower for token in ("₹", "$", "€", "cr", "crore", "million", "bn")):
        return "currency"
    if any(token in lower for token in ("1–5", "1-5", "score", "low / medium / high")):
        return "ordinal"
    return "qualitative"


def infer_threshold_hints(label: str, unit: str) -> List[str]:
    hints: List[str] = []
    combined = f"{label} {unit}".lower()
    if "days" in combined or "weeks" in combined or "months" in combined:
        hints.append("time-sensitive")
    if "low / medium / high" in combined:
        hints.append("tiered-risk")
    if "1–5" in combined or "1-5" in combined or "score" in combined:
        hints.append("ordinal-scale")
    if "per 10,000" in combined or "%" in combined:
        hints.append("rate-threshold")
    if any(token in combined for token in ("₹", "$", "€", "cr", "crore", "million")):
        hints.append("financial-threshold")
    return hints


def map_native_kpi_to_family(label: str) -> str:
    lower = label.lower()
    if any(word in lower for word in ("adverse", "harm", "injury", "cardiac", "safety", "severity", "exposed")):
        return "safety_harm"
    if any(word in lower for word in ("cost", "revenue", "gmv", "commercial exposure", "valuation", "margin", "financial")):
        return "financial_impact"
    if any(word in lower for word in ("cash", "liquidity", "headroom", "resource", "burnout", "staffing", "runway")):
        return "resource_pressure"
    if any(word in lower for word in ("regulatory", "legal", "litigation", "liability", "compliance", "exposure level")):
        return "regulatory_legal"
    if any(word in lower for word in ("time", "timeline", "deadline", "urgency", "days", "weeks", "months")):
        return "urgency_time"
    if any(word in lower for word in ("customer", "stakeholder", "trust", "clinician", "relationship", "alignment")):
        return "stakeholder_trust"
    if any(word in lower for word in ("reputation", "reputational", "institutional trust", "confidence", "credibility")):
        return "institutional_reputation"
    if any(word in lower for word in ("continuity", "protocol disruption", "operational disruption", "disruption", "wash-out")):
        return "continuity_disruption"
    if any(word in lower for word in ("evidence", "confidence", "sample size", "uncertainty", "signal")):
        return "evidence_quality"
    if any(word in lower for word in ("reversibility", "optionality", "flexibility", "hybrid", "split")):
        return "reversibility_optionality"
    if any(word in lower for word in ("ethical", "ethics", "disclosure", "transparency", "defensible disclosure")):
        return "ethics_disclosure"
    if any(word in lower for word in ("affordable", "access", "vulnerable", "equity", "alternatives")):
        return "equity_access"
    legacy_category = infer_kpi_category(label)
    return LEGACY_CATEGORY_TO_FAMILY.get(legacy_category, "continuity_disruption")


def map_family_to_legacy_category(family: str) -> str:
    return FAMILY_TO_LEGACY_CATEGORY.get(family, "general")


def infer_kpi_category(label: str) -> str:
    lower = label.lower()
    if any(word in lower for word in ("adverse", "cardiac", "patient exposed", "wash-out", "transition harm", "clinical protocol", "safety")):
        return "regulatory"
    if any(word in lower for word in ("statistical confidence", "evidence sufficiency", "defensible disclosure", "ethical transparency", "litigation", "liability")):
        return "regulatory"
    if any(word in lower for word in ("trust", "reputational", "patient", "affordable alternatives", "clinician")):
        return "customer"
    if any(word in lower for word in ("commercial exposure", "revenue at risk", "₹", "gmv", "revenue")):
        return "cost"
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
    family: Optional[str] = None,
) -> str:
    sentence = scenario_sentence_for_category(scenario_text, category)
    if sentence:
        return sentence
    if family and family in FAMILY_BASELINE_NOTES:
        return FAMILY_BASELINE_NOTES[family]
    return CATEGORY_BASELINE_NOTES.get(
        category,
        f"{label} is a key decision dimension for the {normalized_persona['roleLabel']}.",
    )


def detect_scenario_kpi_domains(scenario_text: str, persona_raw: str) -> Dict[str, int]:
    combined = (scenario_text or "").lower() + " " + persona_raw.lower()
    return {
        category: sum(1 for signal in signals if signal in combined)
        for category, signals in SCENARIO_KPI_SIGNALS.items()
    }


def persona_default_categories(persona_lower: str) -> List[str]:
    if "cfo" in persona_lower or "finance" in persona_lower or "treasury" in persona_lower:
        return ["debt", "cost", "cash", "regulatory", "timeline", "customer", "rating", "emissions"]
    if "administrator" in persona_lower:
        return ["cash", "timeline", "customer", "rating", "regulatory"]
    if "principal" in persona_lower:
        return ["timeline", "customer", "rating", "cash", "regulatory"]
    if "founder" in persona_lower or "ceo" in persona_lower:
        return ["cost", "timeline", "customer", "rating", "cash"]
    if "manager" in persona_lower or "director" in persona_lower:
        return ["timeline", "customer", "cost", "rating", "regulatory"]
    return ["timeline", "customer", "regulatory", "rating", "cost"]


def derive_kpis_from_context(scenario_text: str, normalized_persona: Dict[str, Any]) -> List[Dict[str, Any]]:
    domain_scores = detect_scenario_kpi_domains(scenario_text, normalized_persona["raw"])
    sorted_categories = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
    selected = [cat for cat, score in sorted_categories if score > 0][:8]

    if len(selected) < 4:
        for cat in persona_default_categories(normalized_persona["raw"].lower()):
            if cat not in selected:
                selected.append(cat)
            if len(selected) >= 6:
                break

    seen: set = set()
    result = []
    for idx, category in enumerate(selected, start=1):
        if category in seen:
            continue
        seen.add(category)
        label = fallback_label_for_category(category, normalized_persona)
        family = LEGACY_CATEGORY_TO_FAMILY.get(category, "continuity_disruption")
        result.append(
            {
                "code": f"K{idx}",
                "label": label,
                "nativeLabel": label,
                "category": category,
                "family": family,
                "unit": None,
                "nativeScale": "qualitative",
                "thresholdHints": [],
                "baselineNote": baseline_note_for_kpi(label, category, scenario_text, normalized_persona, family=family),
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
    signals = SCENARIO_KPI_SIGNALS.get(category, ())
    for sentence in sentences:
        lower = sentence.lower()
        if any(signal in lower for signal in signals):
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
        effects = {}
        risks = {}
        traits = infer_option_traits(option["label"], option.get("description", ""), parsed, normalized_persona)
        for kpi in kpis:
            effect = score_option_action_effect(option, kpi, traits, parsed, normalized_persona)
            effects[kpi["code"]] = effect
            scores[kpi["code"]] = action_effect_to_score(effect)
            risks[kpi["code"]] = build_risk_object(effect, kpi, parsed, normalized_persona)
        results[option_id] = {
            "id": option_id,
            "label": option["label"],
            "scores": scores,
            "effects": effects,
            "risks": risks,
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


def classify_urgency_and_bandwidth(parsed: ParseResult, normalized_persona: Dict[str, Any]) -> Dict[str, Any]:
    combined = " ".join(filter(None, [parsed.scenario, parsed.tension, parsed.time_horizon])).lower()
    urgency_score = 1
    if any(token in combined for token in ("today", "immediate", "urgent", "month-end", "11 days", "72-hour")):
        urgency_score += 2
    if any(token in combined for token in ("days", "week", "weeks", "quarter")):
        urgency_score += 1
    bandwidth_score = 3
    if normalized_persona.get("riskOrientation") == "conservative":
        bandwidth_score -= 1
    if urgency_score >= 4:
        level = "immediate"
        top_kpis = 3
        max_options = 2
    elif urgency_score == 3:
        level = "moderate"
        top_kpis = 5
        max_options = 3
    else:
        level = "analytical"
        top_kpis = 8
        max_options = 4
    return {
        "level": level,
        "urgencyScore": urgency_score,
        "bandwidthScore": bandwidth_score,
        "topKpiCount": top_kpis,
        "maxOptionsToShow": max_options,
    }


def blend_weight_rows(
    rule_rows: Dict[str, Dict[str, float]],
    ml_rows: Dict[str, Dict[str, float]],
    ml_confidence: float,
) -> Dict[str, Dict[str, float]]:
    if not ml_rows:
        return rule_rows
    ratio = max(0.15, min(0.45, round(ml_confidence * 0.4, 2)))
    blended: Dict[str, Dict[str, float]] = {}
    for emotion_code, rule_row in rule_rows.items():
        ml_row = ml_rows.get(emotion_code, {})
        merged: Dict[str, float] = {}
        for code, value in rule_row.items():
            merged[code] = ((1.0 - ratio) * value) + (ratio * ml_row.get(code, value))
        blended[emotion_code] = normalize_weight_row(merged)
    return blended


def build_emotion_weights_for_persona(
    kpis: List[Dict[str, Any]],
    normalized_persona: Dict[str, Any],
    parsed: Optional["ParseResult"] = None,
    option_count: int = 3,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
    persona_id = normalized_persona.get("personaId")
    reference_personas = load_reference_personas()
    ml_metadata = {
        "used": False,
        "mode": "rules-only",
        "weightConfidence": 0.0,
        "optionConfidence": 0.0,
        "summary": "ML advisory layer unavailable",
    }
    if persona_id and persona_id in reference_personas:
        reference = reference_personas[persona_id]
        rows: Dict[str, Dict[str, float]] = {}
        for emotion_code, row in reference.emotion_weights.items():
            rows[emotion_code] = {
                kpi["code"]: float(row.get(kpi["code"], 100.0 / max(1, len(kpis))))
                for kpi in kpis
            }
        predictor = get_ml_predictor()
        if predictor is not None:
            ml_rows = predictor.predict_weights(normalized_persona, kpis, option_count)
            rows = blend_weight_rows(rows, ml_rows, predictor.weight_confidence())
            ml_metadata = {
                "used": True,
                "mode": "reference-plus-ml-blend",
                "weightConfidence": round(predictor.weight_confidence(), 3),
                "optionConfidence": round(predictor.option_confidence(), 3),
                "summary": predictor.summary(),
            }
        return rows, ml_metadata

    rows: Dict[str, Dict[str, float]] = {}
    role_bias = role_family_bias(normalized_persona)
    orient_bias = risk_orientation_bias(normalized_persona.get("riskOrientation", "moderate"))
    tension_bias = scenario_tension_family_bias(
        parsed.tension if parsed else None,
        parsed.time_horizon if parsed else None,
    )
    domain_bias = DOMAIN_PACKS.get(normalized_persona.get("domainPack", ""), {}).get("familyBias", {})
    combined_bias: Dict[str, int] = {}
    for source in (role_bias, orient_bias, tension_bias, domain_bias):
        for k, v in source.items():
            combined_bias[k] = combined_bias.get(k, 0) + v

    for emotion_code, profile in EMOTION_FAMILY_WEIGHTS.items():
        raw = {}
        for kpi in kpis:
            family = kpi.get("family", LEGACY_CATEGORY_TO_FAMILY.get(kpi.get("category", "general"), "continuity_disruption"))
            raw[kpi["code"]] = float(profile.get(family, 8) + combined_bias.get(family, 0))
        rows[emotion_code] = normalize_weight_row(raw)
    predictor = get_ml_predictor()
    if predictor is not None:
        ml_rows = predictor.predict_weights(normalized_persona, kpis, option_count)
        rows = blend_weight_rows(rows, ml_rows, predictor.weight_confidence())
        ml_metadata = {
            "used": True,
            "mode": "rules-plus-ml-blend",
            "weightConfidence": round(predictor.weight_confidence(), 3),
            "optionConfidence": round(predictor.option_confidence(), 3),
            "summary": predictor.summary(),
        }
    return rows, ml_metadata


def risk_orientation_bias(orientation: str) -> Dict[str, int]:
    if orientation == "conservative":
        return {"financial_impact": 2, "safety_harm": 3, "regulatory_legal": 2, "reversibility_optionality": 2, "urgency_time": -1}
    if orientation == "growth_oriented":
        return {"urgency_time": 2, "continuity_disruption": 2, "reversibility_optionality": 1, "financial_impact": -1, "safety_harm": -1}
    return {}


def scenario_tension_family_bias(tension: Optional[str], time_horizon: Optional[str]) -> Dict[str, int]:
    bias: Dict[str, int] = {}
    if tension:
        lower = tension.lower()
        if any(w in lower for w in ("deadline", "urgency", "immediate", "now", "today", "month-end")):
            bias["urgency_time"] = bias.get("urgency_time", 0) + 2
        if any(w in lower for w in ("compliance", "regulatory", "penalty", "fine", "legal")):
            bias["regulatory_legal"] = bias.get("regulatory_legal", 0) + 2
        if any(w in lower for w in ("customer", "client", "relationship", "trust")):
            bias["stakeholder_trust"] = bias.get("stakeholder_trust", 0) + 2
        if any(w in lower for w in ("cost", "budget", "financial", "cash", "debt")):
            bias["financial_impact"] = bias.get("financial_impact", 0) + 2
            bias["resource_pressure"] = bias.get("resource_pressure", 0) + 1
        if any(w in lower for w in ("safety", "accident", "injury", "harm", "adverse")):
            bias["safety_harm"] = bias.get("safety_harm", 0) + 2
        if any(w in lower for w in ("disclosure", "ethical", "ethics", "transparency")):
            bias["ethics_disclosure"] = bias.get("ethics_disclosure", 0) + 2
        if any(w in lower for w in ("access", "affordable", "equity", "vulnerable")):
            bias["equity_access"] = bias.get("equity_access", 0) + 2
    if time_horizon:
        if any(w in time_horizon.lower() for w in ("week", "days", "30", "60", "90")):
            bias["urgency_time"] = bias.get("urgency_time", 0) + 1
    return bias


def role_family_bias(normalized_persona: Dict[str, Any]) -> Dict[str, int]:
    role_lower = normalized_persona["raw"].lower()
    if any(term in role_lower for term in ("medical", "clinical", "ethics", "pharmacovigilance", "healthcare")):
        return {"safety_harm": 5, "regulatory_legal": 4, "evidence_quality": 3, "ethics_disclosure": 4, "equity_access": 2, "stakeholder_trust": 2}
    if "procurement" in role_lower or "sales" in role_lower:
        return {"stakeholder_trust": 3, "continuity_disruption": 3, "financial_impact": 1}
    if "cfo" in role_lower or "financial" in role_lower:
        return {"financial_impact": 5, "resource_pressure": 3, "institutional_reputation": 2, "regulatory_legal": 2}
    if "operating officer" in role_lower or "plant head" in role_lower:
        return {"urgency_time": 4, "continuity_disruption": 5, "safety_harm": 4, "resource_pressure": 2}
    if "sustainability" in role_lower:
        return {"institutional_reputation": 2, "regulatory_legal": 2, "continuity_disruption": 3, "reversibility_optionality": 2}
    if "delivery" in role_lower or "platform" in role_lower:
        return {"continuity_disruption": 4, "urgency_time": 4, "financial_impact": 2, "stakeholder_trust": 1}
    if "human resources" in role_lower or "talent" in role_lower:
        return {"stakeholder_trust": 4, "continuity_disruption": 2, "institutional_reputation": 2, "equity_access": 2}
    return {"financial_impact": 1, "urgency_time": 1, "stakeholder_trust": 1, "safety_harm": 1, "regulatory_legal": 1, "continuity_disruption": 1}


def infer_kpi_archetype(label: str, normalized_persona: Dict[str, Any]) -> str:
    lower = label.lower()
    if any(word in lower for word in ("cash", "cost", "margin", "gmv", "valuation", "debt", "ebitda", "billing", "roi", "payback", "dividend")):
        return "finance"
    if any(word in lower for word in ("adverse", "cardiac", "patient exposed", "wash-out", "transition harm", "clinical protocol", "safety", "harm")):
        return "safety"
    if any(word in lower for word in ("patient", "affordable alternatives", "trust", "reputational", "clinicians", "media ecosystem", "access")):
        return "stakeholder"
    if any(word in lower for word in ("statistical confidence", "evidence sufficiency", "defensible disclosure", "ethical transparency", "regulatory", "litigation", "liability", "pharmacovigilance")):
        return "governance"
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
    if any(term in normalized_persona["raw"].lower() for term in ("medical", "clinical", "ethics")):
        return "governance"
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
    elif any(term in role_lower for term in ("medical", "clinical", "ethics", "pharmacovigilance")):
        target_tokens = ["adverse", "wash-out", "disclosure", "ethical", "regulatory", "liability", "patient"]
        target_categories = ["regulatory", "customer"]

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
    option_description: str,
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> Dict[str, float]:
    lower = f"{option_label} {option_description}".lower()
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

    if any(word in lower for word in ("suspend", "pull the drug", "transition protocol")):
        traits["safety"] += 1.2
        traits["governance"] += 0.8
        traits["stakeholder"] -= 0.4
        traits["finance"] -= 0.6
        traits["resilience"] -= 0.4

    if any(word in lower for word in ("enhanced monitoring", "screening", "independent 25,000-patient study", "continue with enhanced monitoring")):
        traits["execution"] += 0.4
        traits["stakeholder"] += 0.2
        traits["safety"] -= 0.5
        traits["governance"] -= 0.2

    if any(word in lower for word in ("restrict new starts", "existing patients continue", "maintaining existing patients")):
        traits["balance"] += 0.8
        traits["safety"] += 0.2
        traits["stakeholder"] += 0.3
        traits["governance"] -= 0.5

    if any(word in lower for word in ("escalate urgently", "joint review", "cdsco", "expedited safety report", "regulator")):
        traits["governance"] += 1.2
        traits["stakeholder"] += 0.5
        traits["execution"] += 0.2
        traits["finance"] -= 0.2

    if any(word in lower for word in ("quietly", "no public disclosure")):
        traits["governance"] -= 1.0
        traits["stakeholder"] -= 0.8

    if any(word in lower for word in ("disclose the signal", "full-disclosure", "notify regulator proactively")):
        traits["governance"] += 0.8
        traits["stakeholder"] += 0.4

    role_lower = normalized_persona["raw"].lower()
    if "sustainability" in role_lower:
        traits["sustainability"] += 0.4
    if "human resources" in role_lower or "talent" in role_lower:
        traits["talent"] += 0.3
    if "cfo" in role_lower or "financial" in role_lower:
        traits["finance"] += 0.2
    if any(term in role_lower for term in ("medical", "clinical", "ethics", "pharmacovigilance")):
        traits["safety"] += 0.3
        traits["governance"] += 0.3

    return traits


def score_option_action_effect(
    option: Dict[str, Any],
    kpi: Dict[str, Any],
    traits: Dict[str, float],
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> float:
    special_case_effect = score_special_case_option_effect(option, kpi, parsed, normalized_persona)
    if special_case_effect is not None:
        return special_case_effect

    if option["id"] in {"fund", "defer", "split"}:
        return legacy_score_to_action_effect(float(score_option_for_category(option["id"], kpi["category"])))

    family = kpi.get("family", LEGACY_CATEGORY_TO_FAMILY.get(kpi.get("category", "general"), "continuity_disruption"))
    archetype = FAMILY_TO_TRAIT.get(family, infer_kpi_archetype(kpi["label"], normalized_persona))
    label_lower = option["label"].lower()
    value = (traits.get(archetype, 1.0) - 1.0) * 2.0

    if family == "safety_harm" and any(word in label_lower for word in ("force", "restart", "variance")):
        value -= 1.0
    if family in {"stakeholder_trust", "institutional_reputation"} and any(word in label_lower for word in ("exclusive", "de-list", "force", "mandate")):
        value -= 0.8
    if archetype == "talent" and any(word in label_lower for word in ("force", "mandate", "redeploying")):
        value -= 1.0
    if family in {"financial_impact", "resource_pressure"} and any(word in label_lower for word in ("invest", "acceleration", "fund", "tooling", "bonus")):
        value -= 0.6
    if family in {"urgency_time", "continuity_disruption"} and any(word in label_lower for word in ("delay", "decline", "shutdown", "full repair", "slow-roll")):
        value -= 0.9
    if family == "continuity_disruption" and any(word in label_lower for word in ("lower the public target", "rebase accounting", "delay")):
        value -= 0.9
    if family in {"regulatory_legal", "ethics_disclosure", "evidence_quality"} and any(word in label_lower for word in ("rebase accounting", "cross-fund")):
        value -= 0.5

    if traits.get("balance", 0.0) > 0 and family in {"stakeholder_trust", "continuity_disruption", "regulatory_legal", "reversibility_optionality", "equity_access"}:
        value += 0.3

    if normalized_persona.get("domainPack") == "healthcare_safety":
        if family in {"ethics_disclosure", "regulatory_legal"} and any(word in label_lower for word in ("disclose", "escalate", "notify", "review")):
            value += 0.3
        if family == "equity_access" and any(word in label_lower for word in ("suspend", "pull the drug")):
            value -= 0.4

    return clip_action_effect(value)


def score_special_case_option_effect(
    option: Dict[str, Any],
    kpi: Dict[str, Any],
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> Optional[float]:
    role_lower = normalized_persona["raw"].lower()
    scenario_lower = (parsed.scenario or "").lower()
    if not any(term in role_lower for term in ("medical", "clinical", "ethics", "pharmacovigilance")):
        return None
    if not any(term in scenario_lower for term in ("monoclonal", "adverse event", "pharmacovigilance", "cdsco", "wash-out")):
        return None

    option_text = f"{option['label']} {option.get('description', '')}".lower()
    label = kpi["label"].lower()

    if "suspend" in option_text or "pull the drug" in option_text:
        mode = "suspend"
    elif "enhanced monitoring" in option_text or "screening" in option_text:
        mode = "monitor"
    elif "restrict new starts" in option_text or "existing patients continue" in option_text:
        mode = "restrict"
    elif "cdsco" in option_text or "joint review" in option_text or "expedited safety report" in option_text:
        mode = "escalate"
    else:
        return None

    score_map = {
        "suspend": {
            "adverse cardiac event signal": 2.0,
            "statistical confidence / evidence sufficiency": 0.8,
            "active patients exposed": 2.0,
            "vulnerable patients without affordable alternatives": 0.0,
            "wash-out transition harm risk": 0.2,
            "time to defensible disclosure": 2.0,
            "regulatory exposure level": 1.6,
            "ethical transparency integrity": 2.0,
            "institutional trust / reputational downside": 1.3,
            "commercial exposure": 0.0,
            "clinical protocol disruption severity": 0.2,
            "litigation / liability exposure": 1.4,
        },
        "monitor": {
            "adverse cardiac event signal": 0.2,
            "statistical confidence / evidence sufficiency": 1.6,
            "active patients exposed": 0.0,
            "vulnerable patients without affordable alternatives": 2.0,
            "wash-out transition harm risk": 2.0,
            "time to defensible disclosure": 1.2,
            "regulatory exposure level": 0.6,
            "ethical transparency integrity": 1.1,
            "institutional trust / reputational downside": 0.7,
            "commercial exposure": 2.0,
            "clinical protocol disruption severity": 2.0,
            "litigation / liability exposure": 0.2,
        },
        "restrict": {
            "adverse cardiac event signal": 1.2,
            "statistical confidence / evidence sufficiency": 1.4,
            "active patients exposed": 1.0,
            "vulnerable patients without affordable alternatives": 1.5,
            "wash-out transition harm risk": 1.8,
            "time to defensible disclosure": 0.8,
            "regulatory exposure level": 0.7,
            "ethical transparency integrity": 0.2,
            "institutional trust / reputational downside": 0.4,
            "commercial exposure": 1.3,
            "clinical protocol disruption severity": 1.5,
            "litigation / liability exposure": 0.4,
        },
        "escalate": {
            "adverse cardiac event signal": 1.4,
            "statistical confidence / evidence sufficiency": 1.8,
            "active patients exposed": 1.0,
            "vulnerable patients without affordable alternatives": 1.4,
            "wash-out transition harm risk": 1.2,
            "time to defensible disclosure": 1.9,
            "regulatory exposure level": 2.0,
            "ethical transparency integrity": 1.8,
            "institutional trust / reputational downside": 1.6,
            "commercial exposure": 1.0,
            "clinical protocol disruption severity": 1.0,
            "litigation / liability exposure": 1.7,
        },
    }

    for key, value in score_map[mode].items():
        if key in label:
            return legacy_score_to_action_effect(value)
    return None


def clip_action_effect(value: float) -> float:
    return max(-2.0, min(2.0, value))


def action_effect_to_score(effect: float) -> float:
    return max(0.0, min(2.0, round((effect + 2.0) / 2.0, 2)))


def legacy_score_to_action_effect(score: float) -> float:
    return clip_action_effect((score - 1.0) * 2.0)


def flag_for_score(score: float) -> str:
    if score < 0.5:
        return "red"
    if score < 1.5:
        return "yellow"
    return "green"


def severity_for_score(score: float) -> float:
    return max(1.0, 3.0 - score)


def build_risk_object(
    action_effect: float,
    kpi: Dict[str, Any],
    parsed: ParseResult,
    normalized_persona: Dict[str, Any],
) -> Dict[str, Any]:
    family = kpi.get("family", "continuity_disruption")
    combined = " ".join(filter(None, [parsed.scenario, parsed.tension, parsed.time_horizon])).lower()
    downside = max(0.0, -action_effect)

    probability = 2.0 + downside
    if any(token in combined for token in ("uncertain", "not yet", "signal", "reviewing", "confidence")) and family in {"evidence_quality", "regulatory_legal", "safety_harm"}:
        probability += 0.5

    impact_defaults = {
        "safety_harm": 5.0,
        "financial_impact": 3.0,
        "resource_pressure": 3.0,
        "regulatory_legal": 4.0,
        "urgency_time": 3.0,
        "stakeholder_trust": 4.0,
        "institutional_reputation": 4.0,
        "continuity_disruption": 4.0,
        "evidence_quality": 3.0,
        "reversibility_optionality": 4.0,
        "ethics_disclosure": 5.0,
        "equity_access": 4.0,
    }
    impact = impact_defaults.get(family, 3.0) + (1.0 if downside >= 1.0 else 0.0)

    exposure = 2.5
    if re.search(r"\b\d[\d,\.]*\b", combined):
        exposure += 1.0
    if family in {"stakeholder_trust", "institutional_reputation", "equity_access", "safety_harm"}:
        exposure += 0.5

    irreversibility_defaults = {
        "safety_harm": 5.0,
        "financial_impact": 3.0,
        "resource_pressure": 3.0,
        "regulatory_legal": 4.0,
        "urgency_time": 3.0,
        "stakeholder_trust": 4.0,
        "institutional_reputation": 4.0,
        "continuity_disruption": 4.0,
        "evidence_quality": 3.0,
        "reversibility_optionality": 5.0,
        "ethics_disclosure": 4.0,
        "equity_access": 4.0,
    }
    irreversibility = irreversibility_defaults.get(family, 3.0)

    time_pressure = 2.0
    if any(token in combined for token in ("11 days", "days", "weeks", "quarter", "month-end", "urgent", "immediate")):
        time_pressure += 2.0
    elif any(token in combined for token in ("months", "year", "years")):
        time_pressure += 1.0

    uncertainty_penalty = 0.0
    if family in {"evidence_quality", "regulatory_legal", "safety_harm", "ethics_disclosure"} and any(
        token in combined for token in ("not yet statistically significant", "not yet", "uncertain", "private confidence", "not publishable")
    ):
        uncertainty_penalty += 8.0
    if family in {"institutional_reputation", "ethics_disclosure"} and any(token in combined for token in ("media", "leak", "misrepresentation")):
        uncertainty_penalty += 6.0

    base = probability * impact * exposure * irreversibility * time_pressure
    normalized = min(100.0, round((base / 31.25), 1))
    risk_score = min(100.0, round(normalized + uncertainty_penalty, 1))
    return {
        "probability": round(min(probability, 5.0), 1),
        "impact": round(min(impact, 5.0), 1),
        "exposure": round(min(exposure, 5.0), 1),
        "irreversibility": round(min(irreversibility, 5.0), 1),
        "timePressure": round(min(time_pressure, 5.0), 1),
        "uncertaintyPenalty": round(uncertainty_penalty, 1),
        "riskScore": risk_score,
        "band": risk_band_for_value(risk_score),
        "level": risk_level_for_value(risk_score),
        "text": risk_text_for_value(risk_score),
    }


def risk_band_for_value(value: float) -> str:
    if value <= 20:
        return "Low"
    if value <= 40:
        return "Moderate"
    if value <= 60:
        return "High"
    if value <= 80:
        return "Very High"
    return "Critical"


def risk_level_for_value(value: float) -> str:
    if value <= 20:
        return "green"
    if value <= 60:
        return "yellow"
    return "red"


def risk_text_for_value(value: float) -> str:
    return f"{risk_band_for_value(value)} risk"


def risk_penalty_for_object(risk: Dict[str, Any], emotion_code: str) -> float:
    sensitivity = {
        "BASELINE": 0.10,
        "A": 0.18,
        "B": 0.10,
        "C": 0.12,
        "D": 0.11,
        "E": 0.14,
        "F": 0.12,
    }.get(emotion_code, 0.10)
    return round((risk.get("riskScore", 0.0) / 10.0) * sensitivity, 2)


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
            effect = option["effects"][kpi_code]
            risk = option["risks"][kpi_code]
            weighted_value = effect * weights.get(kpi_code, 0)
            total += weighted_value
            total -= risk_penalty_for_object(risk, emotion_code)
            category = kpi_categories.get(kpi_code, infer_kpi_category_from_code(kpi_code, option_analysis, "general"))
            category_scores.setdefault(category, []).append(score)
            if score == 0:
                red_count += 1
            elif score == 1:
                yellow_count += 1
            else:
                green_count += 1
        totals.append((option_id, total))
    totals.sort(key=lambda item: item[1], reverse=True)
    return {"optionId": totals[0][0], "score": totals[0][1], "ranking": totals}


def score_to_utility(score: float) -> float:
    if score <= 0.0:
        return -1.5
    if score <= 1.0:
        return -1.5 + score * 2.5
    return 1.0 + (score - 1.0)


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


def compute_kpi_contributions(
    option: Dict[str, Any],
    kpis: List[Dict[str, Any]],
    weights: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Per-KPI weighted contributions for one option, sorted by contribution descending."""
    kpi_by_code = {kpi["code"]: kpi for kpi in kpis}
    contributions = []
    for kpi_code, score in option["scores"].items():
        kpi = kpi_by_code.get(kpi_code, {})
        weight = weights.get(kpi_code, 0.0)
        effect = option["effects"].get(kpi_code, legacy_score_to_action_effect(score))
        risk = option["risks"].get(kpi_code, risk_for_score(score))
        contrib = effect * weight
        contributions.append({
            "kpi_code": kpi_code,
            "kpi_label": kpi.get("label", kpi_code),
            "category": kpi.get("category", "general"),
            "family": kpi.get("family"),
            "effect": round(effect, 2),
            "score": score,
            "weight": weight,
            "contribution": round(contrib, 2),
            "flag": risk.get("level", "yellow"),
        })
    return sorted(contributions, key=lambda c: c["contribution"], reverse=True)


def derive_snapshot_subtitle(
    emotion_code: str,
    winner_label: str,
    runner_up_label: str,
    margin: float,
    top_drivers: List[Dict[str, Any]],
) -> str:
    emotion_name = EMOTION_LABELS.get(emotion_code, emotion_code)
    driver_names = [d["kpi_label"] for d in top_drivers[:2]]
    driver_str = " and ".join(driver_names) if driver_names else "the top-weighted KPIs"
    if margin < 5:
        return (
            f"{emotion_name} weighting narrowly prefers this over \"{runner_up_label}\" "
            f"(margin of {margin:.1f} pts). The tilt comes from {driver_str}."
        )
    return (
        f"{emotion_name} weighting prefers this option by {margin:.1f} pts over "
        f"\"{runner_up_label}\". Driven primarily by {driver_str}."
    )


def explain_divergence(
    emotion_code: str,
    recommended_label: str,
    baseline_label: str,
    top_drivers: List[Dict[str, Any]],
) -> str:
    if recommended_label == baseline_label:
        return "This emotion converges with baseline. The lens changes which KPIs dominate the explanation, not the winner."
    driver_labels = ", ".join(item["kpi_label"] for item in top_drivers[:3]) or "the top weighted KPIs"
    emotion_name = EMOTION_LABELS.get(emotion_code, emotion_code)
    return (
        f"{emotion_name} diverges from baseline because it gives more decision weight to {driver_labels}. "
        f"This is a useful lens if those KPIs are truly dominant; it is a risky bias if they crowd out slower but higher-downside signals."
    )


def derive_flip_condition(
    parsed: ParseResult,
    recommended_label: str,
    runner_up_label: str,
    top_drivers: List[Dict[str, Any]],
) -> str:
    top_driver = top_drivers[0]["kpi_label"] if top_drivers else "the top KPI"
    if parsed.time_horizon and any(token in parsed.time_horizon.lower() for token in ("day", "week", "month")):
        return (
            f"If new evidence changes {top_driver} materially inside the current decision window, "
            f"the recommendation can flip from \"{recommended_label}\" to \"{runner_up_label}\"."
        )
    return (
        f"Watch {top_driver}. If it moves against the current assumptions or reversibility drops faster than expected, "
        f"re-test \"{runner_up_label}\" as the stronger path."
    )


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
    full_option_analysis: Dict[str, Dict[str, Any]],
    urgency_profile: Dict[str, Any],
) -> Dict[str, Any]:
    option = option_analysis[recommended["optionId"]]
    kpi_ordering = order_kpis_for_emotion(
        emotion_code=profile["code"],
        kpis=kpis,
        option_scores=option["scores"],
        option_analysis=full_option_analysis,
        normalized_persona=normalized_persona,
        parsed=parsed,
        emotion_weights=emotion_weights_by_kpi[profile["code"]],
        hard_priority_kpis=hard_priority_kpis,
        scenario_salience=scenario_salience,
        top_kpi_count=urgency_profile["topKpiCount"],
    )
    emotion_weights = emotion_weights_by_kpi[profile["code"]]
    margin = compute_margin(recommended["ranking"])
    close_call = margin < close_call_threshold(normalized_persona.get("personaId"))

    winner_contributions = compute_kpi_contributions(option, kpis, emotion_weights)
    top_drivers = winner_contributions[:3]

    ranking = recommended["ranking"]
    runner_up_label = option_analysis[ranking[1][0]]["label"] if len(ranking) > 1 else option["label"]

    facts = build_context_bullets(profile["code"], parsed, normalized_persona)
    blind_spot_items = [item for item in kpi_ordering if item["slotType"] == "blind_spot_warning"]
    blind_spots = build_blind_spots_from_slots(kpi_ordering, profile["code"], len(kpis))
    blind_spot_labels = [item["label"] for item in blind_spot_items]

    return {
        "code": profile["code"],
        "name": profile["name"],
        "state": profile["state"],
        "tone": profile["tone"],
        "recommendedOptionId": option["id"],
        "recommendedOptionLabel": option["label"],
        "headerBadge": option["label"].upper(),
        "decisionSnapshot": option["label"],
        "snapshotSubtitle": derive_snapshot_subtitle(
            profile["code"], option["label"], runner_up_label, margin, top_drivers
        ),
        "reason": derive_snapshot_subtitle(
            profile["code"], option["label"], runner_up_label, margin, top_drivers
        ),
        "personaLens": persona_lens(profile["code"], normalized_persona, emotion_weights, kpis, top_drivers),
        "priorityFacts": facts,
        "consequenceRisk": consequence_risk(
            profile["code"], parsed, option["label"], blind_spot_labels,
            winner_contributions, emotion_weights,
        ),
        "blindSpots": blind_spots,
        "divergenceExplanation": explain_divergence(
            profile["code"], option["label"], option_analysis[baseline_option_id]["label"], top_drivers
        ),
        "flipCondition": derive_flip_condition(parsed, option["label"], runner_up_label, top_drivers),
        "nextStep": next_step(
            profile["code"], close_call, parsed, option["label"],
            runner_up_label=runner_up_label,
            margin=margin,
            blind_spot_items=blind_spot_items,
            top_drivers=top_drivers,
        ),
        "divergesFromBaseline": option["id"] != baseline_option_id,
        "publicRoleContext": enrichment["summary"] if enrichment["used"] else None,
        "weights": emotion_weights,
        "kpiOrdering": kpi_ordering,
        "scores": {option_id: round(score, 1) for option_id, score in ranking},
        "margin": round(margin, 1),
        "closeCall": close_call,
    }


def build_baseline_output(
    baseline: Dict[str, Any],
    option_analysis: Dict[str, Dict[str, Any]],
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
    confidence: Dict[str, str],
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
        "confidence": confidence.get("overall", "Medium"),
        "confidenceBreakdown": confidence,
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
            risk = option_analysis[option_id]["risks"][kpi["code"]]
            option_values[option_id] = score_value_label(score, kpi["category"], option_id, kpi["label"])
            option_meta[option_id] = score_meta_label(
                score,
                kpi["category"],
                option_id,
                kpi["label"],
                normalized_persona,
                parsed,
                risk,
            )
            option_risks[option_id] = risk
        catalog.append(
            {
                "code": kpi["code"],
                "label": kpi["label"],
                "nativeLabel": kpi.get("nativeLabel", kpi["label"]),
                "category": kpi["category"],
                "family": kpi.get("family", LEGACY_CATEGORY_TO_FAMILY.get(kpi["category"], "continuity_disruption")),
                "unit": kpi.get("unit"),
                "nativeScale": kpi.get("nativeScale"),
                "thresholdHints": kpi.get("thresholdHints", []),
                "baselineNote": kpi["baselineNote"],
                "optionValues": option_values,
                "optionMeta": option_meta,
                "optionRisks": option_risks,
            }
        )
    return catalog


def compute_kpi_priority_inputs(
    kpi: Dict[str, Any],
    option_analysis: Dict[str, Dict[str, Any]],
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
    scenario_relevance: int,
) -> Dict[str, float]:
    code = kpi["code"]
    effects = [option["effects"].get(code, 0.0) for option in option_analysis.values()]
    spread = (max(effects) - min(effects)) if effects else 0.0
    family = kpi.get("family", "continuity_disruption")
    authority = str(normalized_persona.get("decisionAuthority", "")).lower()
    horizon = " ".join(filter(None, [parsed.time_horizon, parsed.tension, parsed.scenario])).lower()

    relevance = min(5.0, max(1.0, float(scenario_relevance + 1)))
    sensitivity = min(5.0, max(1.0, 1.0 + (spread * 1.5)))
    if any(token in authority for token in ("board", "executive", "full")):
        actionability = 4.5
    elif family in {"financial_impact", "resource_pressure", "continuity_disruption", "urgency_time"}:
        actionability = 4.0
    elif family in {"institutional_reputation", "stakeholder_trust", "regulatory_legal"}:
        actionability = 3.5
    else:
        actionability = 3.0
    urgency_link = 1.0
    if family == "urgency_time":
        urgency_link += 2.5
    if any(token in horizon for token in ("today", "urgent", "11 days", "month-end", "next quarter", "weeks")):
        urgency_link += 1.5
    elif any(token in horizon for token in ("months", "year", "years")):
        urgency_link += 0.5

    return {
        "relevance": round(min(5.0, relevance), 2),
        "sensitivity": round(min(5.0, sensitivity), 2),
        "actionability": round(min(5.0, actionability), 2),
        "urgencyLink": round(min(5.0, urgency_link), 2),
    }


def compute_kpi_priority_score(priority_inputs: Dict[str, float]) -> float:
    return round(
        (priority_inputs.get("relevance", 1.0) * 0.4)
        + (priority_inputs.get("sensitivity", 1.0) * 0.3)
        + (priority_inputs.get("actionability", 1.0) * 0.2)
        + (priority_inputs.get("urgencyLink", 1.0) * 0.1),
        3,
    )


def order_kpis_for_emotion(
    emotion_code: str,
    kpis: List[Dict[str, Any]],
    option_scores: Dict[str, float],
    option_analysis: Dict[str, Dict[str, Any]],
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
    emotion_weights: Dict[str, float],
    hard_priority_kpis: List[str],
    scenario_salience: Dict[str, int],
    top_kpi_count: int,
) -> List[Dict[str, Any]]:
    baseline = round(100.0 / len(kpis), 1) if kpis else 12.5
    placed: Dict[str, Dict[str, Any]] = {}

    for kpi in kpis:
        code = kpi["code"]
        score = option_scores.get(code, 1.0)
        if code in hard_priority_kpis and score < 1.5:
            placed[code] = {
                "code": code,
                "slotType": "priority",
                "flag": flag_for_score(score),
                "weightPct": round(emotion_weights[code], 1),
                "reason": f"Hard priority for this persona; currently {flag_for_score(score)}",
                "rankScore": round(emotion_weights[code] * severity_for_score(score), 1),
            }

    for kpi in kpis:
        code = kpi["code"]
        if code in placed:
            continue
        score = option_scores.get(code, 1.0)
        distortion = round(emotion_weights[code] - baseline, 1)
        if distortion < -7.0 and score < 0.5:
            placed[code] = {
                "code": code,
                "slotType": "blind_spot_warning",
                "flag": flag_for_score(score),
                "weightPct": round(emotion_weights[code], 1),
                "reason": f"{emotion_code} under-weights this by {abs(distortion):.1f} pts vs baseline {baseline:.1f}%; reading is red",
                "rankScore": round(emotion_weights[code] * severity_for_score(score), 1),
            }

    remaining = [k for k in kpis if k["code"] not in placed]
    priority_inputs = {
        kpi["code"]: compute_kpi_priority_inputs(
            kpi,
            option_analysis,
            normalized_persona,
            parsed,
            scenario_salience.get(kpi["code"], 1),
        )
        for kpi in kpis
    }
    remaining.sort(
        key=lambda item: (
            -compute_kpi_priority_score(priority_inputs[item["code"]]),
            -emotion_weights[item["code"]],
        )
    )
    for kpi in remaining[:top_kpi_count]:
        code = kpi["code"]
        score = option_scores.get(code, 1.0)
        priority_score = compute_kpi_priority_score(priority_inputs[code])
        placed[code] = {
            "code": code,
            "slotType": "primary",
            "flag": flag_for_score(score),
            "weightPct": round(emotion_weights[code], 1),
            "reason": (
                f"Priority score {priority_score:.2f} from relevance {priority_inputs[code]['relevance']}, "
                f"sensitivity {priority_inputs[code]['sensitivity']}, actionability {priority_inputs[code]['actionability']}, "
                f"urgency {priority_inputs[code]['urgencyLink']}"
            ),
            "rankScore": round(priority_score * emotion_weights[code] * severity_for_score(score), 1),
        }

    for kpi in kpis:
        code = kpi["code"]
        if code in placed:
            continue
        score = option_scores.get(code, 1.0)
        priority_score = compute_kpi_priority_score(priority_inputs[code])
        placed[code] = {
            "code": code,
            "slotType": "secondary",
            "flag": flag_for_score(score),
            "weightPct": round(emotion_weights[code], 1),
            "reason": f"Secondary priority {priority_score:.2f} for {emotion_code}",
            "rankScore": round(priority_score * emotion_weights[code] * severity_for_score(score), 1),
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
        item["priorityInputs"] = priority_inputs.get(item["code"], {})
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


def score_based_value_phrase(score: float, category: str) -> str:
    tiers = SCORE_VALUE_PHRASES.get(category)
    if not tiers:
        if score < 0.5:
            return "high impact"
        if score < 1.5:
            return "moderate impact"
        return "well managed"
    if score < 0.5:
        return tiers[0]
    if score < 1.5:
        return tiers[1]
    return tiers[2]


def generic_meta(category: str, score: float) -> str:
    tiers = SCORE_META_PHRASES.get(category)
    if not tiers:
        tier = "high" if score < 0.5 else "moderate" if score < 1.5 else "low"
        return f"{tier} impact on this dimension"
    if score < 0.5:
        return tiers[0]
    if score < 1.5:
        return tiers[1]
    return tiers[2]


def score_value_label(score: float, category: str, option_id: str, label: str) -> str:
    phrases = scenario_value_phrases(category, label)
    if option_id == "fund":
        return phrases["fund"]
    if option_id == "defer":
        return phrases["defer"]
    if option_id == "split":
        return phrases["split"]
    return score_based_value_phrase(score, category)


def score_meta_label(
    score: float,
    category: str,
    option_id: str,
    label: str,
    normalized_persona: Dict[str, Any],
    parsed: ParseResult,
    risk: Optional[Dict[str, Any]] = None,
) -> str:
    risk_text = (risk or risk_for_score(score)).get("text", "Moderate risk")
    role = normalized_persona["roleLabel"]
    lower_label = label.lower()
    if option_id == "fund" or any(w in lower_label for w in ("fund", "full bond", "raise", "launch", "commit", "proceed")):
        action = fund_meta(category, label, parsed)
    elif option_id == "defer" or any(w in lower_label for w in ("defer", "delay", "postpone", "wait", "hold")):
        action = defer_meta(category, label, parsed)
    elif option_id == "split" or any(w in lower_label for w in ("split", "partial", "hybrid", "mixed")):
        action = split_meta(category, label, parsed)
    else:
        action = generic_meta(category, score)
    return f"{risk_text}: {action} for the {role} lens."


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


def risk_for_score(score: float) -> Dict[str, str]:
    if score >= 1.5:
        return {"level": "green", "text": "Low risk"}
    if score >= 0.5:
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
    top_drivers: Optional[List[Dict[str, Any]]] = None,
) -> str:
    emotion_name = EMOTION_LABELS.get(emotion_code, emotion_code)
    role = normalized_persona["roleLabel"]
    posture = EMOTION_POSTURE.get(emotion_code, "weights the available KPIs")
    if top_drivers:
        kpi_list = ", ".join(d["kpi_label"] for d in top_drivers[:3])
        return (
            f"{emotion_name} mode reads this through the {role} lens. "
            f"It {posture}, which is why the top drivers here are: {kpi_list}."
        )
    top_kpis_str = top_weighted_kpis(emotion_code, weights, kpis)
    return (
        f"{emotion_name} mode reads this through the {role} lens. "
        f"It {posture}: {top_kpis_str}."
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


def consequence_risk(
    emotion_code: str,
    parsed: "ParseResult",
    recommended_label: str,
    blind_spot_labels: List[str],
    winner_contributions: Optional[List[Dict[str, Any]]] = None,
    emotion_weights: Optional[Dict[str, float]] = None,
) -> str:
    missed, favoured, failure_verb = EMOTION_FAILURE_MODES.get(
        emotion_code, ("hidden downside", "visible signals", "incomplete information")
    )
    emotion_name = EMOTION_LABELS.get(emotion_code, emotion_code)
    base = (
        f"{emotion_name} can over-weight {favoured} at the cost of {missed}. "
        f"This recommendation is vulnerable to {failure_verb}."
    )

    if winner_contributions and emotion_weights:
        avg_weight = sum(emotion_weights.values()) / max(len(emotion_weights), 1)
        under_weighted_reds = [
            c for c in winner_contributions
            if c["flag"] == "red" and c["weight"] < avg_weight
        ]
        if under_weighted_reds:
            names = ", ".join(c["kpi_label"] for c in under_weighted_reds[:2])
            is_are = "is" if len(under_weighted_reds) == 1 else "are"
            it_them = "it" if len(under_weighted_reds) == 1 else "them"
            return base + f" Specifically, {names} {is_are} red under the winner — watch {it_them} closely."

    if parsed.tension:
        base += f" Active tension: {parsed.tension.rstrip('.')}."
    if blind_spot_labels:
        base += f" Watch: {', '.join(blind_spot_labels[:2])}."
    return base


def next_step(
    emotion_code: str,
    close_call: bool,
    parsed: "ParseResult",
    recommended_label: str,
    runner_up_label: Optional[str] = None,
    margin: float = 0.0,
    blind_spot_items: Optional[List[Dict[str, Any]]] = None,
    top_drivers: Optional[List[Dict[str, Any]]] = None,
) -> str:
    emotion_name = EMOTION_LABELS.get(emotion_code, emotion_code)
    runner_up = runner_up_label or "the runner-up option"

    if close_call:
        top_driver_name = top_drivers[0]["kpi_label"] if top_drivers else "the top-weighted KPI"
        text = (
            f"Close margin ({margin:.1f} pts) between \"{recommended_label}\" and "
            f"\"{runner_up}\". Before committing, test both options "
            f"head-to-head on {top_driver_name} — the KPI that produced the tilt."
        )
        if parsed.time_horizon:
            text += f" Decision window: {parsed.time_horizon}."
        return text

    if blind_spot_items:
        top_blind = blind_spot_items[0]
        blind_label = top_blind.get("label", "the blind-spot KPI")
        blind_flag = top_blind.get("flag", "flagged")
        return (
            f"Commit to \"{recommended_label}\" but add a 72-hour checkpoint on "
            f"{blind_label} — currently {blind_flag} and under-weighted by {emotion_name} mode. "
            f"If it degrades further, fall back to \"{runner_up}\"."
        )

    action = EMOTION_NEXT_STEP_ACTIONS.get(emotion_code, "confirm before committing")
    text = f"Commit to \"{recommended_label}\" — {action}."
    if parsed.time_horizon:
        text += f" Decision window: {parsed.time_horizon}."
    return text


def band_confidence(score: float) -> str:
    if score >= 0.85:
        return "High"
    if score >= 0.7:
        return "Medium-High"
    if score >= 0.5:
        return "Medium"
    if score >= 0.3:
        return "Low-Medium"
    return "Low"


def compute_confidence(
    parsed: ParseResult,
    enrichment: Dict[str, Any],
    option_count: int,
    ml_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    score = 0.0
    if parsed.persona:
        score += 1.0
    if parsed.scenario:
        score += 1.0
    if parsed.call:
        score += 0.8
    if parsed.kpis:
        score += 1.0
    if option_count >= 2:
        score += 0.8
    if enrichment["used"]:
        score += 0.4

    recommendation_conf = band_confidence(min(1.0, score / 5.0))
    evidence_score = 0.4
    if parsed.scenario:
        evidence_score += 0.2
    if parsed.kpis:
        evidence_score += 0.2
    if parsed.time_horizon or parsed.tension:
        evidence_score += 0.1
    if parsed.call:
        evidence_score += 0.1
    evidence_conf = band_confidence(min(1.0, evidence_score))
    divergence_conf = band_confidence(float((ml_metadata or {}).get("weightConfidence", 0.45)))
    blind_spot_conf = "Medium" if parsed.kpis else "Low"

    return {
        "overall": recommendation_conf,
        "recommendationConfidence": recommendation_conf,
        "evidenceConfidence": evidence_conf,
        "emotionDivergenceSeverity": divergence_conf,
        "blindSpotExposure": blind_spot_conf,
    }


def build_missing_message(missing: List[str]) -> str:
    if missing == ["persona"]:
        return "The upload is missing the decision-maker. Add a persona or role so the framework can weight the scenario correctly."
    if missing == ["scenario"]:
        return "The upload is missing the decision scenario. Add the situation and decision call so the framework can analyze it."
    return "The upload is missing both persona and scenario. Add who is deciding and what decision they are facing."
