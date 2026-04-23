import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

try:
    from .fixed_matrix import build_fixed_matrix_bootstrap, build_fixed_matrix_cell_runtime, build_persona_perspective_labels, normalize_persona_for_fixed_matrix, normalize_scenario_for_fixed_matrix  # type: ignore
except Exception:  # pragma: no cover
    from fixed_matrix import build_fixed_matrix_bootstrap, build_fixed_matrix_cell_runtime, build_persona_perspective_labels, normalize_persona_for_fixed_matrix, normalize_scenario_for_fixed_matrix


ROOT = Path(__file__).resolve().parent
PERSONA_DIR = ROOT / "data" / "personas"
SCENARIO_DIR = ROOT / "data" / "scenarios"
VO112_SCHEMA_PATH = Path("/Users/pragyan/Downloads/CROSS_VO112_cell_level_executable_schema.md")

PROJECT = {
    "name": "Tata Steel UK Port Talbot EAF Transformation",
    "domain": "industrial-transformation",
    "description": "A Tata UK transformation workspace grounded in commissioning, scrap, energy, workforce, customer, grant, and decarbonization decisions.",
}

DOMAINS = [
    {
        "id": "industrial-transformation",
        "label": "Industrial Transformation / Steel",
        "note": "Port Talbot EAF programme context",
    }
]

PLATFORMS = [
    {
        "id": "programme-core",
        "label": "Port Talbot Transformation Programme",
        "note": "Integrated programme view across construction, workforce, customer, grant, and energy dependencies.",
    },
    {
        "id": "commissioning-delivery",
        "label": "Construction / Commissioning",
        "note": "Delivery, contractor, and readiness decisions.",
    },
    {
        "id": "commercial-transition",
        "label": "Customer / Grade Capability",
        "note": "Transition-gap margin, customer retention, and grade suitability.",
    },
    {
        "id": "grid-energy",
        "label": "Energy / Grid Readiness",
        "note": "National Grid timing, power cost, and energy competitiveness.",
    },
    {
        "id": "scrap-supply",
        "label": "Scrap Supply / Quality",
        "note": "Scrap sourcing, quality, and processing readiness.",
    },
    {
        "id": "workforce-transition",
        "label": "Workforce / Community Transition",
        "note": "Reskilling, community legitimacy, labour continuity, and regional regeneration.",
    },
]

PERSONA_PLATFORM_BIAS = {
    "P1": ["programme-core", "commissioning-delivery", "commercial-transition", "grid-energy", "workforce-transition"],
    "P2": ["workforce-transition", "programme-core"],
    "P3": ["commissioning-delivery", "programme-core", "grid-energy"],
    "P4": ["programme-core", "commercial-transition", "grid-energy"],
    "P5": ["workforce-transition", "programme-core"],
    "P6": ["programme-core"],
    "P7": ["scrap-supply", "programme-core", "commercial-transition"],
    "P8": ["grid-energy", "programme-core", "commissioning-delivery"],
    "P9": ["workforce-transition", "programme-core"],
    "P10": ["commercial-transition", "programme-core"],
}

PERSONA_FRAMEWORKS = {
    "P1": {"frameworks": ["B", "C"], "recommended": "B"},
    "P2": {"frameworks": ["C", "F"], "recommended": "C"},
    "P3": {"frameworks": ["D", "E"], "recommended": "D"},
    "P4": {"frameworks": ["A", "E"], "recommended": "A"},
    "P5": {"frameworks": ["C", "F"], "recommended": "C"},
    "P6": {"frameworks": ["B", "C"], "recommended": "B"},
    "P7": {"frameworks": ["B", "F"], "recommended": "B"},
    "P8": {"frameworks": ["A", "E"], "recommended": "A"},
    "P9": {"frameworks": ["C", "F"], "recommended": "C"},
    "P10": {"frameworks": ["B", "F"], "recommended": "B"},
}

