import json
import os
from typing import Any, Dict, List, Optional
from urllib import error as _urlerror
from urllib import request as _urlrequest
from urllib.parse import urlparse as _urlparse

try:
    from .fixed_matrix import execute_fixed_matrix_stack  # type: ignore
except Exception:  # pragma: no cover
    from fixed_matrix import execute_fixed_matrix_stack


BROAD_QUESTION_HINTS = {
    "best solution",
    "best path",
    "right path",
    "what should we do",
    "what should i do",
    "what now",
    "help",
    "tell me the answer",
    "give me the answer",
    "what is the answer",
    "best move",
}

INTENT_PATTERNS = {
    "kpi_lookup": ["what is my variance", "what is the variance", "variance", "what is my commercials", "what is my commercial position", "commercial position", "commercial exposure", "contract exposure"],
    "threshold": ["at what point", "threshold", "trigger", "red line", "minimum acceptable", "where does risk become", "become unacceptable"],
    "probability": ["how likely", "probability", "expected value", "chance", "odds", "combined probability"],
    "comparison": ["compare", "versus", "vs", "better than", "option a", "option b", "trade-off"],
    "legal_trigger": ["legal obligation", "obligation to disclose", "mandatory", "covenant", "grant", "governance-wise", "materiality", "required to disclose"],
    "reversibility": ["preserves room to recover", "point of no return", "reversible", "reversibility", "switching cost", "lock-in"],
    "stakeholder_signal": ["what signal", "how will this look", "who should know", "who to tell", "tell first", "notify", "stakeholder", "if leaked"],
    "cost_of_delay": ["what happens if you wait", "cost of waiting", "cost of delay", "if we wait", "delay cost", "wait longer"],
    "action_selection": ["what should", "best move", "right path", "best option", "most defensible", "which path"],
    "consequence": ["what happens if", "consequence", "fallout", "downstream effect", "second-order"],
    "sequencing": ["what should be done first", "first second third", "before escalation", "sequence", "what information must be gathered"],
    "data": ["what data", "what evidence", "which kpi", "what matters most", "evidence required"],
}

DECISION_FAMILY_PATTERNS = {
    "contract-entitlement": [
        "entitlement",
        "contractual cover",
        "under the clause",
        "under clause",
        "notice compliance",
        "certification rules",
        "compensable",
        "variation claim",
        "change order",
        "valid under clause",
    ],
    "commercial-exposure": [
        "commercial position",
        "commercial exposure",
        "customer exposure",
        "revenue at risk",
        "margin erosion",
        "offtake",
        "portfolio precedent",
        "commercials",
        "contract exposure",
        "counterparty",
    ],
    "variance": [
        "variance",
        "drift",
        "overrun",
        "vs plan",
        "vs budget",
        "contingency burn",
        "cost drift",
        "schedule variance",
        "funding-case variance",
    ],
    "bids-pricing": [
        "bid",
        "bids",
        "pricing",
        "price protection",
        "repricing",
        "rebid",
        "tender",
        "win probability",
        "priced risk",
        "award stage",
    ],
    "disclosure": [
        "disclose",
        "notify",
        "late-notice",
        "governance",
        "audit",
        "dbet",
        "board reporting",
        "materiality",
        "fairness concerns",
        "stakeholder signal",
    ],
    "timing": [
        "when",
        "now",
        "wait",
        "delay",
        "timing",
        "trigger",
        "deadline",
        "slip",
    ],
    "risk": [
        "risk",
        "riskiest",
        "exposure",
        "downside",
        "danger",
        "worst",
        "consequence",
    ],
    "strategy": [
        "strategic",
        "long-term",
        "long horizon",
        "optionality",
        "precedent",
        "positioning",
        "best decision",
    ],
    "data-needed": [
        "what data",
        "what evidence",
        "which kpi",
        "what matters most",
        "evidence required",
        "confirm",
    ],
}

FIXED_MATRIX_QUESTION_PATTERNS = {
    "meaning": ["what does", "what is", "what does this mean", "meaning", "understand", "read on", "status of"],
    "comparison": ["compare", "versus", "vs", "better than", "trade-off", "difference between"],
    "threshold": ["threshold", "trigger", "at what point", "red line", "stop", "go/no-go", "when does this become"],
    "consequence": ["what happens if", "consequence", "fallout", "downside", "risk if", "impact if", "worst case"],
    "prioritization": ["most important", "priority", "what matters most", "where should i focus", "dominant issue"],
    "clarification": ["do you mean", "which of these", "narrow this", "more context"],
    "action": ["what should", "best decision", "best move", "what do we do", "next step", "recommended decision", "what decision is best"],
    "missing_data": ["what data", "what evidence", "missing evidence", "what else do we need", "what should we verify"],
}

PERSONA_WRITING_RULES = [
    {
        "match": ("ceo",),
        "lead": "At enterprise level",
        "matters": "programme credibility, grant exposure, and cross-functional continuity",
        "next_step": "take an enterprise call that protects date confidence without losing control of precedent",
    },
    {
        "match": ("cfo",),
        "lead": "Financially",
        "matters": "contingency, covenant headroom, grant drawdown, and precedent risk",
        "next_step": "protect headroom and optionality before the number hardens into precedent",
    },
    {
        "match": ("project director",),
        "lead": "At programme-control level",
        "matters": "schedule float, contractor behaviour, live-site coordination, and delivery discipline",
        "next_step": "keep the issue inside disciplined change control and protect critical-path logic",
    },
    {
        "match": ("board chair",),
        "lead": "From a governance standpoint",
        "matters": "materiality, disclosure defensibility, and institutional credibility",
        "next_step": "make sure the board can defend the framing later, not just the action today",
    },
    {
        "match": ("commercial director",),
        "lead": "Commercially",
        "matters": "customer confidence, revenue protection, and contractability",
        "next_step": "protect the account position without creating an avoidable renegotiation trigger",
    },
    {
        "match": ("head of scrap procurement", "procurement"),
        "lead": "From a supply-assurance standpoint",
        "matters": "contracted volume security, supplier concentration, and cost-base optionality",
        "next_step": "secure cover where it matters, but do not lock into the wrong cost position too early",
    },
    {
        "match": ("head of energy",),
        "lead": "From an energy-position standpoint",
        "matters": "long-term competitiveness, grid timing, and contracting leverage",
        "next_step": "protect structural cost position rather than optimize for short-term convenience",
    },
    {
        "match": ("chro",),
        "lead": "From a workforce-readiness standpoint",
        "matters": "skills readiness, labour market pressure, and workforce trust",
        "next_step": "protect readiness and trust before the people system absorbs avoidable damage",
    },
    {
        "match": ("union",),
        "lead": "From a member-accountability standpoint",
        "matters": "member trust, fairness, and negotiation leverage",
        "next_step": "do not spend escalation capital casually, but do not hide the trust consequence either",
    },
    {
        "match": ("council",),
        "lead": "Publicly",
        "matters": "community trust, regeneration credibility, and local economic stability",
        "next_step": "protect institutional trust before the public narrative hardens against the programme",
    },
]

VO112_GLOBAL_FACTS = {
    "claim_total": "£31.4M",
    "agreed_amount": "£16.5M",
    "disputed_amount": "£14.9M",
    "contingency_total": "£93M",
    "extension": "11 weeks",
    "schedule_float": "7 weeks",
    "grant_conditions_at_risk": "2",
    "offtake_contracted": "61% of target",
    "decision_window": "21 days",
    "suspension_extra_slip": "6–8 weeks",
    "total_slip_if_suspended": "17–19 weeks",
}

SCENARIO_WRITING_RULES = {
    "contracts": {
        "match": ("contracts", "commercial-contracts", "commercial-variance", "variation", "claim"),
        "name": "contracts / commercial variance",
        "decision_focus": "current exposure, contractual leverage, and precedent risk",
    },
    "schedule": {
        "match": ("schedule", "delivery", "commissioning"),
        "name": "schedule / delivery",
        "decision_focus": "float consumption, dependency risk, and commissioning credibility",
    },
    "workforce": {
        "match": ("workforce", "transition"),
        "name": "workforce / transition",
        "decision_focus": "readiness, trust, and organisational execution risk",
    },
    "default": {
        "match": (),
        "name": "active scenario",
        "decision_focus": "the live decision tension in the scenario",
    },
}

FIXED_MATRIX_LENS_HINTS = {
    "cautious": ["cautious", "safest", "safe", "protect", "downside", "worst", "defensible", "exposure", "harm"],
    "strategic": ["strategic", "long-term", "optionality", "future", "precedent", "positioning", "thesis"],
    "decisive": ["decisive", "now", "immediately", "act", "do now", "next step", "fastest", "commit"],
    "analytical": ["analytical", "data", "evidence", "compare", "understand", "probability", "certainty", "why"],
}

FIXED_MATRIX_PERSPECTIVE_HINTS = {
    "self": ["personal", "my", "role", "accountability", "exposure", "owner", "mandate", "career"],
    "stakeholder": ["stakeholder", "people", "customer", "union", "government", "community", "relationship", "trust"],
    "business": ["business", "outcome", "delivery", "commercial", "financial", "schedule", "value", "result"],
    "ethics": ["ethics", "governance", "approval", "board", "compliance", "defensible", "rule", "disclose", "materiality"],
}


def _perspective_kind(label: str) -> str:
    lower = (label or "").lower()
    if "schedule" in lower or "delivery" in lower:
        return "schedule"
    if "financial" in lower or "grant" in lower or "cash" in lower or "budget" in lower:
        return "financial"
    if "people" in lower or "political" in lower or "stakeholder" in lower or "governance" in lower:
        return "people"
    if "commercial" in lower or "strategic" in lower or "customer" in lower:
        return "commercial"
    return "default"


def _extract_tokens(value: str) -> List[str]:
    return [item for item in "".join(ch if ch.isalnum() else " " for ch in (value or "").lower()).split() if len(item) > 3]


def _dedupe(items: List[str], limit: int = 5) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if not item:
            continue
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
        if len(out) >= limit:
            break
    return out


def _normalize_kpi_text(value: str) -> str:
    return " ".join("".join(ch if ch.isalnum() else " " for ch in (value or "").lower()).split())


def _lower_first(value: str) -> str:
    if not value:
        return ""
    return value[:1].lower() + value[1:]


def _first_sentence(value: str) -> str:
    text = " ".join((value or "").split()).strip()
    if not text:
        return ""
    for marker in [". ", "? ", "! "]:
        if marker in text:
            return text.split(marker, 1)[0].strip() + marker.strip()
    return text


