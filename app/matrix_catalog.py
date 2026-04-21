import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
PERSONA_DIR = ROOT / "data" / "personas"
SCENARIO_DIR = ROOT / "data" / "scenarios"

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
        options.append(
            {
                "code": code.replace("Option ", ""),
                "label": label.strip(),
                "summary": normalized,
                "risk": risk,
                "keywords": _keywords(label, normalized),
            }
        )
    return options


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
        "frameworks": frameworks["frameworks"],
        "recommendedFramework": frameworks["recommended"],
    }


def _parse_scenario_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    header_match = re.search(r"^#\s+(P\d+)\s+·\s+(.+?)\s+—\s+Decision Scenario$", text, re.M)
    if not header_match:
        raise ValueError(f"Could not parse scenario header in {path.name}")
    code, name = header_match.groups()
    domain = _extract_field(text, "Domain")
    platform = _extract_field(text, "Platform")
    persona = _extract_field(text, "Persona")
    scenario_date = _extract_field(text, "Scenario date")
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
    summary = " ".join(line.strip() for line in scenario_body.splitlines()[:2] if line.strip())
    return {
        "id": f"{code.lower()}-{_slugify(path.stem.replace('_Scenario', ''))}-scenario",
        "code": code,
        "name": f"{code} scenario",
        "label": scenario_title or f"{name} scenario",
        "personaCode": code,
        "personaName": name,
        "domain": domain,
        "platform": platform,
        "persona": persona,
        "scenarioDate": scenario_date,
        "about": about,
        "scenarioTitle": scenario_title,
        "scenarioBody": scenario_body,
        "summary": summary,
        "call": call,
        "tension": tension,
        "decisionContext": decision_context,
        "kpiFamilies": kpis,
        "options": options,
        "keywords": _keywords(scenario_title, summary, tension, call, *(item["label"] for item in kpis)),
    }


@lru_cache(maxsize=1)
def load_matrix_bootstrap() -> Dict[str, Any]:
    persona_files = sorted(
        PERSONA_DIR.glob("P*.md"),
        key=lambda path: int(re.search(r"P(\d+)", path.name).group(1)),
    )
    personas = [_parse_persona_file(path) for path in persona_files]
    scenario_files = sorted(
        SCENARIO_DIR.glob("P*_Scenario.md"),
        key=lambda path: int(re.search(r"P(\d+)", path.name).group(1)),
    )
    scenarios = [_parse_scenario_file(path) for path in scenario_files]
    scenario_map: Dict[str, List[Dict[str, Any]]] = {}
    for scenario in scenarios:
        scenario_map.setdefault(scenario["personaCode"], []).append(scenario)
    for persona in personas:
        persona["scenarios"] = scenario_map.get(persona["code"], [])
        persona["defaultScenarioId"] = persona["scenarios"][0]["id"] if persona["scenarios"] else ""
    return {
        "project": PROJECT,
        "domains": DOMAINS,
        "platforms": PLATFORMS,
        "personas": personas,
        "scenarios": scenarios,
        "defaultPersonaId": personas[0]["id"] if personas else "",
    }
