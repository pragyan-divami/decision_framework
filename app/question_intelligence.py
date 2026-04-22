import json
import os
from typing import Any, Dict, List, Optional
from urllib import error as _urlerror
from urllib import request as _urlrequest


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


def _score_cell(question: str, cell: Dict[str, Any], context: Dict[str, Any]) -> float:
    lower = (question or "").lower()
    tokens = set(_extract_tokens(lower))
    intent = _classify_intent(question)
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

    cells = context.get("matrix_cells") or []
    if not cells:
        return {
            "mode": "suggest",
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.0,
            "reason": "No matrix cells were available for this scenario.",
            "clarifying_question": None,
            "suggested_questions": [],
            "follow_up_questions": [],
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
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    gap = top["score"] - (second["score"] if second else 0)
    if intent == "kpi_lookup" and top["score"] < 4:
        return {
            "mode": "clarify",
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.35,
            "reason": "I can answer this, but I need to know which kind of variance or exposure you mean.",
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
                "persona_id": context.get("persona_id"),
                "scenario_id": context.get("scenario_id"),
                "framework_code": context.get("framework_code"),
                "emotion_mode": None,
                "perspective_code": None,
                "target_cell_id": None,
                "confidence": 0.15,
                "reason": prompt,
                "clarifying_question": None,
                "suggested_questions": _build_broad_suggestions(context, question),
                "follow_up_questions": [],
            }
        return {
            "mode": "suggest",
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.2,
            "reason": "That question is too broad for this scenario. Try one of these instead.",
            "clarifying_question": None,
            "suggested_questions": _build_recovery_suggestions(question, context),
            "follow_up_questions": [],
        }

    if gap < 2:
        if intent == "kpi_lookup":
            return {
                "mode": "clarify",
                "persona_id": context.get("persona_id"),
                "scenario_id": context.get("scenario_id"),
                "framework_code": context.get("framework_code"),
                "emotion_mode": None,
                "perspective_code": None,
                "target_cell_id": None,
                "confidence": 0.45,
                "reason": "Your question maps to more than one plausible variance signal in this scenario.",
                "clarifying_question": "Do you mean schedule variance, financial variance, people/governance exposure, or contract/commercial variance?",
                "suggested_questions": _dedupe([
                    f"What is my variance from the {top['cell'].get('perspective_label')} perspective?",
                    f"What is my variance from the {second['cell'].get('perspective_label')} perspective?" if second else "",
                ], 3),
                "follow_up_questions": [],
            }
        return {
            "mode": "clarify",
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": None,
            "perspective_code": None,
            "target_cell_id": None,
            "confidence": 0.45,
            "reason": "The question could map to more than one matrix cell.",
            "clarifying_question": _build_clarification(top["cell"], second["cell"] if second else None),
            "suggested_questions": _dedupe([
                f"What is the right path through the {top['cell'].get('perspective_label')} perspective?",
                f"What is the right path through the {second['cell'].get('perspective_label')} perspective?" if second else "",
            ], 3),
            "follow_up_questions": [],
        }

    cell = top["cell"]
    if broad_question:
        return {
            "mode": "answer",
            "persona_id": context.get("persona_id"),
            "scenario_id": context.get("scenario_id"),
            "framework_code": context.get("framework_code"),
            "emotion_mode": cell.get("emotion_mode"),
            "perspective_code": cell.get("perspective_code"),
            "target_cell_id": cell.get("cell_id"),
            "confidence": min(0.55, 0.28 + min(top["score"], 10) * 0.02),
            "reason": f"Broad question. I selected the best-fit current outcome from {cell.get('emotion_mode_label') or cell.get('emotion_mode')} × {cell.get('perspective_label')} based on the strongest scenario signals.",
            "clarifying_question": None,
            "suggested_questions": [],
            "follow_up_questions": _build_broad_suggestions(context, question),
        }
    return {
        "mode": "answer",
        "persona_id": context.get("persona_id"),
        "scenario_id": context.get("scenario_id"),
        "framework_code": context.get("framework_code"),
        "emotion_mode": cell.get("emotion_mode"),
        "perspective_code": cell.get("perspective_code"),
        "target_cell_id": cell.get("cell_id"),
        "confidence": min(0.9, 0.55 + min(top["score"], 10) * 0.03),
        "reason": f"Matched {cell.get('emotion_mode_label') or cell.get('emotion_mode')} × {cell.get('perspective_label')} based on the strongest scenario and KPI overlap.",
        "clarifying_question": None,
        "suggested_questions": [],
        "follow_up_questions": _build_follow_ups(cell, context),
    }


def _build_system_prompt() -> str:
    return (
        "You are a constrained decision-matrix routing engine. "
        "You receive one active scenario context, one active persona, visible matrix rows, visible matrix columns, "
        "and a compact inventory of matrix cells. "
        "You must choose exactly one mode: answer, clarify, or suggest. "
        "Rules: "
        "1. Stay inside the provided scenario context. Do not invent scenarios, personas, KPIs, or cells. "
        "2. First classify the question into one intent: kpi_lookup, threshold, probability, comparison, legal_trigger, reversibility, stakeholder_signal, cost_of_delay, action_selection, consequence, sequencing, or data. "
        "3. If the question maps clearly to one cell, return mode=answer with the exact target_cell_id from the inventory. "
        "4. If one important distinction is missing, return mode=clarify with exactly one short clarifying question. "
        "5. If the question is too broad or malformed, return mode=suggest with 3 to 5 better scenario-specific questions. "
        "6. Treat shorthand executive questions like 'what is my variance' or 'what is my commercial position' as kpi_lookup queries, not as broad generic prompts. Answer directly if one dominant KPI is clear; otherwise ask one short clarification. "
        "7. When returning suggested_questions or follow_up_questions, make them varied across perspective, intent, and decision angle. "
        "Do not return five versions of the same 'best path' question. Use a mix of action, risk, data, threshold, and stakeholder prompts when relevant. "
        "8. Use the matrix cells as the answer surface. Do not invent new cells or new KPIs. "
        "9. Return valid JSON only."
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
            "scenario_kpis": context.get("scenario_kpis", []),
            "persona_tension": context.get("persona_tension"),
            "framework_code": context.get("framework_code"),
        },
        "visible_perspectives": context.get("perspectives", []),
        "visible_emotion_modes": context.get("emotion_modes", []),
        "matrix_cells": context.get("matrix_cells", []),
        "clarification_context": clarification_context,
        "required_output_keys": [
            "mode",
            "persona_id",
            "scenario_id",
            "framework_code",
            "emotion_mode",
            "perspective_code",
            "target_cell_id",
            "confidence",
            "reason",
            "clarifying_question",
            "suggested_questions",
            "follow_up_questions",
        ],
    }
    return json.dumps(compact, ensure_ascii=True)


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
                        "persona_id": {"type": ["string", "null"]},
                        "scenario_id": {"type": ["string", "null"]},
                        "framework_code": {"type": ["string", "null"]},
                        "emotion_mode": {"type": ["string", "null"]},
                        "perspective_code": {"type": ["string", "null"]},
                        "target_cell_id": {"type": ["string", "null"]},
                        "confidence": {"type": "number"},
                        "reason": {"type": "string"},
                        "clarifying_question": {"type": ["string", "null"]},
                        "suggested_questions": {"type": "array", "items": {"type": "string"}},
                        "follow_up_questions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "mode",
                        "persona_id",
                        "scenario_id",
                        "framework_code",
                        "emotion_mode",
                        "perspective_code",
                        "target_cell_id",
                        "confidence",
                        "reason",
                        "clarifying_question",
                        "suggested_questions",
                        "follow_up_questions",
                    ],
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


def _validate_router_output(result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
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

    result["suggested_questions"] = _dedupe(result.get("suggested_questions") or [], 5)
    result["follow_up_questions"] = _dedupe(result.get("follow_up_questions") or [], 5)
    result["reason"] = (result.get("reason") or "").strip()
    result["confidence"] = float(result.get("confidence") or 0.0)
    return result


def route_question_with_llm(
    question: str,
    context: Dict[str, Any],
    clarification_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        result = _call_openai_router(question, context, clarification_context)
        validated = _validate_router_output(result, context)
        return {
            "status": "ok",
            "router": validated,
            "provider": "openai",
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