def _is_broad_question(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    if lower in BROAD_QUESTION_HINTS:
        return True
    tokens = _extract_tokens(lower)
    if len(tokens) <= 2 and any(word in lower for word in ["help", "answer", "solution", "path", "what", "now"]):
        return True
    return False


def _classify_intent(question: str) -> str:
    lower = (question or "").lower()
    winner = "action_selection"
    best = 0
    for intent, phrases in INTENT_PATTERNS.items():
        score = sum(2 for phrase in phrases if phrase in lower)
        score += sum(1 for token in _extract_tokens(lower) if any(token in phrase for phrase in phrases))
        if score > best:
            best = score
            winner = intent
    return winner


def _classify_outcome_preference(question: str) -> str:
    lower = (question or "").lower()
    if any(term in lower for term in ["worst", "riskiest", "most risky", "highest risk", "dangerous", "least defensible", "disastrous"]):
        return "worst"
    if any(term in lower for term in ["risky", "high risk", "downside", "exposure"]):
        return "risky"
    if any(term in lower for term in ["moderate", "balanced", "middle ground", "hybrid", "pragmatic", "measured"]):
        return "moderate"
    if any(term in lower for term in ["strategic", "long-term", "long horizon", "optionality", "precedent", "institutional"]):
        return "strategic"
    if any(term in lower for term in ["best", "safest", "optimal", "most defensible", "right choice", "best choice"]):
        return "best"
    return "default"


def _classify_decision_family(question: str, context: Dict[str, Any]) -> str:
    lower = (question or "").lower()
    winner = "strategy"
    best = 0
    for family, phrases in DECISION_FAMILY_PATTERNS.items():
        score = sum(3 for phrase in phrases if phrase in lower)
        score += sum(1 for token in _extract_tokens(lower) if any(token in phrase for phrase in phrases))
        if score > best:
            best = score
            winner = family

    scenario_context = " ".join(
        [
            str(context.get("scenario_summary") or ""),
            *[str(item) for item in (context.get("scenario_decision_context") or {}).values()],
            *[str(item.get("label") or "") for item in (context.get("scenario_kpis") or []) if isinstance(item, dict)],
        ]
    ).lower()
    if winner == "strategy" and "variance" in lower and "variance" in scenario_context:
        return "variance"
    if winner == "strategy" and any(term in lower for term in ["commercial", "customer", "revenue", "margin", "offtake"]):
        return "commercial-exposure"
    if winner == "strategy" and any(term in lower for term in ["contract", "entitlement", "clause", "notice"]):
        return "contract-entitlement"
    if winner == "strategy" and any(term in lower for term in ["bid", "pricing", "tender", "price"]):
        return "bids-pricing"
    if winner == "strategy" and any(term in lower for term in ["disclose", "notify", "governance", "audit", "dbet"]):
        return "disclosure"
    if winner == "strategy" and any(term in lower for term in ["risk", "worst", "danger", "downside", "exposure"]):
        return "risk"
    if winner == "strategy" and any(term in lower for term in ["when", "wait", "delay", "timing", "trigger"]):
        return "timing"
    if winner == "strategy" and any(term in lower for term in ["data", "evidence", "kpi", "confirm"]):
        return "data-needed"
    return winner


def _match_persona_writing_rule(role: str) -> Dict[str, str]:
    lower = (role or "").lower()
    for rule in PERSONA_WRITING_RULES:
        if any(term in lower for term in rule["match"]):
            return rule
    return {
        "lead": f"For {role or 'the active role'}",
        "matters": "the consequences that sit inside this role's mandate",
        "next_step": "turn the signal into a concrete next move",
    }


def _match_scenario_writing_rule(kinds: List[str], decision_family: str) -> Dict[str, str]:
    lower_kinds = " ".join((kinds or [])).lower()
    for rule in SCENARIO_WRITING_RULES.values():
        if any(term in lower_kinds for term in rule["match"]):
            return rule
    if decision_family in {"contract-entitlement", "commercial-exposure", "variance", "bids-pricing"}:
        return SCENARIO_WRITING_RULES["contracts"]
    if decision_family == "timing":
        return SCENARIO_WRITING_RULES["schedule"]
    return SCENARIO_WRITING_RULES["default"]


def _is_vo112_context(context: Dict[str, Any]) -> bool:
    combined = " ".join(
        str(item or "")
        for item in [
            context.get("scenario_id"),
            context.get("scenario_title"),
            context.get("scenario_summary"),
        ]
    ).lower()
    return any(term in combined for term in ["vo112", "vo-112", "tenova", "variation order cascade"])


def _build_vo112_variance_answer(
    context: Dict[str, Any],
    cell: Dict[str, Any],
    execution: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    if not _is_vo112_context(context):
        return None
    persona = context.get("vo112_persona_schema") or {}
    role = (persona.get("role") or context.get("persona_role") or "").lower()
    if "ceo" not in role:
        return None

    kpi_spine = persona.get("kpi_spine") or []
    k3 = next((item for item in kpi_spine if str(item.get("kpiCode")) == "K3"), {})
    k1 = next((item for item in kpi_spine if str(item.get("kpiCode")) == "K1"), {})
    k7 = next((item for item in kpi_spine if str(item.get("kpiCode")) == "K7"), {})
    facts = VO112_GLOBAL_FACTS

    direct_answer = (
        f"Your current variance is a programme-level commercial variance, not just a budget delta. "
        f"Tenova's VO-112 has created a {facts['claim_total']} cost variance against the approved programme baseline, "
        f"with {facts['agreed_amount']} agreed in principle and {facts['disputed_amount']} disputed."
    )
    why_this_answer = (
        f"This already threatens schedule float, grant covenant exposure, and customer confidence. "
        f"The first KPI to surface is {k3.get('kpiLabel', 'K3 · Grant covenant conditions at risk')} because it is the fastest route to damaging the 2027 commitment and the DBET relationship."
    )
    recommended_decision = (
        "Negotiate a commercial settlement rather than simply paying the full claim or withholding the disputed amount. "
        "In the CEO scenario, this is the middle path: preserve programme continuity, avoid triggering Tenova suspension rights, and reduce exposure versus paying the full £31.4M."
    )
    decision_risk = (
        "You may still pay more than Tata's strict legal position requires, and it may set a precedent for future contractor claims. "
        f"But withholding carries the sharper downside: Tenova may suspend, adding {facts['suspension_extra_slip']} more weeks to the existing extension and potentially pushing total slip to {facts['total_slip_if_suspended']}, which would likely break the 2027 date."
    )
    suggested_next_step = (
        f"Open a {facts['decision_window']} CEO escalation track: authorize commercial negotiation on the disputed {facts['disputed_amount']}, "
        "prepare a DBET/grant-notification position because grant conditions are already at risk, "
        "and ask for a combined decision pack showing settlement range, schedule impact if Tenova suspends, and grant/customer exposure if the date slips further."
    )
    reasoning_summary = (
        f"The answer is anchored first on {k3.get('kpiLabel', 'grant covenant conditions at risk')} because it is a hard-priority red signal, "
        f"then on {k1.get('kpiLabel', 'schedule float remaining')} because the date risk is already compressed, "
        f"with {k7.get('kpiLabel', 'customer offtake volume contracted')} kept visible as the commercial confidence signal."
    )
    return {
        "direct_answer": direct_answer,
        "why_this_answer": why_this_answer,
        "recommended_decision": recommended_decision,
        "decision_risk": decision_risk,
        "suggested_next_step": suggested_next_step,
        "reasoning_summary": reasoning_summary,
        "likely_consequence": _first_sentence(decision_risk),
        "watch_item": k1.get("kpiLabel", "K1 · EAF schedule float remaining"),
        "missing_data": "",
    }


def _compose_fixed_answer_spine(
    question: str,
    question_type: str,
    decision_family: str,
    cell: Dict[str, Any],
    execution: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, str]:
    vo112_override = None
    if decision_family == "variance":
        vo112_override = _build_vo112_variance_answer(context, cell, execution)
    if vo112_override:
        return vo112_override

    normalized_persona = context.get("normalized_decision_profile") or {}
    normalized_scenario = context.get("normalized_scenario_profile") or {}
    role = normalized_persona.get("role") or context.get("persona_role") or "the active role"
    scenario_title = normalized_scenario.get("scenario_title") or context.get("scenario_title") or "this scenario"
    scenario_tension = normalized_scenario.get("tension") or context.get("persona_tension") or ""
    scenario_kinds = normalized_scenario.get("scenario_kinds") or []
    persona_rule = _match_persona_writing_rule(role)
    scenario_rule = _match_scenario_writing_rule(scenario_kinds, decision_family)
    matched = execution.get("matched_visible_data") or []
    primary = matched[0] if matched else {}
    secondary = matched[1] if len(matched) > 1 else {}
    support = matched[2] if len(matched) > 2 else {}
    cell_face = execution.get("cell_face") or cell.get("cell_face") or {}
    stack_rationale = cell.get("stack_rationale") or {}
    primary_label = primary.get("label") or cell.get("primary_kpi") or "the leading signal"
    primary_summary = primary.get("summary") or primary.get("preview") or f"{primary_label} is the dominant signal in the scenario."
    secondary_label = secondary.get("label") or ""
    support_label = support.get("label") or ""
    lens = cell.get("decision_lens_label") or cell.get("emotion_mode_label") or "this decision lens"
    perspective = cell.get("perspective_label") or cell.get("perspective_code") or "this perspective"

    if decision_family == "variance":
        direct_answer = f"{persona_rule['lead']}, the main variance in {scenario_title} sits in {primary_label.lower()}."
    elif decision_family == "commercial-exposure":
        direct_answer = f"{persona_rule['lead']}, the real commercial exposure in {scenario_title} sits in {primary_label.lower()}."
    elif decision_family == "contract-entitlement":
        direct_answer = f"{persona_rule['lead']}, the decision turns on whether {primary_label.lower()} gives enough cover to hold the line in {scenario_title}."
    elif question_type == "threshold":
        direct_answer = f"{persona_rule['lead']}, {primary_label.lower()} is the trigger point to watch in {scenario_title}."
    elif question_type == "missing_data":
        direct_answer = f"{persona_rule['lead']}, do not lock the decision yet; the missing piece is {primary_label.lower()}."
    elif question_type == "consequence":
        direct_answer = f"{persona_rule['lead']}, the first thing that breaks in {scenario_title} is {primary_label.lower()}."
    else:
        direct_answer = f"{persona_rule['lead']}, the strongest current call in {scenario_title} is to anchor the decision on {primary_label.lower()}."
    if cell_face.get("decision"):
        direct_answer = cell_face["decision"]

    why_this_answer = " ".join(filter(None, [
        f"The call is anchored on {primary_label.lower()}",
        f"because that is the clearest live signal in {scenario_title}.",
        f"The context is {scenario_tension.lower()}." if scenario_tension else "",
    ])).strip()

    if question_type == "missing_data":
        recommended_decision = f"Hold the decision open until {primary_label.lower()} is resolved, then commit from the {lens.lower()} × {perspective.lower()} route."
    elif question_type == "threshold":
        recommended_decision = f"Keep the current posture only while {primary_label.lower()} remains inside tolerance; once it worsens, change course."
    else:
        recommended_decision = f"Use {primary_label.lower()} as the decision anchor and make the call in a way that protects {scenario_rule['decision_focus']}."
    if cell_face.get("decision"):
        recommended_decision = cell_face["decision"]

    decision_risk = (
        secondary.get("summary")
        or execution.get("decision_risk")
        or f"The downside is underweighting {secondary_label.lower() if secondary_label else 'the secondary tension'} while the role stays anchored to {primary_label.lower()}."
    )
    suggested_next_step = (
        support.get("summary")
        or execution.get("suggested_next_step")
        or f"Next, {persona_rule['next_step']} by testing {support_label.lower() if support_label else primary_label.lower()} explicitly."
    )
    reasoning_summary = " ".join(filter(None, [
        f"This routes through {lens} × {perspective}",
        f"because it best protects {scenario_rule['decision_focus']} for {role}.",
    ])).strip()
    likely_consequence = (
        cell.get("consequence")
        or secondary.get("summary")
        or f"If this is handled badly, pressure shifts from {primary_label.lower()} into the next-order consequence for {role}."
    )
    watch_item = secondary_label or execution.get("watch_item") or ""
    missing_data = execution.get("missing_data") or (
        primary_label if question_type == "missing_data" else ""
    )
    return {
        "direct_answer": direct_answer.strip(),
        "why_this_answer": _first_sentence(why_this_answer.strip()),
        "recommended_decision": recommended_decision.strip(),
        "decision_risk": decision_risk.strip(),
        "suggested_next_step": _first_sentence(suggested_next_step.strip()),
        "reasoning_summary": _first_sentence(reasoning_summary.strip()),
        "likely_consequence": _first_sentence(likely_consequence),
        "watch_item": watch_item.strip(),
        "missing_data": missing_data.strip(),
    }


def _uses_fixed_matrix(context: Dict[str, Any]) -> bool:
    return bool(context.get("uses_fixed_matrix"))


def _classify_fixed_question_type(question: str) -> str:
    lower = (question or "").lower()
    if any(phrase in lower for phrase in ["what data", "what evidence", "missing evidence", "what else do we need", "what should we verify"]):
        return "missing_data"
    if any(phrase in lower for phrase in ["threshold", "trigger", "at what point", "red line", "stop", "go/no-go", "when does this become"]):
        return "threshold"
    if any(phrase in lower for phrase in ["compare", "versus", "vs", "better than", "trade-off", "difference between"]):
        return "comparison"
    if any(phrase in lower for phrase in ["what should", "best decision", "best move", "what do we do", "next step", "recommended decision", "what decision is best", "route", "decision"]):
        return "action"
    if any(phrase in lower for phrase in ["what happens if", "consequence", "fallout", "downside", "risk if", "impact if", "worst case"]):
        return "consequence"
    winner = "action"
    best = 0
    for question_type, phrases in FIXED_MATRIX_QUESTION_PATTERNS.items():
        score = sum(3 for phrase in phrases if phrase in lower)
        score += sum(1 for token in _extract_tokens(lower) if any(token in phrase for phrase in phrases))
        if score > best:
            best = score
            winner = question_type
    return winner


def _find_cell_by_id(context: Dict[str, Any], cell_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not cell_id:
        return None
    for cell in context.get("matrix_cells", []) or []:
        if cell.get("cell_id") == cell_id:
            return cell
    return None


def _build_evidence_used(cell: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    scenario_context = context.get("scenario_decision_context") or {}
    return _dedupe(
        [
            f"Primary KPI: {cell.get('primary_kpi')}" if cell.get("primary_kpi") else "",
            *[f"Supporting KPI: {item}" for item in (cell.get("supporting_kpis") or [])[:2]],
            *[f"Scenario context: {item}" for item in scenario_context.values()],
            f"Scenario summary: {context.get('scenario_summary')}" if context.get("scenario_summary") else "",
        ],
        5,
    )


def _fixed_visible_data_fit(question: str, cell: Dict[str, Any]) -> float:
    lower = (question or "").lower()
    score = 0.0
    for item in cell.get("ranked_visible_data") or []:
        label = str(item.get("label") or "").lower()
        summary = str(item.get("summary") or item.get("preview") or "").lower()
        evidence = " ".join(str(piece or "").lower() for piece in (item.get("evidence") or []))
        if label and label in lower:
            score += 1.0
        score += min(0.6, sum(0.15 for token in _extract_tokens(label) if token in lower))
        score += min(0.5, sum(0.1 for token in _extract_tokens(summary) if token in lower))
        score += min(0.3, sum(0.06 for token in _extract_tokens(evidence) if token in lower))
    return min(1.0, score)


def _fixed_lens_score(question: str, cell: Dict[str, Any], question_type: str, context: Dict[str, Any]) -> float:
    lens_code = str(cell.get("emotion_mode") or "").lower()
    lower = (question or "").lower()
    score = 0.0
    score += min(1.0, sum(0.2 for phrase in FIXED_MATRIX_LENS_HINTS.get(lens_code, []) if phrase in lower))
    bias = str((context.get("normalized_decision_profile") or {}).get("default_decision_bias") or "").lower()
    if bias and bias == lens_code:
        score += 0.2
    question_fit = {
        "cautious": {"threshold": 0.35, "consequence": 0.35, "prioritization": 0.10, "action": 0.15, "missing_data": 0.10, "comparison": 0.05, "meaning": 0.05},
        "strategic": {"comparison": 0.35, "prioritization": 0.35, "action": 0.20, "consequence": 0.15, "meaning": 0.10},
        "decisive": {"action": 0.40, "threshold": 0.20, "prioritization": 0.15, "consequence": 0.15},
        "analytical": {"meaning": 0.35, "missing_data": 0.35, "comparison": 0.20, "threshold": 0.10},
    }
    score += question_fit.get(lens_code, {}).get(question_type, 0.0)
    return min(1.0, score)


def _fixed_perspective_score(question: str, cell: Dict[str, Any], question_type: str, context: Dict[str, Any]) -> float:
    perspective_code = str(cell.get("perspective_code") or "").lower()
    lower = (question or "").lower()
    score = 0.0
    score += min(1.0, sum(0.2 for phrase in FIXED_MATRIX_PERSPECTIVE_HINTS.get(perspective_code, []) if phrase in lower))
    label = str(cell.get("perspective_label") or "").lower()
    score += min(0.5, sum(0.1 for token in _extract_tokens(label) if token in lower))
    for item in cell.get("ranked_visible_data") or []:
        label_tokens = _extract_tokens(str(item.get("label") or ""))
        if question_type == "missing_data" and item.get("type") == "missing_evidence":
            score += 0.25
        if question_type == "threshold" and item.get("type") in {"threshold", "approval_requirement"}:
            score += 0.25
        if question_type == "consequence" and item.get("type") in {"downside", "harm_potential", "trust_impact"}:
            score += 0.25
        if question_type == "comparison" and item.get("type") in {"expected_value", "option_value", "defensibility"}:
            score += 0.2
        if label_tokens and any(token in lower for token in label_tokens):
            score += 0.1
    if any(term in lower for term in ["strategic", "long-term", "optionality", "future", "positioning", "route"]):
        if perspective_code == "business":
            score += 0.25
        if perspective_code == "ethics" and any(term in lower for term in ["governance", "defensible", "approval", "board"]):
            score += 0.15
    if any(term in lower for term in ["trust", "stakeholder", "workforce", "customer", "community", "government"]):
        if perspective_code == "stakeholder":
            score += 0.25
    return min(1.0, score)


def _fixed_persona_alignment(cell: Dict[str, Any], context: Dict[str, Any]) -> float:
    profile = context.get("normalized_decision_profile") or {}
    weights = profile.get("default_perspective_weights") or {}
    perspective_code = str(cell.get("perspective_code") or "")
    base = float(weights.get(perspective_code, 0.25))
    lens_code = str(cell.get("emotion_mode") or "")
    bias = str(profile.get("default_decision_bias") or profile.get("default_emotion_tendency") or "").lower()
    if bias and bias == lens_code:
        base += 0.15
    return min(1.0, max(0.0, base))


def _fixed_question_type_compatibility(cell: Dict[str, Any], question_type: str) -> float:
    ranked_types = [str(item.get("type") or "") for item in (cell.get("ranked_visible_data") or [])]
    if question_type == "missing_data":
        return 1.0 if "missing_evidence" in ranked_types else 0.55
    if question_type == "threshold":
        return 1.0 if any(item in ranked_types for item in {"threshold", "approval_requirement", "time_window"}) else 0.55
    if question_type == "consequence":
        return 1.0 if any(item in ranked_types for item in {"downside", "harm_potential", "trust_impact"}) else 0.55
    if question_type == "comparison":
        return 1.0 if any(item in ranked_types for item in {"expected_value", "option_value", "defensibility"}) else 0.55
    if question_type == "prioritization":
        return 1.0 if ranked_types else 0.50
    if question_type == "meaning":
        return 1.0 if any(item in ranked_types for item in {"confidence", "expected_value", "stakeholder_map"}) else 0.60
    if question_type == "action":
        return 1.0 if any(item in ranked_types for item in {"bottleneck", "time_window", "threshold"}) else 0.65
    return 0.60


def _score_fixed_matrix_cell(question: str, cell: Dict[str, Any], context: Dict[str, Any], question_type: str) -> Dict[str, float]:
    lens = _fixed_lens_score(question, cell, question_type, context)
    perspective = _fixed_perspective_score(question, cell, question_type, context)
    persona = _fixed_persona_alignment(cell, context)
    question_fit = _fixed_question_type_compatibility(cell, question_type)
    visible_data = _fixed_visible_data_fit(question, cell)
    total = (0.30 * lens) + (0.30 * perspective) + (0.20 * persona) + (0.10 * question_fit) + (0.10 * visible_data)
    return {
        "lens": round(lens, 4),
        "perspective": round(perspective, 4),
        "persona": round(persona, 4),
        "question_type": round(question_fit, 4),
        "visible_data": round(visible_data, 4),
        "total": round(total, 4),
    }


def _select_fixed_visible_item(question: str, cell: Dict[str, Any], question_type: str) -> Dict[str, Any]:
    visible_items = list(cell.get("ranked_visible_data") or [])
    if not visible_items:
        return {}
    preferred_types = {
        "threshold": {"threshold", "approval_requirement", "time_window"},
        "consequence": {"downside", "harm_potential", "trust_impact"},
        "missing_data": {"missing_evidence", "confidence"},
        "comparison": {"expected_value", "option_value", "defensibility"},
        "prioritization": {"bottleneck", "expected_value", "downside"},
        "meaning": {"confidence", "expected_value", "stakeholder_map"},
        "action": {"bottleneck", "time_window", "threshold", "reversibility"},
    }.get(question_type, set())
    scored: List[Dict[str, Any]] = []
    for item in visible_items:
        score = float(item.get("score") or 0.0)
        if item.get("type") in preferred_types:
            score += 0.35
        label = str(item.get("label") or "").lower()
        summary = str(item.get("summary") or item.get("preview") or "").lower()
        score += min(0.25, sum(0.05 for token in _extract_tokens(label) if token in (question or "").lower()))
        score += min(0.20, sum(0.04 for token in _extract_tokens(summary) if token in (question or "").lower()))
        scored.append({"item": item, "score": score})
    scored.sort(key=lambda entry: entry["score"], reverse=True)
    return scored[0]["item"]


def _build_fixed_matrix_answer_fields(question: str, cell: Dict[str, Any], context: Dict[str, Any], confidence: float, reason: str) -> Dict[str, Any]:
    question_type = _classify_fixed_question_type(question)
    decision_family = _classify_decision_family(question, context)
    visible_items = cell.get("ranked_visible_data") or []
    top = _select_fixed_visible_item(question, cell, question_type) or (visible_items[0] if visible_items else {})
    lens = cell.get("decision_lens_label") or cell.get("emotion_mode_label") or cell.get("emotion_mode") or "this decision lens"
    perspective = cell.get("perspective_label") or cell.get("perspective_code") or "this perspective"
    cell_face = cell.get("cell_face") or {}
    execution = execute_fixed_matrix_stack(
        question=question,
        question_type=question_type,
        cell=cell,
        normalized_persona=context.get("normalized_decision_profile") or {},
        normalized_scenario=context.get("normalized_scenario_profile") or {},
        confidence=confidence,
        preferred_visible_type=str(top.get("type") or ""),
    )
    framed = _compose_fixed_answer_spine(question, question_type, decision_family, cell, execution, context)
    matched = execution.get("matched_visible_data") or []
    top_label = top.get("label") or cell.get("primary_kpi") or "the strongest decision signal"
    second = matched[1] if len(matched) > 1 else {}
    direct_answer = framed.get("direct_answer") or cell_face.get("decision") or execution.get("recommended_decision") or f"The recommended decision is to prioritize {_lower_first(top_label)} through {lens.lower()} × {perspective.lower()}."
    why = framed.get("why_this_answer") or (
        f"This routes through {lens} × {perspective} because "
        f"{_lower_first(top_label)} is the strongest visible-data match for the question. "
        f"{execution.get('reasoning_summary') or ''}"
    ).strip()
    evidence = _dedupe([
        cell_face.get("value") and f"Matrix value: {cell_face.get('value')}",
        *(execution.get("evidence_used") or []),
        cell.get("decision_style") or "",
        cell.get("rationale") or "",
    ], 6)
    supporting = _dedupe([item.get("label") or "" for item in matched] or [top.get("label") or ""], 4)
    return {
        "decision_family": decision_family,
        "decision_lens": lens,
        "direct_answer": direct_answer,
        "why_this_answer": why,
        "supporting_kpis": supporting,
        "recommended_action": _first_sentence(framed.get("suggested_next_step") or execution.get("suggested_next_step") or ""),
        "primary_risk": _first_sentence(framed.get("decision_risk") or execution.get("decision_risk") or ""),
        "likely_consequence": framed.get("likely_consequence") or _first_sentence(
            cell.get("consequence") or f"{_lower_first(second.get('label') or top_label)} becomes the dominant consequence if the situation deteriorates."
        ),
        "evidence_used": evidence,
        "recommended_decision": _first_sentence(framed.get("recommended_decision") or execution.get("recommended_decision") or direct_answer),
        "decision_risk": _first_sentence(framed.get("decision_risk") or execution.get("decision_risk") or ""),
        "suggested_next_step": _first_sentence(framed.get("suggested_next_step") or execution.get("suggested_next_step") or ""),
        "reasoning_summary": framed.get("reasoning_summary") or execution.get("reasoning_summary") or "",
        "watch_item": framed.get("watch_item") or execution.get("watch_item") or "",
        "missing_data": framed.get("missing_data") or execution.get("missing_data") or "",
        "answer_mode": execution.get("mode") or "direct_recommendation",
        "confidence": confidence,
        "reason": reason,
    }


def _build_direct_answer(question: str, cell: Dict[str, Any], context: Dict[str, Any], decision_family: str) -> str:
    primary_kpi = cell.get("primary_kpi") or "the dominant signal"
    option = cell.get("recommended_action") or cell.get("primary_kpi") or cell.get("perspective_label") or "the recommended route"
    outcome_preference = _classify_outcome_preference(question)
    if decision_family == "variance":
        return f"Your primary variance is {_lower_first(primary_kpi)}."
    if decision_family == "commercial-exposure":
        return f"Your commercial position is most exposed through {_lower_first(primary_kpi)}."
    if decision_family == "contract-entitlement":
        return f"The strongest contract position is the route anchored to {_lower_first(primary_kpi)}."
    if decision_family == "bids-pricing":
        return f"The bid and pricing pressure is concentrated around {_lower_first(primary_kpi)}."
    if decision_family == "disclosure":
        return f"The disclosure decision is best judged through {_lower_first(primary_kpi)}."
    if decision_family == "data-needed":
        return f"The first signal to inspect is {_lower_first(primary_kpi)}."
    if outcome_preference == "worst":
        return f"The worst choice is to lean into the route that leaves Tata most exposed through {_lower_first(primary_kpi)}."
    if outcome_preference == "risky":
        return f"The riskiest route is the one that amplifies downside around {_lower_first(primary_kpi)}."
    if outcome_preference == "moderate":
        return f"The most balanced route is the one that stabilizes {_lower_first(primary_kpi)} without overcommitting."
    if outcome_preference == "strategic":
        return f"The most strategic route is the one that protects the longer-term position around {_lower_first(primary_kpi)}."
    return _first_sentence(option) or f"The best-supported answer is the route anchored to {_lower_first(primary_kpi)}."


def _build_why_this_answer(cell: Dict[str, Any], context: Dict[str, Any], decision_family: str) -> str:
    scenario_title = context.get("scenario_title") or "this scenario"
    perspective = cell.get("perspective_label") or cell.get("perspective_code") or "this perspective"
    lens = cell.get("decision_lens_label") or cell.get("emotion_mode_label") or cell.get("emotion_mode") or "this decision lens"
    primary_kpi = cell.get("primary_kpi") or "the dominant KPI"
    if decision_family == "variance":
        return f"In {scenario_title}, the strongest variance signal for this persona sits in {primary_kpi}, so the answer routes through {lens} × {perspective}."
    if decision_family == "commercial-exposure":
        return f"In {scenario_title}, the strongest commercial exposure clusters around {primary_kpi}, so the answer routes through {lens} × {perspective}."
    if decision_family == "contract-entitlement":
        return f"In {scenario_title}, the strongest entitlement logic sits in the {perspective} perspective and is anchored to {primary_kpi}."
    if decision_family == "bids-pricing":
        return f"In {scenario_title}, the bid and pricing implications are concentrated around {primary_kpi}, so {lens} × {perspective} is the strongest support."
    if decision_family == "disclosure":
        return f"In {scenario_title}, disclosure defensibility is concentrated around {primary_kpi}, making {lens} × {perspective} the best-fit route."
    return f"This answer is grounded in {lens} × {perspective} because the strongest scenario signals are concentrated around {primary_kpi}."


def _build_answer_fields(
    question: str,
    cell: Dict[str, Any],
    context: Dict[str, Any],
    confidence: float,
    reason: str,
) -> Dict[str, Any]:
    decision_family = _classify_decision_family(question, context)
    return {
        "decision_family": decision_family,
        "decision_lens": cell.get("decision_lens_label") or cell.get("emotion_mode_label") or cell.get("emotion_mode"),
        "direct_answer": _build_direct_answer(question, cell, context, decision_family),
        "why_this_answer": _build_why_this_answer(cell, context, decision_family),
        "supporting_kpis": _dedupe([cell.get("primary_kpi") or "", *(cell.get("supporting_kpis") or [])], 4),
        "recommended_action": _first_sentence(cell.get("recommended_action") or ""),
        "primary_risk": _first_sentence(cell.get("risk") or ""),
        "likely_consequence": _first_sentence(cell.get("consequence") or ""),
        "evidence_used": _build_evidence_used(cell, context),
        "confidence": confidence,
        "reason": reason,
    }


def _build_question_for_cell(cell: Dict[str, Any], context: Dict[str, Any], family: str) -> str:
    persona_role = context.get("persona_role") or "this persona"
    scenario_title = context.get("scenario_title") or "this scenario"
    perspective = cell.get("perspective_label") or cell.get("perspective_code") or "this perspective"
    primary_kpi = (cell.get("primary_kpi") or "this KPI").strip()
    primary_kpi_lower = primary_kpi[:1].lower() + primary_kpi[1:] if primary_kpi else "this KPI"
    kind = _perspective_kind(perspective)

    if family == "data":
        return f"Which data should {persona_role} inspect first before acting on {primary_kpi_lower} in {scenario_title}?"
    if family == "threshold":
        return f"At what point does {primary_kpi_lower} become the trigger to change course in {scenario_title}?"
    if family == "stakeholder":
        return f"Who should {persona_role} tell first if {primary_kpi_lower} worsens in {scenario_title}?"
    if family == "risk":
        return f"What is the dominant downside if Tata waits on {primary_kpi_lower} in {scenario_title}?"

    if kind == "schedule":
        return f"What is the safest schedule-recovery path if {primary_kpi_lower} deteriorates in {scenario_title}?"
    if kind == "financial":
        return f"What is the most financially defensible move if {primary_kpi_lower} worsens in {scenario_title}?"
    if kind == "people":
        return f"What is the most defensible stakeholder path if {primary_kpi_lower} becomes harder to manage in {scenario_title}?"
    if kind == "commercial":
        return f"What is the best commercial move if {primary_kpi_lower} comes under pressure in {scenario_title}?"
    return f"What is the best path through the {perspective} lens in {scenario_title}?"


def _select_distinct_cells(context: Dict[str, Any], ranked_cells: List[Dict[str, Any]], limit: int = 4) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    seen_perspectives = set()
    for item in ranked_cells:
        cell = item.get("cell") if isinstance(item, dict) else item
        if not cell:
            continue
        perspective = cell.get("perspective_label") or cell.get("perspective_code")
        if perspective and perspective in seen_perspectives:
            continue
        chosen.append(cell)
        if perspective:
            seen_perspectives.add(perspective)
        if len(chosen) >= limit:
            break
    if chosen:
        return chosen
    return (context.get("matrix_cells") or [])[:limit]


def _build_broad_suggestions(context: Dict[str, Any], question: str = "") -> List[str]:
    cells = _select_distinct_cells(context, context.get("matrix_cells") or [], 4)
    families = _detect_question_families(question)
    if not families:
        families = ["action", "risk", "stakeholder", "threshold"]
    suggestions = []
    for index, cell in enumerate(cells):
        family = families[index % len(families)] if families else "action"
        kind = _perspective_kind(cell.get("perspective_label") or "")
        if family == "action" and kind == "financial" and "risk" not in families:
            family = "risk"
        if family == "financial" and kind != "financial":
            family = "threshold" if kind == "schedule" else "risk"
        if family == "commercial" and kind != "commercial":
            family = "action"
        suggestions.append(_build_question_for_cell(cell, context, family))
    return _dedupe(suggestions, 5)


def _build_follow_ups(cell: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    if not cell:
        return []
    perspectives = context.get("perspectives", [])
    modes = context.get("emotion_modes", [])
    current_perspective = cell.get("perspective_label") or cell.get("perspective_code")
    current_mode = cell.get("emotion_mode_label") or cell.get("emotion_mode")
    other_perspective = next((item["label"] for item in perspectives if item.get("label") != current_perspective), None)
    other_mode = next((item["label"] for item in modes if item.get("label") != current_mode), None)
    primary_kpi = cell.get("primary_kpi") or "this signal"
    kind = _perspective_kind(current_perspective or "")
    risk_follow_up = f"What becomes the dominant risk if Tata waits 14 more days on {primary_kpi.lower()}?"
    threshold_follow_up = f"At what point does {primary_kpi.lower()} become the trigger to change course?"
    if kind == "financial":
        risk_follow_up = f"What happens to contingency and exposure if Tata waits on {primary_kpi.lower()}?"
        threshold_follow_up = f"At what point does {primary_kpi.lower()} become a board-level financial trigger?"
    elif kind == "people":
        risk_follow_up = f"Who becomes the next stakeholder risk if Tata waits on {primary_kpi.lower()}?"
        threshold_follow_up = f"When does {primary_kpi.lower()} become a disclosure or governance trigger?"
    elif kind == "commercial":
        risk_follow_up = f"What commercial downside grows first if Tata waits on {primary_kpi.lower()}?"
        threshold_follow_up = f"When does {primary_kpi.lower()} force a customer or counterparty decision?"
    return _dedupe([
        f"How does this look from the {other_perspective} perspective instead?" if other_perspective else "",
        f"What changes if this is viewed through {other_mode} instead of {current_mode}?" if other_mode and current_mode else "",
        risk_follow_up,
        f"Which additional data would confirm this recommendation for {primary_kpi.lower()}?",
        threshold_follow_up,
    ], 5)


def _detect_question_families(question: str) -> List[str]:
    lower = (question or "").lower()
    families: List[str] = []
    intent = _classify_intent(question)
    intent_map = {
        "threshold": "threshold",
        "probability": "data",
        "comparison": "action",
        "legal_trigger": "stakeholder",
        "reversibility": "threshold",
        "stakeholder_signal": "stakeholder",
        "cost_of_delay": "risk",
        "action_selection": "action",
        "consequence": "risk",
        "sequencing": "stakeholder",
        "data": "data",
    }
    mapped = intent_map.get(intent)
    if mapped:
        families.append(mapped)
    if any(term in lower for term in ["risk", "downside", "exposure", "danger", "slip"]):
        families.append("risk")
    if any(term in lower for term in ["data", "evidence", "kpi", "metric", "prove", "confirm"]):
        families.append("data")
    if any(term in lower for term in ["when", "threshold", "trigger", "point", "deadline"]):
        families.append("threshold")
    if any(term in lower for term in ["tell", "notify", "disclose", "announce", "who should know"]):
        families.append("stakeholder")
    families.append("action")
    return _dedupe(families, 4)


def _build_recovery_suggestions(question: str, context: Dict[str, Any]) -> List[str]:
    ranked = sorted(
        [{"cell": cell, "score": _score_cell(question, cell, context)} for cell in (context.get("matrix_cells") or [])],
        key=lambda item: item["score"],
        reverse=True,
    )
    cells = _select_distinct_cells(context, ranked, 4)
    families = _detect_question_families(question)
    suggestions = []
    for index, cell in enumerate(cells):
        family = families[index % len(families)] if families else "action"
        suggestions.append(_build_question_for_cell(cell, context, family))
    if len(suggestions) < 4:
        suggestions.extend(_build_broad_suggestions(context))
    return _dedupe(suggestions, 5)


def _build_clarification(top: Dict[str, Any], second: Optional[Dict[str, Any]]) -> str:
    if not top or not second:
        return "Do you want the answer from a different perspective or emotional mode?"
    if top.get("perspective_label") != second.get("perspective_label"):
        return f"Do you want the answer from the {top.get('perspective_label')} lens or the {second.get('perspective_label')} lens?"
    if top.get("emotion_mode_label") != second.get("emotion_mode_label"):
        return f"Do you want the {top.get('emotion_mode_label')} view or the {second.get('emotion_mode_label')} view?"
    return "Do you want the safest path, the most defensible path, or the fastest path?"


def _explicit_perspective_score(question: str, cell: Dict[str, Any]) -> float:
    lower = (question or "").lower()
    label = cell.get("perspective_label") or ""
    terms = [label, *(cell.get("question_tags") or []), *(cell.get("supporting_kpis") or [])]
    score = 0.0
    for term in terms:
        term_lower = str(term or "").lower()
        if not term_lower:
            continue
        if term_lower in lower:
            score += 10.0 if term_lower == label.lower() else 3.0
    return score


def _explicit_emotion_score(question: str, cell: Dict[str, Any]) -> float:
    lower = (question or "").lower()
    label = str(cell.get("emotion_mode_label") or "").lower()
    mode = str(cell.get("emotion_mode") or "").lower()
    terms = [label, mode]
    score = 0.0
    for term in terms:
        if term and term in lower:
            score += 10.0 if term == label else 4.0
    return score


def _explicit_kpi_score(question: str, cell: Dict[str, Any]) -> float:
    lower = (question or "").lower()
    kpis = _dedupe([
        *(cell.get("supporting_kpis") or []),
        cell.get("primary_kpi") or "",
        *(cell.get("question_tags") or []),
    ], 24)
    score = 0.0
    for kpi in kpis:
        kpi_lower = str(kpi or "").lower().strip()
        if not kpi_lower:
            continue
        if kpi_lower in lower:
            score += 18.0
            continue
        parts = [part for part in kpi_lower.replace("/", " ").split() if len(part) > 3]
        overlap = sum(1 for part in parts if part in lower)
        if overlap >= 2:
            score += overlap * 4.0
    return score


def _extract_matrix_constraints(question: str, cells: List[Dict[str, Any]]) -> Dict[str, set]:
    lower = (question or "").lower()
    perspective_matches = set()
    emotion_matches = set()
    for cell in cells:
        perspective_terms = _dedupe([
            cell.get("perspective_label") or "",
            *(cell.get("supporting_kpis") or []),
            cell.get("primary_kpi") or "",
            *(cell.get("question_tags") or []),
        ], 28)
        if any(str(term or "").lower() in lower for term in perspective_terms if str(term or "").strip()):
            if cell.get("perspective_code"):
                perspective_matches.add(cell.get("perspective_code"))
            if cell.get("perspective_label"):
                perspective_matches.add(cell.get("perspective_label"))

        emotion_terms = _dedupe([
            cell.get("emotion_mode_label") or "",
            cell.get("emotion_mode") or "",
        ], 12)
        if any(str(term or "").lower() in lower for term in emotion_terms if str(term or "").strip()):
            if cell.get("emotion_mode"):
                emotion_matches.add(cell.get("emotion_mode"))
            if cell.get("emotion_mode_label"):
                emotion_matches.add(cell.get("emotion_mode_label"))

    return {
        "perspective": perspective_matches,
        "emotion": emotion_matches,
    }


def _apply_matrix_constraints(ranked: List[Dict[str, Any]], constraints: Dict[str, set]) -> List[Dict[str, Any]]:
    filtered = ranked
    if constraints.get("perspective"):
        perspective_filtered = [
            item for item in filtered
            if item["cell"].get("perspective_code") in constraints["perspective"]
            or item["cell"].get("perspective_label") in constraints["perspective"]
        ]
        if perspective_filtered:
            filtered = perspective_filtered
    if constraints.get("emotion"):
        emotion_filtered = [
            item for item in filtered
            if item["cell"].get("emotion_mode") in constraints["emotion"]
            or item["cell"].get("emotion_mode_label") in constraints["emotion"]
        ]
        if emotion_filtered:
            filtered = emotion_filtered
    return filtered


def _infer_preferred_perspective(question: str, ranked: List[Dict[str, Any]], intent: str) -> Optional[str]:
    scores: Dict[str, float] = {}
    for item in ranked:
        cell = item["cell"]
        key = cell.get("perspective_code") or cell.get("perspective_label")
        if not key:
            continue
        score = _explicit_perspective_score(question, cell) + _explicit_kpi_score(question, cell)
        kind = _perspective_kind(cell.get("perspective_label") or "")
        lower = (question or "").lower()
        if intent in {"stakeholder_signal", "sequencing"} and kind == "people":
            score += 8
        elif intent in {"timing", "cost_of_delay"} and kind == "schedule":
            score += 8
        elif intent in {"comparison", "reversibility"} and kind == "commercial":
            score += 6
        elif intent in {"threshold", "legal_trigger"} and kind == "financial":
            score += 6
        elif intent == "kpi_lookup" and any(term in lower for term in ["commercial", "supplier", "customer", "contract"]) and kind == "commercial":
            score += 8
        scores[key] = max(scores.get(key, 0.0), score)
    ranked_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked_scores or ranked_scores[0][1] <= 0:
        return None
    if len(ranked_scores) == 1 or ranked_scores[0][1] - ranked_scores[1][1] >= 3:
        return ranked_scores[0][0]
    return None


def _infer_preferred_mode(question: str, ranked: List[Dict[str, Any]], intent: str) -> Optional[str]:
    scores: Dict[str, float] = {}
    lower = (question or "").lower()
    for item in ranked:
        cell = item["cell"]
        key = cell.get("emotion_mode") or cell.get("emotion_mode_label")
        if not key:
            continue
        score = _explicit_emotion_score(question, cell)
        mode_terms = _dedupe([
            cell.get("emotion_mode_label") or "",
            cell.get("emotion_mode") or "",
        ], 10)
        score += sum(2.0 for term in mode_terms if str(term or "").lower() in lower)
        if intent == "stakeholder_signal" and any(term in lower for term in ["stakeholder", "relationship", "signal", "tell first", "who should know"]):
            if any(term in str(cell.get("emotion_mode_label") or "").lower() for term in ["alignment", "relationship", "signal"]):
                score += 8
        if intent == "risk" and any(term in str(cell.get("emotion_mode_label") or "").lower() for term in ["downside", "safety", "regret"]):
            score += 6
        if intent == "timing" and any(term in str(cell.get("emotion_mode_label") or "").lower() for term in ["speed", "checkpoint", "indicator"]):
            score += 6
        scores[key] = max(scores.get(key, 0.0), score)
    ranked_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked_scores or ranked_scores[0][1] <= 0:
        return None
    if len(ranked_scores) == 1 or ranked_scores[0][1] - ranked_scores[1][1] >= 3:
        return ranked_scores[0][0]
    return None


def _apply_semantic_preferences(question: str, ranked: List[Dict[str, Any]], intent: str) -> List[Dict[str, Any]]:
    filtered = ranked
    preferred_perspective = _infer_preferred_perspective(question, filtered, intent)
    if preferred_perspective:
        perspective_filtered = [
            item for item in filtered
            if item["cell"].get("perspective_code") == preferred_perspective
            or item["cell"].get("perspective_label") == preferred_perspective
        ]
        if perspective_filtered:
            filtered = perspective_filtered
    preferred_mode = _infer_preferred_mode(question, filtered, intent)
    if preferred_mode:
        mode_filtered = [
            item for item in filtered
            if item["cell"].get("emotion_mode") == preferred_mode
            or item["cell"].get("emotion_mode_label") == preferred_mode
        ]
        if mode_filtered:
            filtered = mode_filtered
    return filtered


def _resolve_framework_intersection(ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    perspective_scores: Dict[str, float] = {}
    mode_scores: Dict[str, float] = {}
    for item in ranked:
        cell = item["cell"]
        perspective_key = cell.get("perspective_code") or cell.get("perspective_label")
        mode_key = cell.get("emotion_mode") or cell.get("emotion_mode_label")
        if perspective_key:
            perspective_scores[perspective_key] = max(perspective_scores.get(perspective_key, 0.0), item["score"])
        if mode_key:
            mode_scores[mode_key] = max(mode_scores.get(mode_key, 0.0), item["score"])

    preferred_perspective = max(perspective_scores.items(), key=lambda item: item[1])[0] if perspective_scores else None
    preferred_mode = max(mode_scores.items(), key=lambda item: item[1])[0] if mode_scores else None
    if not preferred_perspective and not preferred_mode:
        return ranked

    intersected = [
        item for item in ranked
        if (
            not preferred_perspective
            or item["cell"].get("perspective_code") == preferred_perspective
            or item["cell"].get("perspective_label") == preferred_perspective
        ) and (
            not preferred_mode
            or item["cell"].get("emotion_mode") == preferred_mode
            or item["cell"].get("emotion_mode_label") == preferred_mode
        )
    ]
    return intersected or ranked


def _score_cell(question: str, cell: Dict[str, Any], context: Dict[str, Any]) -> float:
    lower = (question or "").lower()
    tokens = set(_extract_tokens(lower))
    intent = _classify_intent(question)
    outcome_preference = _classify_outcome_preference(question)
    broad_question = _is_broad_question(question)
    haystack_parts = [
        cell.get("cell_id"),
        cell.get("emotion_mode"),
        cell.get("emotion_mode_label"),
        cell.get("perspective_code"),
        cell.get("perspective_label"),
        cell.get("primary_kpi"),
        *(cell.get("supporting_kpis") or []),
        cell.get("recommended_action"),
        cell.get("risk"),
        cell.get("consequence"),
        *(cell.get("question_tags") or []),
    ]
    haystack = " ".join(str(item or "") for item in haystack_parts).lower()
    score = 0.0
    decision_weight = float(cell.get("decision_weight") or 0.0)
    score += sum(1.0 for token in tokens if token in haystack)
    score += min(decision_weight / 8.0, 8.0)
    if broad_question:
        score += min(decision_weight / 4.0, 12.0)
    perspective_kind = _perspective_kind(cell.get("perspective_label") or "")
    risk_text = f"{cell.get('risk') or ''} {cell.get('consequence') or ''} {cell.get('question_tags') or ''}".lower()
    risk_severity = 0.0
    if any(term in risk_text for term in ["critical", "clawback", "breach", "halt", "irreversible", "unacceptable", "suspension", "damage", "loss", "exposure", "slip", "political"]):
        risk_severity += 8.0
    if any(term in str(cell.get("emotion_mode_label") or "").lower() for term in ["downside", "safety", "regret", "risk"]):
        risk_severity += 4.0
    strategic_strength = 0.0
    strategic_text = f"{cell.get('emotion_mode_label') or ''} {cell.get('recommended_action') or ''} {cell.get('question_tags') or ''}".lower()
    if context.get("framework_code") == "B":
        strategic_strength += 3.0
    if any(term in strategic_text for term in ["long-horizon", "long horizon", "optionality", "future", "precedent", "institutional", "second-order", "thesis"]):
        strategic_strength += 8.0
    moderation_strength = 0.0
    moderate_text = f"{cell.get('recommended_action') or ''} {cell.get('question_tags') or ''}".lower()
    if any(term in moderate_text for term in ["hybrid", "phased", "joint", "balanced", "time-limited", "minimum", "continuity", "feasible", "measured", "bridge"]):
        moderation_strength += 8.0
    score += _explicit_perspective_score(question, cell)
    score += _explicit_emotion_score(question, cell)
    score += _explicit_kpi_score(question, cell)

    if "commercial/strategic" in lower and cell.get("perspective_code") in {"P4", "comm"}:
        score += 8
    if "financial" in lower and cell.get("perspective_code") in {"P2", "fin"}:
        score += 8
    if any(term in lower for term in ["people/political", "people", "political", "stakeholder"]) and cell.get("perspective_code") in {"P3", "people"}:
        score += 8
    if any(term in lower for term in ["schedule/delivery", "schedule", "delivery"]) and cell.get("perspective_code") in {"P1", "sched"}:
        score += 8

    if any(term in lower for term in ["safest", "safe", "defensible", "downside"]) and cell.get("emotion_mode") == "A":
        score += 6
    if any(term in lower for term in ["strategic", "long-term", "optionality", "precedent"]) and cell.get("emotion_mode") == "B":
        score += 6
    if any(term in lower for term in ["diplomatic", "stakeholder", "who should know", "tell first"]) and cell.get("emotion_mode") == "C":
        score += 6
    if any(term in lower for term in ["now", "immediately", "fastest", "next move"]) and cell.get("emotion_mode") == "D":
        score += 6

    if intent == "kpi_lookup":
        primary = _normalize_kpi_text(cell.get("primary_kpi") or "")
        scenario_kpis = context.get("scenario_kpis") or []
        for index, item in enumerate(scenario_kpis):
            label = _normalize_kpi_text(item.get("label") if isinstance(item, dict) else str(item))
            code = _normalize_kpi_text(item.get("code") if isinstance(item, dict) else "")
            if label and (primary in label or label in primary or (code and code in primary)):
                score += {0: 14, 1: 10, 2: 7, 3: 5}.get(index, 0)
                break
        if "variance" in lower:
            if perspective_kind in {"schedule", "financial", "commercial"}:
                score += 6
            if any(term in haystack for term in ["variance", "contingency", "grant", "schedule", "scope change", "offtake", "revenue"]):
                score += 8
        if any(term in lower for term in ["commercials", "commercial position", "commercial exposure", "contract exposure"]):
            if perspective_kind == "commercial":
                score += 10
            if any(term in haystack for term in ["customer", "offtake", "revenue", "commercial", "contract"]):
                score += 8
    elif intent == "threshold":
        if perspective_kind in {"financial", "schedule"}:
            score += 6
        if cell.get("emotion_mode") == "A":
            score += 4
    elif intent == "probability":
        if perspective_kind in {"financial", "schedule"}:
            score += 5
    elif intent == "comparison":
        if perspective_kind == "commercial":
            score += 6
        if cell.get("emotion_mode") == "B":
            score += 4
    elif intent == "legal_trigger":
        if perspective_kind in {"financial", "people"}:
            score += 7
        if cell.get("emotion_mode") in {"A", "C"}:
            score += 3
    elif intent == "reversibility":
        if cell.get("emotion_mode") == "B":
            score += 6
        if perspective_kind in {"commercial", "schedule"}:
            score += 4
    elif intent == "stakeholder_signal":
        if perspective_kind == "people":
            score += 8
        if cell.get("emotion_mode") == "C":
            score += 5
    elif intent == "cost_of_delay":
        if perspective_kind == "schedule":
            score += 7
        if cell.get("emotion_mode") in {"A", "D"}:
            score += 3
    elif intent == "action_selection":
        if cell.get("emotion_mode") in {"A", "B"}:
            score += 3
    elif intent == "consequence":
        if perspective_kind in {"people", "commercial"}:
            score += 4
    elif intent == "sequencing":
        if perspective_kind == "people":
            score += 6
        if cell.get("emotion_mode") == "D":
            score += 2
    elif intent == "data":
        if perspective_kind in {"financial", "schedule"}:
            score += 4

    if outcome_preference == "best":
        score += decision_weight * 0.6 + strategic_strength * 0.5 - risk_severity * 0.25
    elif outcome_preference == "worst":
        score += risk_severity * 1.4 + max(0.0, 12.0 - decision_weight * 0.25)
    elif outcome_preference == "risky":
        score += risk_severity * 1.1 - decision_weight * 0.1
    elif outcome_preference == "moderate":
        score += moderation_strength * 1.2 + max(0.0, 8.0 - abs(decision_weight - 14.0))
    elif outcome_preference == "strategic":
        score += strategic_strength * 1.4 + decision_weight * 0.2

    current_framework = context.get("framework_code")
    if current_framework and current_framework == cell.get("emotion_mode"):
        score += 1.5
    current_active = context.get("active_cell_id")
    if current_active and current_active == cell.get("cell_id"):
        score += 0.5
    return score


def _fallback_route(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    question = (question or "").strip()
    intent = _classify_intent(question)
    broad_question = _is_broad_question(question)
    decision_family = _classify_decision_family(question, context)

    cells = context.get("matrix_cells") or []
    if not cells:
        return {
            "mode": "suggest",
            "decision_family": decision_family,
            "decision_lens": None,
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.0,
            "reason": "No matrix cells were available for this scenario.",
            "direct_answer": "",
            "why_this_answer": "",
            "supporting_kpis": [],
            "recommended_action": "",
            "primary_risk": "",
            "likely_consequence": "",
            "evidence_used": [],
            "clarifying_question": None,
            "suggested_questions": [],
            "follow_up_questions": [],
        }

    if _uses_fixed_matrix(context):
        question_type = _classify_fixed_question_type(question)
        ranked_fixed = sorted(
            [{"cell": cell, "score": _score_fixed_matrix_cell(question, cell, context, question_type)} for cell in cells],
            key=lambda item: (
                item["score"]["total"],
                item["score"]["visible_data"],
                float(item["cell"].get("decision_weight") or 0.0),
            ),
            reverse=True,
        )
        top = ranked_fixed[0]
        cell = top["cell"]
        confidence = min(0.94, 0.52 + top["score"]["total"] * 0.42)
        reason = (
            f"Matched {cell.get('decision_lens_label') or cell.get('emotion_mode_label') or cell.get('emotion_mode')} × "
            f"{cell.get('perspective_label')} using fixed-matrix scoring "
            f"(lens {top['score']['lens']:.2f}, perspective {top['score']['perspective']:.2f}, "
            f"persona {top['score']['persona']:.2f}, question-type {top['score']['question_type']:.2f}, "
            f"visible-data {top['score']['visible_data']:.2f})."
        )
        answer_fields = _build_fixed_matrix_answer_fields(question, cell, context, confidence, reason)
        top_visible = [item.get("label") for item in (cell.get("ranked_visible_data") or [])[:2] if item.get("label")]
        follow_ups = _dedupe([
            f"What is the biggest downside through the {cell.get('perspective_label')} perspective?",
            f"What is the trigger point through the {cell.get('decision_lens_label') or cell.get('emotion_mode_label')} lens?",
            f"What evidence would confirm {_lower_first(top_visible[0])}?" if top_visible else "",
            f"What is the next step if {_lower_first(top_visible[1])} worsens?" if len(top_visible) > 1 else "",
        ], 4)
        return {
            "mode": "answer",
            **answer_fields,
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": cell.get("emotion_mode"),
            "perspective_code": cell.get("perspective_code"),
            "target_cell_id": cell.get("cell_id"),
            "clarifying_question": None,
            "suggested_questions": [],
            "follow_up_questions": follow_ups,
        }

    ranked = sorted(
        [{"cell": cell, "score": _score_cell(question, cell, context)} for cell in cells],
        key=lambda item: (
            item["score"],
            _explicit_kpi_score(question, item["cell"]),
            float(item["cell"].get("decision_weight") or 0.0),
        ),
        reverse=True,
    )
    ranked = _apply_matrix_constraints(ranked, _extract_matrix_constraints(question, cells))
    ranked = _apply_semantic_preferences(question, ranked, intent)
    ranked = _resolve_framework_intersection(ranked)
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    gap = top["score"] - (second["score"] if second else 0)
    if intent == "kpi_lookup" and top["score"] < 4:
        return {
            "mode": "clarify",
            "decision_family": decision_family,
            "decision_lens": None,
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.35,
            "reason": "I can answer this, but I need to know which kind of variance or exposure you mean.",
            "direct_answer": "",
            "why_this_answer": "",
            "supporting_kpis": [],
            "recommended_action": "",
            "primary_risk": "",
            "likely_consequence": "",
            "evidence_used": [],
            "clarifying_question": "Do you mean schedule variance, financial variance, people/governance exposure, or contract/commercial variance?",
            "suggested_questions": _dedupe([
                "What is my schedule variance in this scenario?",
                "What is my financial variance in this scenario?",
                "What is my contract/commercial variance in this scenario?",
            ], 3),
            "follow_up_questions": [],
        }

    if top["score"] < 4:
        if broad_question:
            persona_role = context.get("persona_role", "this persona")
            labels = [item.get("label", "") for item in context.get("perspectives", [])]
            prompt = "That question is too broad for this scenario."
            if labels:
                prompt += f" For {persona_role}, do you want to explore it from the {', '.join(labels).replace(', ' + labels[-1], ', or ' + labels[-1]) if len(labels) > 1 else labels[0]} perspective?"
            return {
                "mode": "suggest",
                "decision_family": decision_family,
                "decision_lens": None,
                "persona_id": context.get("persona_id"),
                "scenario_id": context.get("scenario_id"),
                "framework_code": context.get("framework_code"),
                "emotion_mode": None,
                "perspective_code": None,
                "target_cell_id": None,
                "confidence": 0.15,
                "reason": prompt,
                "direct_answer": "",
                "why_this_answer": "",
                "supporting_kpis": [],
                "recommended_action": "",
                "primary_risk": "",
                "likely_consequence": "",
                "evidence_used": [],
                "clarifying_question": None,
                "suggested_questions": _build_broad_suggestions(context, question),
                "follow_up_questions": [],
            }
        return {
            "mode": "suggest",
            "decision_family": decision_family,
            "decision_lens": None,
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.2,
            "reason": "That question is too broad for this scenario. Try one of these instead.",
            "direct_answer": "",
            "why_this_answer": "",
            "supporting_kpis": [],
            "recommended_action": "",
            "primary_risk": "",
            "likely_consequence": "",
            "evidence_used": [],
            "clarifying_question": None,
            "suggested_questions": _build_recovery_suggestions(question, context),
            "follow_up_questions": [],
        }

    if gap < 2:
        if intent == "kpi_lookup":
            return {
                "mode": "clarify",
                "decision_family": decision_family,
                "decision_lens": None,
                "persona_id": context.get("persona_id"),
                "scenario_id": context.get("scenario_id"),
                "framework_code": context.get("framework_code"),
                "emotion_mode": None,
                "perspective_code": None,
                "target_cell_id": None,
                "confidence": 0.45,
                "reason": "Your question maps to more than one plausible variance signal in this scenario.",
                "direct_answer": "",
                "why_this_answer": "",
                "supporting_kpis": [],
                "recommended_action": "",
                "primary_risk": "",
                "likely_consequence": "",
                "evidence_used": [],
                "clarifying_question": "Do you mean schedule variance, financial variance, people/governance exposure, or contract/commercial variance?",
                "suggested_questions": _dedupe([
                    f"What is my variance from the {top['cell'].get('perspective_label')} perspective?",
                    f"What is my variance from the {second['cell'].get('perspective_label')} perspective?" if second else "",
                ], 3),
                "follow_up_questions": [],
            }
        return {
            "mode": "clarify",
            "decision_family": decision_family,
            "decision_lens": None,
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.45,
            "reason": "The question could map to more than one matrix cell.",
            "direct_answer": "",
            "why_this_answer": "",
            "supporting_kpis": [],
            "recommended_action": "",
            "primary_risk": "",
            "likely_consequence": "",
            "evidence_used": [],
            "clarifying_question": _build_clarification(top["cell"], second["cell"] if second else None),
            "suggested_questions": _dedupe([
                f"What is the right path through the {top['cell'].get('perspective_label')} perspective?",
                f"What is the right path through the {second['cell'].get('perspective_label')} perspective?" if second else "",
            ], 3),
            "follow_up_questions": [],
        }

    cell = top["cell"]
    if broad_question:
        confidence = min(0.55, 0.28 + min(top["score"], 10) * 0.02)
        reason = f"Broad question. I selected the best-fit current outcome from {cell.get('emotion_mode_label') or cell.get('emotion_mode')} × {cell.get('perspective_label')} based on the strongest scenario signals."
        answer_fields = _build_answer_fields(question, cell, context, confidence, reason)
        return {
            "mode": "answer",
            **answer_fields,
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": cell.get("emotion_mode"),
            "perspective_code": cell.get("perspective_code"),
            "target_cell_id": cell.get("cell_id"),
            "clarifying_question": None,
            "suggested_questions": [],
            "follow_up_questions": _build_broad_suggestions(context, question),
        }
    confidence = min(0.9, 0.55 + min(top["score"], 10) * 0.03)
    reason = f"Matched {cell.get('emotion_mode_label') or cell.get('emotion_mode')} × {cell.get('perspective_label')} based on the strongest scenario and KPI overlap."
    answer_fields = _build_answer_fields(question, cell, context, confidence, reason)
    return {
        "mode": "answer",
        **answer_fields,
        "persona_id": context.get("persona_id"),
        "scenario_id": context.get("scenario_id"),
        "framework_code": context.get("framework_code"),
        "emotion_mode": cell.get("emotion_mode"),
        "perspective_code": cell.get("perspective_code"),
        "target_cell_id": cell.get("cell_id"),
        "clarifying_question": None,
        "suggested_questions": [],
        "follow_up_questions": _build_follow_ups(cell, context),
    }


def _build_system_prompt() -> str:
    return (
        "You are a constrained decision-matrix routing engine. "
        "You receive one active scenario context, one active persona, visible matrix rows, visible matrix columns, "
        "and a compact inventory of matrix cells. "
        "In this app, matrix rows are called Decision Lenses and matrix columns are called Perspectives. "
        "Some scenarios use a fixed 4x4 decision framework with ranked visible-data summaries per cell; when uses_fixed_matrix=true, "
        "route by question type, decision lens, perspective, and visible-data fit, and always return exactly one answer cell. "
        "Treat user phrases like 'through the <decision lens>', 'from the <perspective>', 'using the <lens>', "
        "or 'under the <perspective>' as explicit routing signals. "
        "You must choose exactly one mode: answer, clarify, or suggest. "
        "Rules: "
        "1. Stay inside the provided scenario context. Do not invent scenarios, personas, KPIs, or cells. "
        "2. First classify the question into one intent: kpi_lookup, threshold, probability, comparison, legal_trigger, reversibility, stakeholder_signal, cost_of_delay, action_selection, consequence, sequencing, or data. "
        "2b. Also detect whether the user is asking for a best, worst, risky, moderate, or strategic choice, and use that as an outcome preference when selecting the target cell. "
        "3. If the question maps clearly to one cell, return mode=answer with the exact target_cell_id from the inventory. "
        "When mode=answer, also return decision_family, decision_lens, direct_answer, why_this_answer, supporting_kpis, recommended_action, primary_risk, likely_consequence, and evidence_used. "
        "Also return recommended_decision, decision_risk, suggested_next_step, reasoning_summary, watch_item, missing_data, and answer_mode when possible. "
        "If the question explicitly names a Decision Lens or Perspective that exists in the provided matrix, constrain routing to matching cells first. "
        "4. If one important distinction is missing, return mode=clarify with exactly one short clarifying question. "
        "5. If the question is too broad or malformed, return mode=suggest with 3 to 5 better scenario-specific questions. "
        "6. Treat shorthand executive questions like 'what is my variance' or 'what is my commercial position' as kpi_lookup queries, not as broad generic prompts. Answer directly if one dominant KPI is clear; otherwise ask one short clarification. "
        "7. When returning suggested_questions or follow_up_questions, make them varied across perspective, intent, and decision angle. "
        "Do not return five versions of the same 'best path' question. Use a mix of action, risk, data, threshold, and stakeholder prompts when relevant. "
        "8. Use the matrix cells as the answer surface. Do not invent new cells or new KPIs. "
        "9. Use the active scenario decision context and commercial logic to reason about contracts, commercials, variance, bids/pricing, compliance, and disclosure. "
        "10. Return valid JSON only."
    )


def _build_user_payload(question: str, context: Dict[str, Any], clarification_context: Optional[Dict[str, Any]]) -> str:
    compact = {
        "question": question,
        "active_context": {
            "persona_id": context.get("persona_id"),
            "persona_role": context.get("persona_role"),
            "scenario_id": context.get("scenario_id"),
            "scenario_title": context.get("scenario_title"),
            "scenario_summary": context.get("scenario_summary"),
            "scenario_decision_context": context.get("scenario_decision_context"),
            "scenario_kpis": context.get("scenario_kpis", []),
            "persona_tension": context.get("persona_tension"),
            "framework_code": context.get("framework_code"),
            "assistant_mode": context.get("assistant_mode", "scenario-only"),
        },
        "commercial_logic": context.get("commercial_logic") or {},
        "visible_perspectives": context.get("perspectives", []),
        "visible_decision_lenses": context.get("emotion_modes", []),
        "visible_emotion_modes": context.get("emotion_modes", []),
        "matrix_cells": context.get("matrix_cells", []),
        "clarification_context": clarification_context,
            "required_output_keys": [
            "mode",
            "decision_family",
            "decision_lens",
            "persona_id",
            "scenario_id",
            "framework_code",
            "emotion_mode",
            "perspective_code",
            "target_cell_id",
            "confidence",
            "reason",
            "direct_answer",
            "why_this_answer",
            "supporting_kpis",
            "recommended_action",
            "primary_risk",
            "likely_consequence",
                "evidence_used",
                "recommended_decision",
                "decision_risk",
                "suggested_next_step",
                "reasoning_summary",
                "watch_item",
                "missing_data",
                "answer_mode",
                "clarifying_question",
                "suggested_questions",
                "follow_up_questions",
        ],
    }
    return json.dumps(compact, ensure_ascii=True)


def _router_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "mode": {"type": "string", "enum": ["answer", "clarify", "suggest"]},
            "decision_family": {"type": ["string", "null"]},
            "decision_lens": {"type": ["string", "null"]},
            "persona_id": {"type": ["string", "null"]},
            "scenario_id": {"type": ["string", "null"]},
            "framework_code": {"type": ["string", "null"]},
            "emotion_mode": {"type": ["string", "null"]},
            "perspective_code": {"type": ["string", "null"]},
            "target_cell_id": {"type": ["string", "null"]},
            "confidence": {"type": "number"},
            "reason": {"type": "string"},
            "direct_answer": {"type": ["string", "null"]},
            "why_this_answer": {"type": ["string", "null"]},
            "supporting_kpis": {"type": "array", "items": {"type": "string"}},
            "recommended_action": {"type": ["string", "null"]},
            "primary_risk": {"type": ["string", "null"]},
            "likely_consequence": {"type": ["string", "null"]},
            "evidence_used": {"type": "array", "items": {"type": "string"}},
            "recommended_decision": {"type": ["string", "null"]},
            "decision_risk": {"type": ["string", "null"]},
            "suggested_next_step": {"type": ["string", "null"]},
            "reasoning_summary": {"type": ["string", "null"]},
            "watch_item": {"type": ["string", "null"]},
            "missing_data": {"type": ["string", "null"]},
            "answer_mode": {"type": ["string", "null"]},
            "clarifying_question": {"type": ["string", "null"]},
            "suggested_questions": {"type": "array", "items": {"type": "string"}},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "external_research_used": {"type": ["boolean", "null"]},
            "external_sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "domain": {"type": "string"},
                    },
                    "required": ["title", "url", "domain"],
                },
            },
        },
        "required": [
            "mode",
            "decision_family",
            "decision_lens",
            "persona_id",
            "scenario_id",
            "framework_code",
            "emotion_mode",
            "perspective_code",
            "target_cell_id",
            "confidence",
            "reason",
            "direct_answer",
            "why_this_answer",
            "supporting_kpis",
            "recommended_action",
            "primary_risk",
            "likely_consequence",
            "evidence_used",
            "recommended_decision",
            "decision_risk",
            "suggested_next_step",
            "reasoning_summary",
            "watch_item",
            "missing_data",
            "answer_mode",
            "clarifying_question",
            "suggested_questions",
            "follow_up_questions",
            "external_research_used",
            "external_sources",
        ],
    }


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty model output")
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Could not parse JSON from model output: {text[:500]}")
        return json.loads(text[start:end + 1])


def _extract_response_output_text(raw: Dict[str, Any]) -> str:
    texts: List[str] = []
    for item in raw.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text" and content.get("text"):
                texts.append(str(content.get("text")))
    if texts:
        return "\n".join(texts)
    return str(raw.get("output_text") or "")


def _extract_response_sources(raw: Dict[str, Any]) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    seen = set()

    def add_source(title: str, url: str) -> None:
        if not url:
            return
        domain = _urlparse(url).netloc or ""
        key = (title or "", url)
        if key in seen:
            return
        seen.add(key)
        results.append({
            "title": title or domain or url,
            "url": url,
            "domain": domain,
        })

    for item in raw.get("output", []) or []:
        if item.get("type") == "message":
            for content in item.get("content", []) or []:
                for annotation in content.get("annotations", []) or []:
                    if annotation.get("type") == "url_citation":
                        add_source(str(annotation.get("title") or ""), str(annotation.get("url") or ""))
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            for source in action.get("sources", []) or []:
                add_source(str(source.get("title") or ""), str(source.get("url") or ""))

    return results[:8]


def _call_openai_router(question: str, context: Dict[str, Any], clarification_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": _build_user_payload(question, context, clarification_context)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "question_router",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "mode": {"type": "string", "enum": ["answer", "clarify", "suggest"]},
                        "decision_family": {"type": ["string", "null"]},
                        "decision_lens": {"type": ["string", "null"]},
                        "persona_id": {"type": ["string", "null"]},
                        "scenario_id": {"type": ["string", "null"]},
                        "framework_code": {"type": ["string", "null"]},
                        "emotion_mode": {"type": ["string", "null"]},
                        "perspective_code": {"type": ["string", "null"]},
                        "target_cell_id": {"type": ["string", "null"]},
                        "confidence": {"type": "number"},
                        "reason": {"type": "string"},
                        "direct_answer": {"type": ["string", "null"]},
                        "why_this_answer": {"type": ["string", "null"]},
                        "supporting_kpis": {"type": "array", "items": {"type": "string"}},
                        "recommended_action": {"type": ["string", "null"]},
                        "primary_risk": {"type": ["string", "null"]},
                        "likely_consequence": {"type": ["string", "null"]},
                        "evidence_used": {"type": "array", "items": {"type": "string"}},
                        "recommended_decision": {"type": ["string", "null"]},
                        "decision_risk": {"type": ["string", "null"]},
                        "suggested_next_step": {"type": ["string", "null"]},
                        "reasoning_summary": {"type": ["string", "null"]},
                        "watch_item": {"type": ["string", "null"]},
                        "missing_data": {"type": ["string", "null"]},
                        "answer_mode": {"type": ["string", "null"]},
                        "clarifying_question": {"type": ["string", "null"]},
                        "suggested_questions": {"type": "array", "items": {"type": "string"}},
                        "follow_up_questions": {"type": "array", "items": {"type": "string"}},
                        "external_research_used": {"type": ["boolean", "null"]},
                        "external_sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "domain": {"type": "string"},
                                },
                                "required": ["title", "url", "domain"],
                            },
                        },
                    },
                    "required": _router_schema()["required"],
                },
            },
        },
    }
    request = _urlrequest.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with _urlrequest.urlopen(request, timeout=20) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except _urlerror.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {body}") from exc
    except _urlerror.URLError as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    try:
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as exc:
        raise RuntimeError(f"Invalid OpenAI router response: {raw}") from exc