COMMERCIAL_KPI_CATALOG = [
    {
        "code": "C1",
        "label": "Contract entitlement strength",
        "description": "How strong Tata's position is on the claim, clause, or dispute item.",
        "keywords": ["contract", "clause", "entitlement", "variation", "claim", "force majeure", "breach"],
        "dataHints": ["relevant clause wording", "reservation-of-rights position", "external legal view if needed"],
    },
    {
        "code": "C2",
        "label": "Immediate cash exposure",
        "description": "Cash or contingency consumed inside the current decision window.",
        "keywords": ["cash", "payment", "settle", "withhold", "escrow", "contingency", "cost"],
        "dataHints": ["cash timing profile", "contingency headroom", "cost of suspension vs disputed amount"],
    },
    {
        "code": "C3",
        "label": "Schedule-at-risk from commercial action",
        "description": "Delay created by dispute, suspension, notice, amendment, or renegotiation.",
        "keywords": ["schedule", "delay", "extension", "commissioning", "slip", "longstop", "float"],
        "dataHints": ["critical path impact", "counterparty suspension rights", "milestone recovery window"],
    },
    {
        "code": "C4",
        "label": "Disclosure / covenant trigger proximity",
        "description": "How close the issue is to a formal disclosure, covenant, or materiality threshold.",
        "keywords": ["disclose", "regulator", "board", "grant", "materiality", "covenant", "notify"],
        "dataHints": ["materiality threshold", "grant / covenant trigger note", "who must be told by when"],
    },
    {
        "code": "C5",
        "label": "Counterparty cooperation risk",
        "description": "Risk that the other side becomes less cooperative if challenged or delayed.",
        "keywords": ["supplier", "customer", "contractor", "counterparty", "relationship", "cooperate", "suspend"],
        "dataHints": ["counterparty leverage map", "current relationship temperature", "fallback counterparty options"],
    },
    {
        "code": "C6",
        "label": "Contractual optionality preserved",
        "description": "How much room remains to amend, settle, defer, hedge, or reverse.",
        "keywords": ["optionality", "reversible", "amend", "side letter", "defer", "reserve rights", "wait"],
        "dataHints": ["amendment path", "reservation-of-rights deadline", "reversible vs irreversible move"],
    },
    {
        "code": "C7",
        "label": "Revenue / demand exposure",
        "description": "Revenue, customer volume, or pricing at risk if the issue leaks or hardens.",
        "keywords": ["revenue", "demand", "customer", "market", "pricing", "volume", "BMW", "JLR", "Stellantis"],
        "dataHints": ["revenue at risk", "customer concentration", "competitive qualification activity"],
    },
    {
        "code": "C8",
        "label": "Precedent / governance risk",
        "description": "Whether the move creates a bad precedent, audit issue, or board liability.",
        "keywords": ["precedent", "governance", "audit", "board", "control", "liability", "scrutiny"],
        "dataHints": ["board / audit view", "similar precedent cases", "control or governance implications"],
    },
]

PERSONA_COMMERCIAL_EMPHASIS = {
    "P1": ["K1", "K2", "K3", "C3", "C8"],
    "P2": ["K1", "K2", "C5", "C3", "C2"],
    "P3": ["K1", "K4", "K7", "C5", "C3"],
    "P4": ["K1", "K2", "K7", "K8", "C2", "C4"],
    "P5": ["K2", "K4", "K5", "C4", "C8"],
    "P6": ["K1", "K2", "K5", "K6", "C4", "C8"],
    "P7": ["K1", "K2", "K6", "K7", "C6", "C7"],
    "P8": ["K1", "K4", "K6", "K5", "C6", "C4"],
    "P9": ["K6", "K2", "K7", "C4", "C8"],
    "P10": ["K1", "K3", "K5", "K8", "C7", "C5"],
}

COMMERCIAL_QUESTION_FAMILIES = {
    "entitlement": {
        "keywords": ["entitled", "entitlement", "claim", "can they claim", "variation", "breach", "force majeure", "clause"],
        "primary": ["C1"],
        "supporting": ["C8", "C3"],
    },
    "payment": {
        "keywords": ["pay", "withhold", "settle", "escrow", "payment", "under protest", "disputed amount"],
        "primary": ["C2", "C3"],
        "supporting": ["C1", "C6"],
    },
    "disclosure": {
        "keywords": ["tell", "disclose", "notify", "regulator", "board", "grant", "customer", "union", "council", "investor"],
        "primary": ["C4"],
        "supporting": ["C8", "C7"],
    },
    "schedule": {
        "keywords": ["schedule", "slip", "longstop", "float", "extension", "commissioning", "delay"],
        "primary": ["C3"],
        "supporting": ["C5", "C6"],
    },
    "counterparty": {
        "keywords": ["supplier", "contractor", "customer", "utility", "counterparty", "cooperate", "suspend", "renegotiate"],
        "primary": ["C5"],
        "supporting": ["C3", "C6"],
    },
    "customer_market": {
        "keywords": ["customer", "market", "BMW", "JLR", "Stellantis", "trust", "revenue", "demand", "qualification"],
        "primary": ["C7"],
        "supporting": ["C5", "C4"],
    },
    "amendment_notice": {
        "keywords": ["amend", "amendment", "notice", "reserve rights", "side letter", "notify formally"],
        "primary": ["C4", "C6"],
        "supporting": ["C1", "C5"],
    },
    "governance": {
        "keywords": ["material", "board", "covenant", "governance", "audit", "director", "filing"],
        "primary": ["C4", "C8"],
        "supporting": ["C2", "C3"],
    },
    "optionality": {
        "keywords": ["wait", "what happens if we wait", "reversible", "optionality", "preserve room", "defer"],
        "primary": ["C6"],
        "supporting": ["C3", "C5"],
    },
    "bids_pricing": {
        "keywords": ["bid", "tender", "pricing", "pass-through", "risk-load", "escalation", "indexation"],
        "primary": ["C1", "C2"],
        "supporting": ["C8", "C7"],
    },
    "consequence": {
        "keywords": ["what breaks", "consequence", "if we act", "if we wait", "what happens next"],
        "primary": ["C6", "C3"],
        "supporting": ["C5", "C8"],
    },
}


def _extract_markdown_table(section: str) -> List[Dict[str, str]]:
    lines = [line.rstrip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    headers = [cell.strip() for cell in lines[0].strip().strip("|").split("|")]
    rows: List[Dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def _extract_section_body(text: str, heading: str) -> str:
    match = re.search(rf"{re.escape(heading)}\n(.*?)(?=\n### |\n## |\Z)", text, re.S)
    return match.group(1).strip() if match else ""


def _extract_prefixed_bullets(text: str) -> List[str]:
    return [line.strip()[2:].strip() for line in text.splitlines() if line.strip().startswith("- ")]


def _dedupe(values: List[str], limit: int = 20) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def _clean_schema_text(value: str) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"fileciteturn\d+file\d+", "", value)
    cleaned = re.sub(r"\?filecite\?turn\d+file\d+\?", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _collapse_markdown_text(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*-\s*", "", text, flags=re.M)
    text = re.sub(r"\n{2,}", "\n\n", text.strip())
    return text


def _build_header_summary(about: str, scenario_body: str, tension: str, call: str) -> str:
    parts = []
    if about:
        parts.append(_collapse_markdown_text(about))
    elif scenario_body:
        parts.append(_collapse_markdown_text(scenario_body))
    if tension:
        parts.append(f"Tension: {_collapse_markdown_text(tension)}")
    if call:
        parts.append(f"Decision focus: {_collapse_markdown_text(call)}")
    return "\n\n".join(part for part in parts if part).strip()


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _extract_field(text: str, label: str) -> str:
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", text)
    return match.group(1).strip() if match else ""


def _extract_section(text: str, heading: str) -> str:
    match = re.search(rf"## {re.escape(heading)}\n\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(1).strip() if match else ""


def _extract_section_pattern(text: str, pattern: str) -> str:
    match = re.search(rf"## {pattern}\n\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(1).strip() if match else ""


def _extract_table_value(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith("| **") and "|" in line[1:]:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                left = re.sub(r"[* ]", "", cells[0]).strip().lower()
                if left == key.lower():
                    return cells[1].strip()
    return ""


def _extract_kpis(text: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    for line in text.splitlines():
        match = re.match(r"-\s+\*\*(K\d+)\*\*\s+·\s+(.+)", line.strip())
        if match:
            code, label = match.groups()
            results.append({"code": code, "label": label.strip()})
    return results


def _extract_table_rows(text: str) -> Dict[str, str]:
    rows: Dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("| **") and "|" in line[1:]:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                left = re.sub(r"[* ]", "", cells[0]).strip()
                rows[left] = cells[1].strip()
    return rows


def _extract_bullets(text: str) -> List[str]:
    bullets: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def _extract_options_from_section(text: str) -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"-\s+\*\*([A-Z])\s+—\s+(.+?)\.\*\*\s*(.*)", stripped)
        if not match:
            continue
        code, label, body = match.groups()
        normalized = re.sub(r"\s+", " ", body).strip()
        risk_match = re.search(r"Risk:\s*(.+)", normalized, re.I)
        risk = risk_match.group(1).strip() if risk_match else ""
        action_summary = re.sub(r"\s*Risk:\s*.+$", "", normalized, flags=re.I).strip()
        options.append(
            {
                "code": code,
                "label": label.strip(),
                "summary": action_summary or normalized,
                "risk": risk,
                "keywords": _keywords(label, normalized),
            }
        )
    return options


def _short_label(label: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", "", label)
    cleaned = re.sub(r"^[A-Z]\d+\s*·\s*", "", cleaned)
    cleaned = cleaned.replace(" vs ", " ")
    return re.sub(r"\s+", " ", cleaned).strip(" -")


def _keywords(*values: str) -> List[str]:
    seen = set()
    items: List[str] = []
    for value in values:
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+-]+", value.lower()):
            if len(token) < 4:
                continue
            if token not in seen:
                seen.add(token)
                items.append(token)
    return items[:10]


def _is_commercial_context(*values: str) -> bool:
    combined = " ".join(values).lower()
    triggers = (
        "contract",
        "commercial",
        "customer",
        "bid",
        "variation",
        "claim",
        "payment",
        "disclose",
        "mou",
        "offtake",
        "notice",
    )
    return any(token in combined for token in triggers)


def _build_commercial_overlay(code: str) -> Dict[str, Any]:
    return {
        "enabled": True,
        "personaEmphasis": PERSONA_COMMERCIAL_EMPHASIS.get(code, []),
        "universalKpis": COMMERCIAL_KPI_CATALOG,
        "questionFamilies": COMMERCIAL_QUESTION_FAMILIES,
    }


def _extract_scenario_options(text: str) -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    matches = list(
        re.finditer(
            r"\*\*(Option [A-Z])\s+—\s+(.+?)\.\*\*\s*(.*?)(?=\n\s*\*\*Option [A-Z]\s+—|\n## |\Z)",
            text,
            re.S,
        )
    )
    for match in matches:
        code, label, body = match.groups()
        normalized = re.sub(r"\s+", " ", body).strip()
        risk_match = re.search(r"Risk:\s*(.+)", normalized, re.I)
        risk = risk_match.group(1).strip() if risk_match else ""
        action_summary = re.sub(r"\s*Risk:\s*.+$", "", normalized, flags=re.I).strip()
        options.append(
            {
                "code": code.replace("Option ", ""),
                "label": label.strip(),
                "summary": action_summary or normalized,
                "risk": risk,
                "keywords": _keywords(label, normalized),
            }
        )
    return options


def _extract_pack_options(text: str) -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    matches = list(
        re.finditer(
            r"\*\*([A-Z])\.\s+(.+?)\*\*\s*(.*?)(?=\n\s*\*\*[A-Z]\.\s+|\n###\s+KPI families|\Z)",
            text,
            re.S,
        )
    )
    for match in matches:
        code, label, body = match.groups()
        normalized = re.sub(r"\s+", " ", body).strip()
        options.append(
            {
                "code": code.strip(),
                "label": label.strip(),
                "summary": normalized,
                "risk": "",
                "keywords": _keywords(label, normalized),
            }
        )
    return options


def _extract_pack_kpis(text: str) -> List[Dict[str, str]]:
    kpis: List[Dict[str, str]] = []
    for index, bullet in enumerate(_extract_bullets(text), start=1):
        kpis.append({"code": f"K{index}", "label": bullet})
    return kpis


def _build_pack_summary(trigger: str, tension: str, options: List[Dict[str, str]]) -> str:
    parts = []
    if trigger:
        parts.append(trigger.strip())
    if tension:
        parts.append(f"Tension: {tension.strip()}")
    if options:
        option_summary = "; ".join(f"{item['code']}: {item['label']}" for item in options[:3])
        parts.append(f"Options in play: {option_summary}.")
    return "\n\n".join(parts)


def _build_pack_explanation(
    trigger: str,
    tension: str,
    options: List[Dict[str, str]],
    commercial_variance: str,
    compliance_variance: str,
    bid_variance: str,
) -> str:
    parts = [_build_pack_summary(trigger, tension, options)]
    if commercial_variance:
        parts.append(f"Commercial variance focus: {commercial_variance.strip()}")
    if compliance_variance:
        parts.append(f"Compliance variance focus: {compliance_variance.strip()}")
    if bid_variance:
        parts.append(f"Bid variance focus: {bid_variance.strip()}")
    return "\n\n".join(part for part in parts if part)


def _derive_perspectives(kpis: List[Dict[str, str]], context_bullets: List[str], lens: str, tension: str, role: str, platform: str) -> List[Dict[str, Any]]:
    base_bullets = context_bullets[:2]
    perspectives: List[Dict[str, Any]] = []
    for item in kpis[:4]:
        short = _short_label(item["label"])
        lower_short = short.lower()
        perspectives.append(
            {
                "id": _slugify(short),
                "label": short,
                "kpis": [item["label"]],
                "data": [
                    f"Latest status for {lower_short}",
                    f"Variance against target for {lower_short}",
                    *base_bullets,
                ][:4],
                "chart": f"{short} tracker",
                "action": f"Bias the decision toward protecting {lower_short} for the {role} lens.",
                "risk": f"If {lower_short} deteriorates, the core tension around {tension.lower()} gets harder to control.",
                "consequence": f"The likely consequence is pressure on the {lens.lower()} lens inside the {platform.lower()} context.",
                "blind": f"The role can over-focus on {lens.lower()} and miss second-order effects around {lower_short}.",
                "keywords": _keywords(short, tension, lens, platform, *base_bullets),
            }
        )
    return perspectives


def _parse_persona_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    header_match = re.search(r"^#\s+(P\d+)\s+·\s+(.+)$", text, re.M)
    if not header_match:
        raise ValueError(f"Could not parse persona header in {path.name}")
    code, name = header_match.groups()

    domain = _extract_field(text, "Domain")
    platform = _extract_field(text, "Platform")
    persona = _extract_field(text, "Persona")
    role_section = _extract_section(text, "Role")
    background = _extract_section(text, "Background")
    context_match = re.search(r"## Context:.*?\n\n(.*?)(?=\n## |\Z)", text, re.S)
    context_text = context_match.group(1).strip() if context_match else ""
    context_bullets = _extract_bullets(context_text)
    focus_text = _extract_section_pattern(text, r"What keeps .* focused")
    time_horizon = _extract_table_value(focus_text, "Time horizon")
    stakeholders = _extract_table_value(focus_text, "Primary stakeholders")
    tension = _extract_table_value(focus_text, "Hardest tension")
    lens = _extract_table_value(focus_text, "Lens")
    kpi_text = _extract_section(text, "KPI families")
    kpis = _extract_kpis(kpi_text)
    decision_notes = _extract_section(text, "Decision style notes")

    frameworks = PERSONA_FRAMEWORKS.get(code, {"frameworks": ["A", "F"], "recommended": "F"})
    platform_bias = PERSONA_PLATFORM_BIAS.get(code, ["programme-core"])

    return {
        "id": f"{code.lower()}-{_slugify(name)}",
        "code": code,
        "label": name,
        "name": name,
        "role": persona or role_section.split(".")[0].strip(),
        "roleSummary": role_section.split("\n\n")[0].strip(),
        "domain": domain,
        "platform": platform,
        "platformBias": platform_bias,
        "summary": background.split("\n\n")[0].strip(),
        "background": background,
        "timeHorizon": time_horizon,
        "primaryStakeholders": stakeholders,
        "hardestTension": tension,
        "lens": lens,
        "contextBullets": context_bullets,
        "kpiFamilies": kpis,
        "decisionStyleNotes": decision_notes,
        "perspectives": _derive_perspectives(kpis, context_bullets, lens, tension, persona or name, platform),
        "fixedMatrixPerspectiveLabels": build_persona_perspective_labels(code),
        "normalizedDecisionProfile": normalize_persona_for_fixed_matrix(
            {
                "id": f"{code.lower()}-{_slugify(name)}",
                "code": code,
                "role": persona or role_section.split(".")[0].strip(),
                "summary": background.split("\n\n")[0].strip(),
                "primaryStakeholders": stakeholders,
                "hardestTension": tension,
                "lens": lens,
                "kpiFamilies": kpis,
            }
        ),
        "commercialOverlay": _build_commercial_overlay(code),
        "frameworks": frameworks["frameworks"],
        "recommendedFramework": frameworks["recommended"],
    }


def _parse_scenario_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    header_match = re.search(r"^#\s+(P\d+)\s+·\s+(.+?)\s+—\s+Decision Scenario$", text, re.M)
    cross_match = re.search(r"^#\s+Scenario:\s+(.+)$", text, re.M)
    shared_across_personas = False
    persona_overrides: Dict[str, Dict[str, Any]] = {}
    if header_match:
        code, name = header_match.groups()
    elif cross_match:
        code, name = "CROSS", "All personas"
        shared_across_personas = True
    else:
        raise ValueError(f"Could not parse scenario header in {path.name}")
    domain = _extract_field(text, "Domain")
    platform = _extract_field(text, "Platform")
    persona = _extract_field(text, "Persona")
    scenario_date = _extract_field(text, "Scenario date")
    classification = _extract_field(text, "Classification")
    trigger = _extract_field(text, "Trigger")
    about = _extract_section(text, "About this scenario")
    scenario_heading_match = re.search(r"## Scenario:\s*(.+)", text)
    scenario_title = scenario_heading_match.group(1).strip() if scenario_heading_match else ""
    scenario_body = ""
    if scenario_heading_match:
      start = scenario_heading_match.end()
      next_heading = re.search(r"\n## ", text[start:])
      if next_heading:
          scenario_body = text[start : start + next_heading.start()].strip()
      else:
          scenario_body = text[start:].strip()
    options = _extract_scenario_options(scenario_body)
    call = _extract_section(text, "The call")
    tension = _extract_section(text, "Tension")
    decision_context_text = _extract_section(text, "Decision context")
    decision_context = _extract_table_rows(decision_context_text)
    kpi_text = _extract_section(text, "KPI families")
    kpis = _extract_kpis(kpi_text)
    summary = _build_header_summary(about, scenario_body, tension, call)
    if shared_across_personas:
        matches = list(
            re.finditer(
                r"###\s+(P\d+)\s+·\s+(.+?)\n(.*?)(?=\n###\s+P\d+\s+·|\n##\s+Shared KPIs|\n##\s+The meta-tension|\Z)",
                text,
                re.S,
            )
        )
        for match in matches:
            persona_code, persona_name, block = match.groups()
            decision_match = re.search(r"\*\*Decision:\*\*\s*(.+)", block)
            tension_match = re.search(r"\*\*Tension:\*\*\s*(.+)", block)
            time_match = re.search(r"\*\*Time horizon:\*\*\s*(.+)", block)
            kpi_match = re.search(r"\*\*KPIs:\*\*\s*(.+)", block)
            persona_overrides[persona_code] = {
                "personaCode": persona_code,
                "personaName": persona_name.strip(),
                "decision": decision_match.group(1).strip() if decision_match else "",
                "tension": tension_match.group(1).strip() if tension_match else tension,
                "timeHorizon": time_match.group(1).strip() if time_match else "",
                "kpis": [
                    {"code": item.split(" ", 1)[0].strip(), "label": item.strip()}
                    for item in re.split(r",\s*", kpi_match.group(1).strip())
                    if item.strip()
                ] if kpi_match else [],
                "options": _extract_options_from_section(block),
                "summary": "\n\n".join(
                    part
                    for part in [
                        _clean_schema_text(decision_match.group(1).strip()) if decision_match else "",
                        f"Tension: {_clean_schema_text(tension_match.group(1).strip())}" if tension_match else "",
                        f"Time horizon: {_clean_schema_text(time_match.group(1).strip())}" if time_match else "",
                    ]
                    if part
                ),
                "explanation": _collapse_markdown_text(block),
                "keywords": _keywords(persona_name, block),
            }
    return {
        "id": f"{code.lower()}-{_slugify(path.stem.replace('_Scenario', ''))}-scenario",
        "code": code,
        "name": f"{code} scenario",
        "label": scenario_title or (cross_match.group(1).strip() if cross_match else f"{name} scenario"),
        "personaCode": code,
        "personaName": name,
        "domain": domain,
        "platform": platform,
        "persona": persona,
        "scenarioDate": scenario_date,
        "classification": classification,
        "trigger": trigger,
        "about": about,
        "scenarioTitle": scenario_title,
        "scenarioBody": scenario_body,
        "summary": summary,
        "call": call,
        "tension": tension,
        "decisionContext": decision_context,
        "kpiFamilies": kpis,
        "options": options,
        "sharedAcrossPersonas": shared_across_personas,
        "personaOverrides": persona_overrides,
        "scenarioKinds": ["commercial-contracts"] if _is_commercial_context(domain, platform, scenario_title, summary, tension, call, about) else [],
        "keywords": _keywords(scenario_title, summary, tension, call, *(item["label"] for item in kpis)),
        "normalizedScenarioProfile": normalize_scenario_for_fixed_matrix(
            {
                "id": f"{code.lower()}-{_slugify(path.stem.replace('_Scenario', ''))}-scenario",
                "scenarioTitle": scenario_title,
                "label": scenario_title or (cross_match.group(1).strip() if cross_match else f"{name} scenario"),
                "summary": summary,
                "about": about,
                "tension": tension,
                "decisionContext": decision_context,
                "options": options,
                "kpiFamilies": kpis,
                "scenarioKinds": ["commercial-contracts"] if _is_commercial_context(domain, platform, scenario_title, summary, tension, call, about) else [],
                "sharedAcrossPersonas": shared_across_personas,
            }
        ),
    }


def _parse_scenario_pack_file(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    pack_title_match = re.search(r"^##\s+(.+Scenario Pack)$", text, re.M)
    pack_title = pack_title_match.group(1).strip() if pack_title_match else path.stem.replace("_", " ")

    scenario_matches = list(
        re.finditer(
            r"^##\s+Scenario\s+(\d+)\s+·\s+(.+?)\n(.*?)(?=^##\s+Scenario\s+\d+\s+·|\Z)",
            text,
            re.M | re.S,
        )
    )

    scenarios: List[Dict[str, Any]] = []
    for match in scenario_matches:
        number, title, block = match.groups()
        trigger = _extract_section_body(block, "### Trigger")
        tension = _extract_section_body(block, "### Decision tension")
        commercial_variance = _extract_section_body(block, "### Commercial variance")
        compliance_variance = _extract_section_body(block, "### Compliance variance")
        bid_variance = _extract_section_body(block, "### Bid variance")
        options_text = _extract_section_body(block, "### Options")
        kpi_text = _extract_section_body(block, "### KPI families")
        options = _extract_pack_options(options_text)
        kpis = _extract_pack_kpis(kpi_text)
        summary = _build_pack_summary(trigger, tension, options)
        explanation = _build_pack_explanation(
            trigger,
            tension,
            options,
            commercial_variance,
            compliance_variance,
            bid_variance,
        )
        decision_context = {
            key: value
            for key, value in {
                "commercialVariance": commercial_variance.strip(),
                "complianceVariance": compliance_variance.strip(),
                "bidVariance": bid_variance.strip(),
            }.items()
            if value
        }
        scenarios.append(
            {
                "id": f"cross-{_slugify(path.stem)}-{number}-scenario",
                "code": "CROSS",
                "name": f"{pack_title} · Scenario {number}",
                "label": title.strip(),
                "personaCode": "CROSS",
                "personaName": "All personas",
                "domain": "Contracts, Commercial, Compliance & Bid Variance",
                "platform": "Port Talbot Transformation Programme",
                "persona": "All personas",
                "scenarioDate": "",
                "classification": "Shared scenario pack",
                "trigger": trigger.strip(),
                "about": trigger.strip(),
                "scenarioTitle": title.strip(),
                "scenarioBody": block.strip(),
                "summary": summary,
                "explanation": explanation,
                "call": "Choose the most defensible path across the available options.",
                "tension": tension.strip(),
                "decisionContext": decision_context,
                "kpiFamilies": kpis,
                "options": options,
                "sharedAcrossPersonas": True,
                "personaOverrides": {},
                "scenarioKinds": ["commercial-contracts", "commercial-variance", "compliance", "bids"],
                "keywords": _keywords(
                    title,
                    trigger,
                    tension,
                    commercial_variance,
                    compliance_variance,
                    bid_variance,
                    *(item["label"] for item in kpis),
                    *(item["label"] for item in options),
                ),
                "normalizedScenarioProfile": normalize_scenario_for_fixed_matrix(
                    {
                        "id": f"cross-{_slugify(path.stem)}-{number}-scenario",
                        "scenarioTitle": title.strip(),
                        "label": title.strip(),
                        "summary": summary,
                        "about": trigger.strip(),
                        "tension": tension.strip(),
                        "decisionContext": decision_context,
                        "options": options,
                        "kpiFamilies": kpis,
                        "scenarioKinds": ["commercial-contracts", "commercial-variance", "compliance", "bids"],
                        "sharedAcrossPersonas": True,
                    }
                ),
            }
        )
    return scenarios


def _parse_vo112_schema() -> Dict[str, Any]:
    if not VO112_SCHEMA_PATH.exists():
        return {}

    text = VO112_SCHEMA_PATH.read_text(encoding="utf-8")

    emotion_rows = _extract_markdown_table(_extract_section_body(text, "## Emotion profiles"))
    emotions: Dict[str, Dict[str, Any]] = {}
    for row in emotion_rows:
        code = row.get("Code", "")
        if not code:
            continue
        emotions[code] = {
            "code": code,
            "name": row.get("Name", ""),
            "displayDensity": row.get("Default density", "moderate"),
            "actionPattern": row.get("Action pattern", ""),
            "biasRisk": row.get("Bias risk", ""),
        }

    perspective_rows = _extract_markdown_table(_extract_section_body(text, "## Perspective metadata"))
    perspectives: Dict[str, Dict[str, Any]] = {}
    for row in perspective_rows:
        code = row.get("Code", "")
        tags = [item.strip() for item in row.get("Typical question tags", "").split(",") if item.strip()]
        if not code:
            continue
        perspectives[code] = {
            "code": code,
            "name": row.get("Name", ""),
            "questionTags": tags,
            "defaultChart": row.get("Default chart", ""),
        }

    personas: Dict[str, Any] = {}
    persona_matches = list(
        re.finditer(r"## (P\d+)\s+·\s+(.+?)\n(.*?)(?=\n## P\d+\s+·|\Z)", text, re.S)
    )
    for match in persona_matches:
        persona_code, persona_name, block = match.groups()
        role_match = re.search(r"\*\*Role:\*\*\s*(.+)", block)
        decision_match = re.search(r"\*\*VO-112 decision:\*\*\s*(.+)", block)
        tension_match = re.search(r"\*\*Tension:\*\*\s*(.+)", block)

        spine_rows = _extract_markdown_table(_extract_section_body(block, "### Persona KPI spine"))
        kpi_spine: List[Dict[str, Any]] = []
        kpi_lookup: Dict[str, str] = {}
        for row in spine_rows:
            perspective_text = row.get("Perspective", "")
            perspective_code = perspective_text.split(" ", 1)[0]
            kpi_label = row.get("KPI", "")
            kpi_code = kpi_label.split(" ", 1)[0]
            kpi_lookup[kpi_code] = kpi_label
            kpi_spine.append(
                {
                    "perspectiveCode": perspective_code,
                    "perspectiveLabel": perspectives.get(perspective_code, {}).get("name", perspective_text),
                    "kpiCode": kpi_code,
                    "kpiLabel": kpi_label,
                    "reading": row.get("Reading", ""),
                    "hardPriority": row.get("Hard priority", "").lower() == "yes",
                }
            )

        resolver_section = _extract_section_body(block, "### Recommended action resolver")
        resolver_hints = [_clean_schema_text(item) for item in _extract_prefixed_bullets(resolver_section)]

        cell_rows = _extract_markdown_table(_extract_section_body(block, "### Executable cells"))
        cells: Dict[str, Any] = {}
        for row in cell_rows:
            cell_id = row.get("Cell ID", "")
            emotion_code = row.get("Emotion", "").split(" ", 1)[0]
            perspective_text = row.get("Perspective", "")
            perspective_code = perspective_text.split(" ", 1)[0]
            primary_label = row.get("Primary KPI", "")
            primary_code = primary_label.split(" ", 1)[0]
            supporting_codes = [item.strip() for item in row.get("Supporting KPIs", "").split(",") if item.strip()]
            question_tags = [item.strip() for item in row.get("Question tags", "").split(",") if item.strip()]
            emotion_meta = emotions.get(emotion_code, {})
            perspective_meta = perspectives.get(perspective_code, {})

            kpis = [primary_label] + [kpi_lookup.get(code, code) for code in supporting_codes]
            route_keywords = _dedupe(
                question_tags
                + perspective_meta.get("questionTags", [])
                + _keywords(primary_label, row.get("Current state", ""))
                + _keywords(*(kpi_lookup.get(code, code) for code in supporting_codes))
                + _keywords(emotion_meta.get("name", ""), perspective_meta.get("name", ""), row.get("Action pattern", "")),
                20,
            )

            cells[cell_id] = {
                "id": cell_id,
                "personaCode": persona_code,
                "emotionCode": emotion_code,
                "emotionName": emotion_meta.get("name", emotion_code),
                "perspectiveCode": perspective_code,
                "perspectiveLabel": perspective_meta.get("name", perspective_text),
                "primaryKpi": {
                    "code": primary_code,
                    "label": primary_label,
                    "currentState": _clean_schema_text(row.get("Current state", "")),
                },
                "supportingKpis": [kpi_lookup.get(code, code) for code in supporting_codes],
                "weight": int(row.get("Weight", "0") or 0),
                "displaySlot": row.get("Display slot", ""),
                "questionTags": question_tags,
                "chartType": _clean_schema_text(row.get("Chart", "")),
                "actionPattern": _clean_schema_text(row.get("Action pattern", "")),
                "biasRisk": _clean_schema_text(row.get("Bias risk", "")),
                "blindSpotScan": row.get("Blind-spot scan", "").lower() == "true",
                "displayDensity": emotion_meta.get("displayDensity", "moderate"),
                "routeKeywords": route_keywords,
                "kpis": kpis[:3],
                "dataRequirements": _dedupe(
                    [
                        f"Current state: {_clean_schema_text(row.get('Current state', ''))}",
                        f"Supporting KPIs: {', '.join(supporting_codes)}" if supporting_codes else "",
                        f"Weighting: {row.get('Weight', '')} / {row.get('Display slot', '')}",
                        _clean_schema_text(tension_match.group(1).strip()) if tension_match else "",
                    ],
                    4,
                ),
            }

        personas[persona_code] = {
            "code": persona_code,
            "name": persona_name.strip(),
            "role": role_match.group(1).strip() if role_match else "",
            "decision": _clean_schema_text(decision_match.group(1).strip()) if decision_match else "",
            "tension": _clean_schema_text(tension_match.group(1).strip()) if tension_match else "",
            "kpiSpine": kpi_spine,
            "resolverHints": resolver_hints,
            "cells": cells,
        }

    return {
        "scenarioCodes": ["vo112", "tenova variation order cascade"],
        "emotions": emotions,
        "perspectives": perspectives,
        "personas": personas,
    }


@lru_cache(maxsize=1)
def load_matrix_bootstrap() -> Dict[str, Any]:
    persona_files = sorted(
        PERSONA_DIR.glob("P*.md"),
        key=lambda path: int(re.search(r"P(\d+)", path.name).group(1)),
    )
    personas = [_parse_persona_file(path) for path in persona_files]
    scenario_files = sorted(
        list(SCENARIO_DIR.glob("P*_Scenario.md")) + list(SCENARIO_DIR.glob("CROSS*.md")),
        key=lambda path: (
            999 if not re.search(r"P(\d+)", path.name) else int(re.search(r"P(\d+)", path.name).group(1)),
            path.name,
        ),
    )
    scenarios: List[Dict[str, Any]] = []
    for path in scenario_files:
        if "Scenario_Pack" in path.name:
            scenarios.extend(_parse_scenario_pack_file(path))
        else:
            scenarios.append(_parse_scenario_file(path))
    scenario_map: Dict[str, List[Dict[str, Any]]] = {}
    for scenario in scenarios:
        if scenario.get("sharedAcrossPersonas"):
            for persona in personas:
                scenario_map.setdefault(persona["code"], []).append(scenario)
        else:
            scenario_map.setdefault(scenario["personaCode"], []).append(scenario)
    for persona in personas:
        persona_scenarios: List[Dict[str, Any]] = []
        for scenario in scenario_map.get(persona["code"], []):
            scenario_copy = dict(scenario)
            normalized_scenario = dict(scenario_copy.get("normalizedScenarioProfile", {}))
            fixed_runtime = build_fixed_matrix_cell_runtime(
                persona.get("normalizedDecisionProfile", {}),
                normalized_scenario,
            )
            normalized_scenario["visible_data_catalog"] = fixed_runtime["visibleDataCatalog"]
            scenario_copy["normalizedScenarioProfile"] = normalized_scenario
            scenario_copy["fixedMatrixCellData"] = fixed_runtime["cells"]
            scenario_copy["fixedMatrixVisibleDataCatalog"] = fixed_runtime["visibleDataCatalog"]
            persona_scenarios.append(scenario_copy)
        persona["scenarios"] = persona_scenarios
        persona["defaultScenarioId"] = persona["scenarios"][0]["id"] if persona["scenarios"] else ""
    return {
        "project": PROJECT,
        "domains": DOMAINS,
        "platforms": PLATFORMS,
        "fixedDecisionFramework": build_fixed_matrix_bootstrap(),
        "personas": personas,
        "scenarios": scenarios,
        "commercialLogic": {
            "universalKpis": COMMERCIAL_KPI_CATALOG,
            "questionFamilies": COMMERCIAL_QUESTION_FAMILIES,
            "personaEmphasis": PERSONA_COMMERCIAL_EMPHASIS,
        },
        "vo112Schema": _parse_vo112_schema(),
        "defaultPersonaId": personas[0]["id"] if personas else "",
    }