def _call_openai_router_with_web(question: str, context: Dict[str, Any], clarification_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_EXTERNAL_MODEL", os.environ.get("OPENAI_MODEL", "gpt-5.4"))
    system_prompt = (
        _build_system_prompt()
        + " External research mode is enabled. You may use web search to fetch current outside facts, "
          "but you must still anchor the decision to the provided active scenario and matrix cells. "
          "Use outside facts only as supporting evidence, not as a reason to switch scenario. "
          "If you use web search, set external_research_used=true and reflect the fetched facts in evidence_used and why_this_answer."
    )
    payload = {
        "model": model,
        "reasoning": {"effort": "low"},
        "tools": [{"type": "web_search"}],
        "tool_choice": "auto",
        "include": ["web_search_call.action.sources"],
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": _build_user_payload(question, context, clarification_context)}]},
        ],
    }
    request = _urlrequest.Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with _urlrequest.urlopen(request, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except _urlerror.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI responses HTTP {exc.code}: {body}") from exc
    except _urlerror.URLError as exc:
        raise RuntimeError(f"OpenAI responses request failed: {exc}") from exc

    try:
        result = _extract_json_object(_extract_response_output_text(raw))
    except Exception as exc:
        raise RuntimeError(f"Invalid OpenAI responses router output: {raw}") from exc
    result["external_research_used"] = True
    result["external_sources"] = _extract_response_sources(raw)
    return result


def _validate_router_output(result: Dict[str, Any], context: Dict[str, Any], question: str = "") -> Dict[str, Any]:
    valid_modes = {"answer", "clarify", "suggest"}
    mode = result.get("mode")
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode: {mode}")

    valid_cell_ids = {cell.get("cell_id") for cell in context.get("matrix_cells", [])}
    valid_emotions = {item.get("code") for item in context.get("emotion_modes", [])}
    valid_perspectives = {item.get("code") for item in context.get("perspectives", [])}

    target_cell_id = result.get("target_cell_id")
    if mode == "answer" and target_cell_id not in valid_cell_ids:
        raise ValueError(f"Invalid target_cell_id: {target_cell_id}")

    emotion_mode = result.get("emotion_mode")
    if emotion_mode and emotion_mode not in valid_emotions:
        result["emotion_mode"] = None

    perspective_code = result.get("perspective_code")
    if perspective_code and perspective_code not in valid_perspectives:
        result["perspective_code"] = None

    result["decision_family"] = (result.get("decision_family") or "").strip() or _classify_decision_family("", context)
    result["decision_lens"] = (result.get("decision_lens") or "").strip()
    result["suggested_questions"] = _dedupe(result.get("suggested_questions") or [], 5)
    result["follow_up_questions"] = _dedupe(result.get("follow_up_questions") or [], 5)
    result["supporting_kpis"] = _dedupe(result.get("supporting_kpis") or [], 5)
    result["evidence_used"] = _dedupe(result.get("evidence_used") or [], 5)
    result["reason"] = (result.get("reason") or "").strip()
    result["direct_answer"] = (result.get("direct_answer") or "").strip()
    result["why_this_answer"] = (result.get("why_this_answer") or "").strip()
    result["recommended_action"] = (result.get("recommended_action") or "").strip()
    result["primary_risk"] = (result.get("primary_risk") or "").strip()
    result["likely_consequence"] = (result.get("likely_consequence") or "").strip()
    result["recommended_decision"] = (result.get("recommended_decision") or "").strip()
    result["decision_risk"] = (result.get("decision_risk") or "").strip()
    result["suggested_next_step"] = (result.get("suggested_next_step") or "").strip()
    result["reasoning_summary"] = (result.get("reasoning_summary") or "").strip()
    result["watch_item"] = (result.get("watch_item") or "").strip()
    result["missing_data"] = (result.get("missing_data") or "").strip()
    result["answer_mode"] = (result.get("answer_mode") or "").strip()
    result["external_research_used"] = bool(result.get("external_research_used"))
    result["external_sources"] = [
        {
            "title": str(item.get("title") or "").strip(),
            "url": str(item.get("url") or "").strip(),
            "domain": str(item.get("domain") or "").strip(),
        }
        for item in (result.get("external_sources") or [])
        if isinstance(item, dict) and str(item.get("url") or "").strip()
    ][:8]
    result["confidence"] = float(result.get("confidence") or 0.0)
    if mode == "answer":
        cell = _find_cell_by_id(context, target_cell_id)
        if cell:
            filled = _build_answer_fields(question, cell, context, result["confidence"], result["reason"])
            if _uses_fixed_matrix(context):
                filled = _build_fixed_matrix_answer_fields(question, cell, context, result["confidence"], result["reason"])
                for key in [
                    "decision_family",
                    "decision_lens",
                    "direct_answer",
                    "why_this_answer",
                    "supporting_kpis",
                    "recommended_action",
                    "primary_risk",
                    "likely_consequence",
                    "evidence_used",
                    "recommended_decision",
                    "decision_risk",
                    "suggested_next_step",
                    "reasoning_summary",
                    "watch_item",
                    "missing_data",
                    "answer_mode",
                ]:
                    result[key] = filled.get(key)
                return result
            for key in [
                "decision_family",
                "decision_lens",
                "direct_answer",
                "why_this_answer",
                "supporting_kpis",
                "recommended_action",
                "primary_risk",
                "likely_consequence",
                "evidence_used",
                "recommended_decision",
                "decision_risk",
                "suggested_next_step",
                "reasoning_summary",
                "watch_item",
                "missing_data",
                "answer_mode",
            ]:
                if not result.get(key):
                    result[key] = filled.get(key)
            if not result.get("direct_answer"):
                result["direct_answer"] = result.get("recommended_decision") or filled.get("direct_answer")
            if not result.get("recommended_action"):
                result["recommended_action"] = result.get("suggested_next_step") or filled.get("recommended_action")
            if not result.get("primary_risk"):
                result["primary_risk"] = result.get("decision_risk") or filled.get("primary_risk")
    return result


def route_question_with_llm(
    question: str,
    context: Dict[str, Any],
    clarification_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        use_external = (context.get("assistant_mode") or "").strip() == "scenario-external"
        result = (
            _call_openai_router_with_web(question, context, clarification_context)
            if use_external
            else _call_openai_router(question, context, clarification_context)
        )
        validated = _validate_router_output(result, context, question)
        return {
            "status": "ok",
            "router": validated,
            "provider": "openai-web" if use_external else "openai",
            "fallback_used": False,
        }
    except Exception as exc:
        fallback = _fallback_route(question, context)
        return {
            "status": "fallback",
            "router": fallback,
            "provider": "fallback",
            "fallback_used": True,
            "error": str(exc),
        }
