import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
HYBRID_MATRIX_LOGIC_PATH = ROOT_DIR / "all_personas_hybrid_matrix_logic.md"
PERSONA_MODEL_RATIONALE_PATH = ROOT_DIR / "persona_model_assignment_rationale_pack.md"


DECISION_LENSES: List[Dict[str, str]] = [
    {"code": "cautious", "label": "Cautious"},
    {"code": "strategic", "label": "Strategic"},
    {"code": "decisive", "label": "Decisive"},
    {"code": "analytical", "label": "Analytical"},
]

CANONICAL_PERSPECTIVES: List[Dict[str, str]] = [
    {"code": "self", "label": "Self / Personal Risk"},
    {"code": "stakeholder", "label": "Stakeholder / People"},
    {"code": "business", "label": "Business / Outcome"},
    {"code": "ethics", "label": "Ethics / Governance"},
]

CELL_SPECS: List[Dict[str, Any]] = [
    {
        "emotion": "Cautious",
        "emotionCode": "cautious",
        "perspective": "Self / Personal Risk",
        "perspectiveCode": "self",
        "primary_fit": "Prospect Theory",
        "secondary_fit": "Expected Utility",
        "support_fit": "COM-B",
        "decision_style": "Loss-averse, regret-minimizing, exposure-sensitive",
        "best_data_to_show": [
            "Worst-case downside",
            "Personal exposure level",
            "Reversibility of the choice",
            "Confidence / certainty level",
            "Safest viable next step",
        ],
        "why_this_data": "This cell needs information that reduces fear of loss, clarifies downside, and makes the safest reasonable action visible.",
        "persona_adjustment": "Increase emphasis on whatever the persona is personally accountable for—career risk, patient risk, financial exposure, public blame, or operational ownership.",
    },
    {
        "emotion": "Strategic",
        "emotionCode": "strategic",
        "perspective": "Self / Personal Risk",
        "perspectiveCode": "self",
        "primary_fit": "Expected Utility",
        "secondary_fit": "Dual-Process",
        "support_fit": "OODA",
        "decision_style": "Long-horizon self-protection with trade-off awareness",
        "best_data_to_show": [
            "Long-term payoff vs short-term comfort",
            "Opportunity cost",
            "Second-order consequences",
            "Scenario comparison over time",
            "3-month vs 12-month outcome view",
        ],
        "why_this_data": "This cell supports people who are thinking ahead and need to protect their long-term position, not just immediate comfort.",
        "persona_adjustment": "Weight future authority, reputation, mandate, and role continuity differently depending on the persona.",
    },
    {
        "emotion": "Decisive",
        "emotionCode": "decisive",
        "perspective": "Self / Personal Risk",
        "perspectiveCode": "self",
        "primary_fit": "OODA",
        "secondary_fit": "Recognition-Primed Decision",
        "support_fit": "Bounded Rationality",
        "decision_style": "Fast action with acceptable personal exposure",
        "best_data_to_show": [
            "Immediate next move",
            "Time window for action",
            "Quick consequence of acting now",
            "Fallback plan",
            "Immediate check before action",
        ],
        "why_this_data": "This cell supports quick decision-making and helps the user move without overthinking, while still containing exposure.",
        "persona_adjustment": "Focus the checks on the persona's real exposure—legal, reputational, operational, or medical.",
    },
    {
        "emotion": "Analytical",
        "emotionCode": "analytical",
        "perspective": "Self / Personal Risk",
        "perspectiveCode": "self",
        "primary_fit": "Expected Utility",
        "secondary_fit": "Dual-Process",
        "support_fit": "Bounded Rationality",
        "decision_style": "Careful self-risk comparison before commitment",
        "best_data_to_show": [
            "Weighted comparison of options",
            "Probability estimates",
            "Key assumptions",
            "Missing information",
            "Decision threshold / stop rule",
        ],
        "why_this_data": "This cell needs structured comparison so the user can reason clearly without spiraling into endless analysis.",
        "persona_adjustment": "Adjust the weighting model to the persona's actual exposure profile and decision authority.",
    },
    {
        "emotion": "Cautious",
        "emotionCode": "cautious",
        "perspective": "Stakeholder / People",
        "perspectiveCode": "stakeholder",
        "primary_fit": "Prospect Theory",
        "secondary_fit": "COM-B",
        "support_fit": "Dual-Process",
        "decision_style": "Harm-avoidant and people-protective",
        "best_data_to_show": [
            "Who is at risk",
            "Human downside severity",
            "Trust impact",
            "Adoption or support friction",
            "Least harmful rollout path",
        ],
        "why_this_data": "This cell needs human consequence data so the decision is not reduced to abstract logic.",
        "persona_adjustment": "Prioritize stakeholder groups differently depending on the persona—patients, workers, citizens, customers, investors, or internal teams.",
    },
    {
        "emotion": "Strategic",
        "emotionCode": "strategic",
        "perspective": "Stakeholder / People",
        "perspectiveCode": "stakeholder",
        "primary_fit": "Expected Utility",
        "secondary_fit": "COM-B",
        "support_fit": "Dual-Process",
        "decision_style": "Multi-stakeholder balancing and coalition building",
        "best_data_to_show": [
            "Stakeholder map",
            "Who gains and who loses",
            "Coalition support strength",
            "Adoption readiness",
            "Long-term trust effect",
        ],
        "why_this_data": "This cell is about balancing interests and making a decision that can hold across multiple groups.",
        "persona_adjustment": "Persona changes who counts as the key stakeholder and how much weight relationship durability should get.",
    },
    {
        "emotion": "Decisive",
        "emotionCode": "decisive",
        "perspective": "Stakeholder / People",
        "perspectiveCode": "stakeholder",
        "primary_fit": "OODA",
        "secondary_fit": "COM-B",
        "support_fit": "Recognition-Primed Decision",
        "decision_style": "Fast coordinated action across people",
        "best_data_to_show": [
            "Who needs to act now",
            "People blockers",
            "Communication priority order",
            "Action owner",
            "Immediate people-risk",
        ],
        "why_this_data": "This cell supports urgent coordination and fast execution through others.",
        "persona_adjustment": "Align the coordination view with the persona's real span of control and influence.",
    },
    {
        "emotion": "Analytical",
        "emotionCode": "analytical",
        "perspective": "Stakeholder / People",
        "perspectiveCode": "stakeholder",
        "primary_fit": "Dual-Process",
        "secondary_fit": "Expected Utility",
        "support_fit": "COM-B",
        "decision_style": "Structured comparison of social impact",
        "best_data_to_show": [
            "Stakeholder impact table",
            "Likely reactions",
            "Sentiment / trust indicators",
            "Fairness trade-offs",
            "Decision justification",
        ],
        "why_this_data": "This cell helps analytical users avoid being logically correct but socially blind.",
        "persona_adjustment": "Shift the stakeholder-impact model based on whose trust or consent matters most for the persona.",
    },
    {
        "emotion": "Cautious",
        "emotionCode": "cautious",
        "perspective": "Business / Outcome",
        "perspectiveCode": "business",
        "primary_fit": "Expected Utility",
        "secondary_fit": "Prospect Theory",
        "support_fit": "Bounded Rationality",
        "decision_style": "Downside-protective but outcome-aware",
        "best_data_to_show": [
            "Downside-adjusted value",
            "Cost of failure",
            "Risk exposure",
            "Contingency buffer",
            "Safest viable business option",
        ],
        "why_this_data": "This cell helps the user protect the business from downside without freezing action entirely.",
        "persona_adjustment": "Tailor the definition of business downside to the persona—margin, capital, schedule, supply, customer loss, or throughput.",
    },
    {
        "emotion": "Strategic",
        "emotionCode": "strategic",
        "perspective": "Business / Outcome",
        "perspectiveCode": "business",
        "primary_fit": "Expected Utility",
        "secondary_fit": "OODA",
        "support_fit": "Dual-Process",
        "decision_style": "Long-term value optimization under uncertainty",
        "best_data_to_show": [
            "Expected value",
            "Strategic upside",
            "Scenario tree",
            "Competitive impact",
            "Option value / flexibility",
        ],
        "why_this_data": "This cell supports strategic optimization, especially where future states and adaptability matter.",
        "persona_adjustment": "Increase emphasis on the business outcomes that sit closest to the persona's mandate.",
    },
    {
        "emotion": "Decisive",
        "emotionCode": "decisive",
        "perspective": "Business / Outcome",
        "perspectiveCode": "business",
        "primary_fit": "OODA",
        "secondary_fit": "Recognition-Primed Decision",
        "support_fit": "Bounded Rationality",
        "decision_style": "Fastest executable path to the target outcome",
        "best_data_to_show": [
            "Immediate next action",
            "Time-to-impact",
            "Operational bottleneck",
            "Current status signal",
            "Short-term business consequence",
        ],
        "why_this_data": "This cell supports execution under pressure and reduces delay caused by over-analysis.",
        "persona_adjustment": "Adapt the action and bottleneck logic to the persona's operational remit.",
    },
    {
        "emotion": "Analytical",
        "emotionCode": "analytical",
        "perspective": "Business / Outcome",
        "perspectiveCode": "business",
        "primary_fit": "Expected Utility",
        "secondary_fit": "Bounded Rationality",
        "support_fit": "Dual-Process",
        "decision_style": "Structured comparison of outcome quality and feasibility",
        "best_data_to_show": [
            "Criteria-weight table",
            "ROI / payoff estimate",
            "Confidence interval",
            "Evidence quality",
            "Decision threshold",
        ],
        "why_this_data": "This cell supports rigorous comparison while guarding against endless refinement.",
        "persona_adjustment": "Match criteria weights to the persona's responsibilities, incentives, and authority.",
    },
    {
        "emotion": "Cautious",
        "emotionCode": "cautious",
        "perspective": "Ethics / Governance",
        "perspectiveCode": "ethics",
        "primary_fit": "Prospect Theory",
        "secondary_fit": "Dual-Process",
        "support_fit": "COM-B",
        "decision_style": "Breach-avoidant, duty-sensitive, reputation-protective",
        "best_data_to_show": [
            "Ethical or legal red lines",
            "Compliance exposure",
            "Public defensibility",
            "Harm potential",
            "Safest ethical path",
        ],
        "why_this_data": "This cell must make the boundaries and downside of crossing them very clear.",
        "persona_adjustment": "Emphasize the governance lens that matters most to the persona—medical ethics, public duty, fiduciary duty, compliance, or safety.",
    },
    {
        "emotion": "Strategic",
        "emotionCode": "strategic",
        "perspective": "Ethics / Governance",
        "perspectiveCode": "ethics",
        "primary_fit": "Dual-Process",
        "secondary_fit": "Expected Utility",
        "support_fit": "COM-B",
        "decision_style": "Legitimacy-preserving strategy with principled reflection",
        "best_data_to_show": [
            "Long-term trust impact",
            "Governance implications",
            "Precedent risk",
            "Fairness considerations",
            "Defensibility over time",
        ],
        "why_this_data": "This cell supports choices that must remain legitimate, explainable, and sustainable over time.",
        "persona_adjustment": "Weight whichever legitimacy system most constrains the persona—board, regulator, public, profession, or institution.",
    },
    {
        "emotion": "Decisive",
        "emotionCode": "decisive",
        "perspective": "Ethics / Governance",
        "perspectiveCode": "ethics",
        "primary_fit": "Dual-Process",
        "secondary_fit": "OODA",
        "support_fit": "Bounded Rationality",
        "decision_style": "Fast action constrained by hard red lines",
        "best_data_to_show": [
            "Non-negotiable boundaries",
            "Immediate compliance or ethics check",
            "Stop / go trigger",
            "Required approval or escalation point",
            "Irreversible harm warning",
        ],
        "why_this_data": "This cell allows action under pressure without accidentally crossing ethical or governance limits.",
        "persona_adjustment": "Make the red-line checks specific to the persona's real duties and escalation obligations.",
    },
    {
        "emotion": "Analytical",
        "emotionCode": "analytical",
        "perspective": "Ethics / Governance",
        "perspectiveCode": "ethics",
        "primary_fit": "Dual-Process",
        "secondary_fit": "Expected Utility",
        "support_fit": "Bounded Rationality",
        "decision_style": "Careful principled reasoning with explicit justification",
        "best_data_to_show": [
            "Policy or rule alignment",
            "Ethical trade-off analysis",
            "Precedent consistency",
            "Justification logic",
            "Missing governance evidence",
        ],
        "why_this_data": "This cell supports careful reasoning about duty, consistency, and defensibility.",
        "persona_adjustment": "Align the justification structure to the norms and obligations of the persona's domain.",
    },
]

PERSONA_PERSPECTIVE_UI_LABELS: Dict[str, Dict[str, str]] = {
    "P1": {
        "self": "Leadership / Personal Exposure",
        "stakeholder": "Government / Workforce Trust",
        "business": "Delivery / Transformation Outcome",
        "ethics": "Institutional Trust / Governance",
    },
    "P2": {
        "self": "Leadership / Workforce Stability",
        "stakeholder": "Workforce Trust / Union Climate",
        "business": "Skills / Readiness Outcome",
        "ethics": "Institutional Fairness / Transition Legitimacy",
    },
    "P3": {
        "self": "Personal Accountability / Programme Control",
        "stakeholder": "Contractor / Site Trust",
        "business": "Delivery / Critical Path",
        "ethics": "Compliance / Change Control",
    },
    "P4": {
        "self": "Capital Protection / Downside Exposure",
        "stakeholder": "Stakeholder Confidence / Market Signaling",
        "business": "Programme Value / Financial Outcome",
        "ethics": "Governance / Grant / Covenant Compliance",
    },
    "P5": {
        "self": "Leadership / Member Accountability",
        "stakeholder": "Workforce Trust / Solidarity",
        "business": "Transition Outcome / Jobs Protection",
        "ethics": "Institutional Fairness / Public Defensibility",
    },
    "P6": {
        "self": "Director Exposure / Materiality",
        "stakeholder": "Stakeholder Trust / Political Relationship",
        "business": "Enterprise Outcome / Strategic Stewardship",
        "ethics": "Governance / Disclosure / Auditability",
    },
    "P7": {
        "self": "Supply Security / Personal Accountability",
        "stakeholder": "Supplier Trust / Negotiation Leverage",
        "business": "Cost / Availability Outcome",
        "ethics": "Contract Integrity / Commercial Defensibility",
    },
    "P8": {
        "self": "Competitive Position / Personal Exposure",
        "stakeholder": "Government / Utility / Stakeholder Alignment",
        "business": "Energy Outcome / Cost Curve",
        "ethics": "Contract / Regulatory Defensibility",
    },
    "P9": {
        "self": "Political Exposure / Public Leadership",
        "stakeholder": "Community Trust / Stakeholder Confidence",
        "business": "Local Regeneration Outcome",
        "ethics": "Institutional Legitimacy / Public Defensibility",
    },
    "P10": {
        "self": "Revenue / Personal Account Exposure",
        "stakeholder": "Customer Trust / Market Signaling",
        "business": "Commercial Outcome / Offtake Security",
        "ethics": "Contract Credibility / Qualification Defensibility",
    },
}

PERSONA_DEFAULT_EMOTION_TENDENCY: Dict[str, str] = {
    "P1": "strategic",
    "P2": "cautious",
    "P3": "decisive",
    "P4": "analytical",
    "P5": "cautious",
    "P6": "strategic",
    "P7": "analytical",
    "P8": "analytical",
    "P9": "cautious",
    "P10": "strategic",
}

PERSONA_DEFAULT_PERSPECTIVE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "P1": {"self": 0.20, "stakeholder": 0.25, "business": 0.35, "ethics": 0.20},
    "P2": {"self": 0.20, "stakeholder": 0.35, "business": 0.20, "ethics": 0.25},
    "P3": {"self": 0.25, "stakeholder": 0.20, "business": 0.40, "ethics": 0.15},
    "P4": {"self": 0.20, "stakeholder": 0.15, "business": 0.40, "ethics": 0.25},
    "P5": {"self": 0.20, "stakeholder": 0.40, "business": 0.15, "ethics": 0.25},
    "P6": {"self": 0.15, "stakeholder": 0.20, "business": 0.25, "ethics": 0.40},
    "P7": {"self": 0.20, "stakeholder": 0.20, "business": 0.40, "ethics": 0.20},
    "P8": {"self": 0.20, "stakeholder": 0.15, "business": 0.40, "ethics": 0.25},
    "P9": {"self": 0.15, "stakeholder": 0.40, "business": 0.15, "ethics": 0.30},
    "P10": {"self": 0.20, "stakeholder": 0.25, "business": 0.40, "ethics": 0.15},
}

VISIBLE_DATA_TYPES: List[Dict[str, str]] = [
    {"code": "downside", "label": "Worst-case downside"},
    {"code": "reversibility", "label": "Reversibility of the choice"},
    {"code": "confidence", "label": "Confidence / certainty level"},
    {"code": "expected_value", "label": "Expected value"},
    {"code": "option_value", "label": "Option value / flexibility"},
    {"code": "stakeholder_map", "label": "Stakeholder map"},
    {"code": "trust_impact", "label": "Trust impact"},
    {"code": "harm_potential", "label": "Harm potential"},
    {"code": "bottleneck", "label": "Operational bottleneck"},
    {"code": "time_window", "label": "Time window for action"},
    {"code": "threshold", "label": "Threshold / red line"},
    {"code": "missing_evidence", "label": "Missing evidence"},
    {"code": "defensibility", "label": "Defensibility over time"},
    {"code": "approval_requirement", "label": "Approval requirement"},
]

VISIBLE_DATA_TYPE_ALIASES: Dict[str, List[str]] = {
    "downside": [
        "Worst-case downside",
        "Cost of failure",
        "Risk exposure",
        "Human downside severity",
        "Immediate people-risk",
        "Short-term business consequence",
        "Irreversible harm warning",
    ],
    "reversibility": [
        "Reversibility of the choice",
        "Fallback plan",
        "Safest viable next step",
        "Least harmful rollout path",
        "Stop / go trigger",
        "Safest ethical path",
    ],
    "confidence": [
        "Confidence / certainty level",
        "Confidence interval",
        "Current status signal",
        "Probability estimates",
        "Key assumptions",
        "Evidence quality",
    ],
    "expected_value": [
        "Expected value",
        "ROI / payoff estimate",
        "Downside-adjusted value",
        "Long-term payoff vs short-term comfort",
        "Strategic upside",
    ],
    "option_value": [
        "Option value / flexibility",
        "Opportunity cost",
        "Scenario tree",
        "Scenario comparison over time",
        "3-month vs 12-month outcome view",
        "Second-order consequences",
    ],
    "stakeholder_map": [
        "Stakeholder map",
        "Who is at risk",
        "Who gains and who loses",
        "Who needs to act now",
        "Communication priority order",
        "Action owner",
    ],
    "trust_impact": [
        "Trust impact",
        "Long-term trust effect",
        "Public defensibility",
        "Sentiment / trust indicators",
        "Coalition support strength",
        "Likely reactions",
    ],
    "harm_potential": [
        "Harm potential",
        "Ethical or legal red lines",
        "Fairness considerations",
        "Fairness trade-offs",
        "Non-negotiable boundaries",
    ],
    "bottleneck": [
        "Operational bottleneck",
        "People blockers",
        "Adoption or support friction",
        "Adoption readiness",
        "Immediate next action",
    ],
    "time_window": [
        "Time window for action",
        "Time-to-impact",
        "Quick consequence of acting now",
        "Immediate check before action",
    ],
    "threshold": [
        "Threshold / red line",
        "Decision threshold / stop rule",
        "Decision threshold",
        "Required approval or escalation point",
        "Immediate compliance or ethics check",
        "Compliance exposure",
        "Policy or rule alignment",
    ],
    "missing_evidence": [
        "Missing information",
        "Missing governance evidence",
        "Decision justification",
        "Justification logic",
    ],
    "defensibility": [
        "Defensibility over time",
        "Precedent risk",
        "Precedent consistency",
        "Governance implications",
        "Ethical trade-off analysis",
    ],
    "approval_requirement": [
        "Required approval or escalation point",
        "Public defensibility",
        "Governance implications",
        "Immediate compliance or ethics check",
    ],
}

TYPE_PERSPECTIVE_RELEVANCE: Dict[str, Dict[str, float]] = {
    "downside": {"self": 0.95, "stakeholder": 0.70, "business": 0.85, "ethics": 0.75},
    "reversibility": {"self": 0.75, "stakeholder": 0.60, "business": 0.80, "ethics": 0.70},
    "confidence": {"self": 0.70, "stakeholder": 0.55, "business": 0.80, "ethics": 0.75},
    "expected_value": {"self": 0.55, "stakeholder": 0.40, "business": 1.00, "ethics": 0.45},
    "option_value": {"self": 0.75, "stakeholder": 0.55, "business": 0.95, "ethics": 0.60},
    "stakeholder_map": {"self": 0.35, "stakeholder": 1.00, "business": 0.55, "ethics": 0.65},
    "trust_impact": {"self": 0.45, "stakeholder": 0.95, "business": 0.60, "ethics": 0.90},
    "harm_potential": {"self": 0.55, "stakeholder": 0.90, "business": 0.45, "ethics": 1.00},
    "bottleneck": {"self": 0.60, "stakeholder": 0.75, "business": 0.90, "ethics": 0.45},
    "time_window": {"self": 0.70, "stakeholder": 0.65, "business": 0.90, "ethics": 0.60},
    "threshold": {"self": 0.65, "stakeholder": 0.55, "business": 0.70, "ethics": 1.00},
    "missing_evidence": {"self": 0.65, "stakeholder": 0.60, "business": 0.80, "ethics": 0.85},
    "defensibility": {"self": 0.55, "stakeholder": 0.75, "business": 0.65, "ethics": 1.00},
    "approval_requirement": {"self": 0.55, "stakeholder": 0.65, "business": 0.70, "ethics": 0.95},
}

TYPE_LENS_RELEVANCE: Dict[str, Dict[str, float]] = {
    "downside": {"cautious": 1.00, "strategic": 0.55, "decisive": 0.65, "analytical": 0.70},
    "reversibility": {"cautious": 0.75, "strategic": 0.85, "decisive": 0.55, "analytical": 0.65},
    "confidence": {"cautious": 0.80, "strategic": 0.60, "decisive": 0.45, "analytical": 1.00},
    "expected_value": {"cautious": 0.45, "strategic": 1.00, "decisive": 0.60, "analytical": 0.95},
    "option_value": {"cautious": 0.60, "strategic": 1.00, "decisive": 0.55, "analytical": 0.75},
    "stakeholder_map": {"cautious": 0.70, "strategic": 0.85, "decisive": 0.80, "analytical": 0.70},
    "trust_impact": {"cautious": 0.80, "strategic": 0.90, "decisive": 0.55, "analytical": 0.75},
    "harm_potential": {"cautious": 0.95, "strategic": 0.70, "decisive": 0.65, "analytical": 0.75},
    "bottleneck": {"cautious": 0.45, "strategic": 0.65, "decisive": 1.00, "analytical": 0.70},
    "time_window": {"cautious": 0.55, "strategic": 0.70, "decisive": 1.00, "analytical": 0.65},
    "threshold": {"cautious": 0.90, "strategic": 0.65, "decisive": 0.85, "analytical": 0.85},
    "missing_evidence": {"cautious": 0.70, "strategic": 0.60, "decisive": 0.35, "analytical": 1.00},
    "defensibility": {"cautious": 0.85, "strategic": 0.90, "decisive": 0.50, "analytical": 0.85},
    "approval_requirement": {"cautious": 0.75, "strategic": 0.70, "decisive": 0.85, "analytical": 0.65},
}

TYPE_MODEL_RELEVANCE: Dict[str, Dict[str, float]] = {
    "downside": {"Prospect Theory": 1.00, "Expected Utility": 0.75, "Dual-Process": 0.55, "OODA": 0.45, "Recognition-Primed Decision": 0.40, "Bounded Rationality": 0.60, "COM-B": 0.40},
    "reversibility": {"Prospect Theory": 0.55, "Expected Utility": 0.75, "Dual-Process": 0.50, "OODA": 0.70, "Recognition-Primed Decision": 0.55, "Bounded Rationality": 0.65, "COM-B": 0.45},
    "confidence": {"Prospect Theory": 0.50, "Expected Utility": 0.90, "Dual-Process": 0.80, "OODA": 0.45, "Recognition-Primed Decision": 0.40, "Bounded Rationality": 0.95, "COM-B": 0.50},
    "expected_value": {"Prospect Theory": 0.45, "Expected Utility": 1.00, "Dual-Process": 0.65, "OODA": 0.55, "Recognition-Primed Decision": 0.45, "Bounded Rationality": 0.75, "COM-B": 0.35},
    "option_value": {"Prospect Theory": 0.55, "Expected Utility": 0.95, "Dual-Process": 0.70, "OODA": 0.75, "Recognition-Primed Decision": 0.45, "Bounded Rationality": 0.60, "COM-B": 0.35},
    "stakeholder_map": {"Prospect Theory": 0.45, "Expected Utility": 0.65, "Dual-Process": 0.70, "OODA": 0.70, "Recognition-Primed Decision": 0.45, "Bounded Rationality": 0.35, "COM-B": 1.00},
    "trust_impact": {"Prospect Theory": 0.55, "Expected Utility": 0.55, "Dual-Process": 0.90, "OODA": 0.40, "Recognition-Primed Decision": 0.35, "Bounded Rationality": 0.40, "COM-B": 0.95},
    "harm_potential": {"Prospect Theory": 0.85, "Expected Utility": 0.50, "Dual-Process": 0.95, "OODA": 0.35, "Recognition-Primed Decision": 0.30, "Bounded Rationality": 0.50, "COM-B": 0.75},
    "bottleneck": {"Prospect Theory": 0.30, "Expected Utility": 0.50, "Dual-Process": 0.35, "OODA": 1.00, "Recognition-Primed Decision": 0.80, "Bounded Rationality": 0.65, "COM-B": 0.70},
    "time_window": {"Prospect Theory": 0.35, "Expected Utility": 0.55, "Dual-Process": 0.40, "OODA": 1.00, "Recognition-Primed Decision": 0.75, "Bounded Rationality": 0.55, "COM-B": 0.45},
    "threshold": {"Prospect Theory": 0.70, "Expected Utility": 0.80, "Dual-Process": 0.75, "OODA": 0.65, "Recognition-Primed Decision": 0.35, "Bounded Rationality": 0.75, "COM-B": 0.60},
    "missing_evidence": {"Prospect Theory": 0.30, "Expected Utility": 0.90, "Dual-Process": 0.75, "OODA": 0.25, "Recognition-Primed Decision": 0.20, "Bounded Rationality": 1.00, "COM-B": 0.30},
    "defensibility": {"Prospect Theory": 0.60, "Expected Utility": 0.80, "Dual-Process": 1.00, "OODA": 0.35, "Recognition-Primed Decision": 0.25, "Bounded Rationality": 0.60, "COM-B": 0.75},
    "approval_requirement": {"Prospect Theory": 0.45, "Expected Utility": 0.65, "Dual-Process": 0.85, "OODA": 0.55, "Recognition-Primed Decision": 0.30, "Bounded Rationality": 0.45, "COM-B": 0.80},
}


def _slug(value: str) -> str:
    return value.lower().replace(" / ", "-").replace(" ", "-")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("---", " ")).strip(" -")


def _sanitize_signal(label: str) -> str:
    text = re.sub(r"\([^)]*\)", "", label or "")
    text = text.replace("—", " ").replace("/", " ")
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text[:160]


def _lower_blob(parts: List[str]) -> str:
    return " ".join(part.lower() for part in parts if part)


def _first_matching_signal(items: List[str], keywords: List[str]) -> str:
    for item in items:
        lowered = item.lower()
        if any(keyword in lowered for keyword in keywords):
            return item
    return items[0] if items else ""


def _preview(summary: str) -> str:
    summary = _clean_text(summary)
    if len(summary) <= 132:
        return summary
    truncated = summary[:129].rsplit(" ", 1)[0].strip()
    return f"{truncated}..."


def _compact_value(summary: str, limit: int = 84) -> str:
    summary = _clean_text(summary)
    if len(summary) <= limit:
        return summary
    truncated = summary[: max(20, limit - 3)].rsplit(" ", 1)[0].strip()
    return f"{truncated}..."


def _read_optional_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_md_subsection(body: str, title: str) -> str:
    match = re.search(
        rf"^### {re.escape(title)}\n(.*?)(?=^### |\Z)",
        body,
        flags=re.M | re.S,
    )
    return match.group(1).strip() if match else ""


def _canonical_perspective_code(label: str) -> str:
    lowered = _clean_text(label).lower()
    if lowered.startswith("self /"):
        return "self"
    if lowered.startswith("stakeholder /"):
        return "stakeholder"
    if lowered.startswith("business /"):
        return "business"
    if lowered.startswith("ethics /"):
        return "ethics"
    if lowered.startswith("personal accountability") or lowered.startswith("leadership /") or lowered.startswith("director exposure"):
        return "self"
    if lowered.startswith("contractor /") or lowered.startswith("government /") or lowered.startswith("workforce trust /") or lowered.startswith("community trust /") or lowered.startswith("customer trust /") or lowered.startswith("supplier trust /") or lowered.startswith("stakeholder trust /"):
        return "stakeholder"
    if lowered.startswith("delivery /") or lowered.startswith("skills /") or lowered.startswith("programme value /") or lowered.startswith("transition outcome /") or lowered.startswith("enterprise outcome /") or lowered.startswith("cost /") or lowered.startswith("energy outcome /") or lowered.startswith("local regeneration") or lowered.startswith("commercial outcome /"):
        return "business"
    if lowered.startswith("compliance /") or lowered.startswith("institutional") or lowered.startswith("governance /") or lowered.startswith("contract integrity /") or lowered.startswith("contract /") or lowered.startswith("institutional legitimacy /") or lowered.startswith("contract credibility /"):
        return "ethics"
    return ""


def _emotion_code(label: str) -> str:
    lowered = _clean_text(label).lower()
    for item in DECISION_LENSES:
        if lowered == item["label"].lower():
            return item["code"]
    return ""


@lru_cache(maxsize=1)
def _load_hybrid_matrix_logic() -> Dict[str, Dict[str, Any]]:
    text = _read_optional_markdown(HYBRID_MATRIX_LOGIC_PATH)
    personas: Dict[str, Dict[str, Any]] = {}
    if not text:
        return personas

    pattern = re.compile(r"^## (P\d+)\s+·\s*([^\n]+)\n(.*?)(?=^## P\d+\s+·|\Z)", re.M | re.S)
    for match in pattern.finditer(text):
        code, heading, body = match.groups()
        perspective_lines = [
            re.sub(r"^\d+\.\s*", "", line).strip()
            for line in _extract_md_subsection(body, "Perspectives").splitlines()
            if re.match(r"^\d+\.\s+", line.strip())
        ]
        perspective_map: Dict[str, str] = {}
        for canonical, label in zip(["self", "stakeholder", "business", "ethics"], perspective_lines[:4]):
            perspective_map[canonical] = label
        value_pool = [
            re.sub(r"^-+\s*", "", line).strip()
            for line in _extract_md_subsection(body, "Value pool").splitlines()
            if line.strip().startswith("-")
        ]
        decision_voice = [
            re.sub(r"^-+\s*", "", line).strip()
            for line in _extract_md_subsection(body, "Decision voice").splitlines()
            if line.strip().startswith("-")
        ]
        personas[code] = {
            "heading": heading.strip(),
            "perspective_labels": perspective_map,
            "value_pool": value_pool,
            "decision_voice": decision_voice,
        }
    return personas


@lru_cache(maxsize=1)
def _load_persona_model_assignments() -> Dict[str, Dict[str, Dict[str, Any]]]:
    text = _read_optional_markdown(PERSONA_MODEL_RATIONALE_PATH)
    assignments: Dict[str, Dict[str, Dict[str, Any]]] = {}
    if not text:
        return assignments

    pattern = re.compile(r"^# (P\d+)\s+·\s*([^\n]+)\n(.*?)(?=^# P\d+\s+·|\Z)", re.M | re.S)
    for match in pattern.finditer(text):
        code, _heading, body = match.groups()
        persona_cells: Dict[str, Dict[str, Any]] = {}
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line.startswith("|"):
                continue
            columns = [part.strip() for part in line.strip("|").split("|")]
            if len(columns) < 7:
                continue
            if columns[0] == "Cell" or set("".join(columns)) <= {"-", ":", " "}:
                continue
            if "×" not in columns[0]:
                continue
            emotion_label, perspective_label = [part.strip() for part in columns[0].split("×", 1)]
            emotion_code = _emotion_code(emotion_label)
            perspective_code = _canonical_perspective_code(perspective_label)
            if not emotion_code or not perspective_code:
                continue
            persona_cells[f"{emotion_code}::{perspective_code}"] = {
                "primary_fit": columns[1],
                "secondary_fit": columns[3],
                "support_fit": columns[5],
                "stack_rationale": {
                    "primary": columns[2],
                    "secondary": columns[4],
                    "support": columns[6],
                },
            }
        if persona_cells:
            assignments[code] = persona_cells
    return assignments


def _persona_logic(persona_code: str) -> Dict[str, Any]:
    return _load_hybrid_matrix_logic().get(persona_code, {})


def _persona_stack_override(persona_code: str, cell_id: str) -> Dict[str, Any]:
    return _load_persona_model_assignments().get(persona_code, {}).get(cell_id, {})


def _confidence_band(normalized_scenario: Dict[str, Any]) -> str:
    context_count = len(normalized_scenario.get("decision_context", {}))
    option_count = len(normalized_scenario.get("options", []))
    signal_count = len(normalized_scenario.get("source_kpis", []))
    total = context_count + option_count + signal_count
    if total >= 14:
        return "high"
    if total >= 9:
        return "medium"
    return "low"


def _visible_data_type_from_label(label: str) -> str:
    normalized = _clean_text(label).lower()
    for type_code, aliases in VISIBLE_DATA_TYPE_ALIASES.items():
        for alias in aliases:
            if normalized == alias.lower():
                return type_code
    for type_code, aliases in VISIBLE_DATA_TYPE_ALIASES.items():
        if any(alias.lower() in normalized or normalized in alias.lower() for alias in aliases):
            return type_code
    return "confidence"


def _build_visible_data_catalog(normalized_persona: Dict[str, Any], normalized_scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    scenario_summary = _clean_text(normalized_scenario.get("scenario_summary", ""))
    tension = _clean_text(normalized_scenario.get("tension", ""))
    decision_context = normalized_scenario.get("decision_context", {}) or {}
    context_values = [_clean_text(str(value)) for value in decision_context.values() if _clean_text(str(value))]
    source_signals = [_sanitize_signal(item.get("label", "")) for item in normalized_scenario.get("source_kpis", []) if item.get("label")]
    option_summaries = [
        _clean_text(" ".join(part for part in [item.get("label", ""), item.get("summary", ""), item.get("risk", "")] if part))
        for item in normalized_scenario.get("options", [])
    ]
    role = normalized_persona.get("role", "")
    stakeholders = normalized_persona.get("priority_stakeholders", []) or []
    authority_level = normalized_persona.get("authority_level", "functional")
    governance_constraints = normalized_persona.get("governance_constraints", []) or []
    scenario_blob = _lower_blob([scenario_summary, tension] + context_values + source_signals + option_summaries)
    all_signals = [item for item in context_values + source_signals + option_summaries if item]
    confidence_band = _confidence_band(normalized_scenario)

    downside_signal = _first_matching_signal(
        all_signals,
        ["risk", "delay", "cost", "exposure", "clawback", "breach", "slip", "harm", "premium", "sentiment"],
    )
    reversibility_signal = _first_matching_signal(
        option_summaries or all_signals,
        ["partial", "quietly", "privately", "amend", "defer", "wait", "hold", "phase", "fallback"],
    )
    bottleneck_signal = _first_matching_signal(
        source_signals or all_signals,
        ["schedule", "grid", "supplier", "quality", "construction", "commissioning", "delivery", "float", "readiness"],
    )
    threshold_signal = _first_matching_signal(
        context_values + source_signals,
        ["grant", "covenant", "threshold", "material", "milestone", "compliance", "approval", "board", "regulator", "notify"],
    )
    trust_signal = _first_matching_signal(
        context_values + source_signals,
        ["trust", "relationship", "public", "media", "political", "union", "customer", "community", "government", "audit"],
    )
    expected_signal = _first_matching_signal(
        context_values + source_signals,
        ["revenue", "margin", "cost", "premium", "cash", "funding", "demand", "value", "throughput", "headroom"],
    )

    stakeholder_summary = ", ".join(stakeholders[:4]) if stakeholders else "the stakeholders already visible in the scenario"
    options_count = len(normalized_scenario.get("options", []))
    source_count = len(source_signals)

    catalog: List[Dict[str, Any]] = [
        {
            "type": "downside",
            "label": "Worst-case downside",
            "summary": _clean_text(
                f"The main downside sits in {downside_signal or tension or scenario_summary or 'the exposed decision path'}, which is where the scenario concentrates the most immediate damage if the call is wrong."
            ),
            "evidence": [item for item in [downside_signal, tension] if item][:3],
        },
        {
            "type": "reversibility",
            "label": "Reversibility of the choice",
            "summary": _clean_text(
                f"The most reversible path is {reversibility_signal or 'the option that preserves room to amend or pause later'}, so the matrix can separate moves that keep optionality from moves that harden the position early."
            ),
            "evidence": [item for item in [reversibility_signal] + option_summaries[:2] if item][:3],
        },
        {
            "type": "confidence",
            "label": "Confidence / certainty level",
            "summary": f"Confidence is {confidence_band} because this scenario currently exposes {source_count} source signals across {options_count} live options and {len(context_values)} structured context anchors.",
            "evidence": [scenario_summary][:1] + source_signals[:2],
        },
        {
            "type": "expected_value",
            "label": "Expected value",
            "summary": _clean_text(
                f"The expected value lens is driven by {expected_signal or 'the biggest business payoff or loss signal in the scenario'}, which is where upside and downside most clearly compound over time."
            ),
            "evidence": [item for item in [expected_signal] + context_values[:2] if item][:3],
        },
        {
            "type": "option_value",
            "label": "Option value / flexibility",
            "summary": _clean_text(
                f"Option value is highest where the team can preserve multiple routes through {reversibility_signal or 'the currently open set of options'}, rather than locking into an irreversible commitment too early."
            ),
            "evidence": option_summaries[:3],
        },
        {
            "type": "stakeholder_map",
            "label": "Stakeholder map",
            "summary": _clean_text(
                f"The people map is anchored on {stakeholder_summary}, with scenario pressure centering on {trust_signal or 'the relationships named in the current context'}."
            ),
            "evidence": [item for item in [decision_context.get("Stakeholders", ""), trust_signal] if _clean_text(str(item))][:3],
        },
        {
            "type": "trust_impact",
            "label": "Trust impact",
            "summary": _clean_text(
                f"The trust consequence runs through {trust_signal or 'how the decision will be seen by the stakeholders around it'}, which determines whether support strengthens or erodes after the call."
            ),
            "evidence": [item for item in [trust_signal] + context_values[:2] if item][:3],
        },
        {
            "type": "harm_potential",
            "label": "Harm potential",
            "summary": _clean_text(
                f"The harm lens is concentrated around {downside_signal or trust_signal or tension or 'the highest-severity failure mode'}, which is the area that becomes hardest to recover if ignored."
            ),
            "evidence": [item for item in [downside_signal, trust_signal] if item][:3],
        },
        {
            "type": "bottleneck",
            "label": "Operational bottleneck",
            "summary": _clean_text(
                f"The likely bottleneck is {bottleneck_signal or 'the operational dependency currently constraining progress'}, which is the choke point most likely to slow delivery or decision execution."
            ),
            "evidence": [item for item in [bottleneck_signal] + source_signals[:2] if item][:3],
        },
        {
            "type": "time_window",
            "label": "Time window for action",
            "summary": _clean_text(
                f"The action window is defined by {decision_context.get('Timehorizon', '') or threshold_signal or 'the timing signal in the scenario'}, which sets how long the team can delay before the path hardens."
            ),
            "evidence": [item for item in [_clean_text(str(decision_context.get('Timehorizon', ''))), threshold_signal] if item][:3],
        },
        {
            "type": "threshold",
            "label": "Threshold / red line",
            "summary": _clean_text(
                f"The clearest threshold sits at {threshold_signal or 'the governance or performance trigger embedded in the scenario'}, which is where the decision changes from discretionary to mandatory."
            ),
            "evidence": [item for item in [threshold_signal] + context_values[:2] if item][:3],
        },
        {
            "type": "missing_evidence",
            "label": "Missing evidence",
            "summary": _clean_text(
                f"The main evidence gap is around {source_signals[1] if len(source_signals) > 1 else source_signals[0] if source_signals else 'the next signal needed to validate the call'}, which is the data most likely to change confidence if it becomes clearer."
            ),
            "evidence": source_signals[:3],
        },
        {
            "type": "defensibility",
            "label": "Defensibility over time",
            "summary": _clean_text(
                f"Defensibility depends on whether the eventual choice can still be justified against {trust_signal or threshold_signal or 'the governance and stakeholder record'} once the outcome becomes visible."
            ),
            "evidence": [item for item in [threshold_signal, trust_signal] if item][:3],
        },
        {
            "type": "approval_requirement",
            "label": "Approval requirement",
            "summary": _clean_text(
                f"The most likely approval boundary sits with {authority_level == 'enterprise' and 'enterprise-level governance bodies or external authorities' or 'the role holder and their immediate governance chain'}, especially where {threshold_signal or 'the scenario crosses a disclosure, funding, or legitimacy line'}."
            ),
            "evidence": [_clean_text(str(item)) for item in governance_constraints[:2]] + [item for item in [threshold_signal] if item][:1],
        },
    ]
    for item in catalog:
        item["preview"] = _preview(item["summary"])
    return catalog


def _headline_fragment(text: str) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .:-")
    parts = [part.strip() for part in re.split(r"[;,.]|(?:\s+-\s+)", cleaned) if part.strip()]
    candidate = parts[0] if parts else cleaned
    lowered = candidate.lower()
    for prefix in [
        "the ",
        "approximately ",
        "about ",
        "around ",
        "current read on ",
        "whether ",
        "amount of ",
        "risk of ",
        "likelihood of ",
        "status of ",
        "impact on ",
        "value of ",
    ]:
        if lowered.startswith(prefix):
            candidate = candidate[len(prefix):]
            break
    if "critical path" in candidate.lower():
        return "Critical Path Slip"
    words = candidate.split()
    if len(words) > 4:
        candidate = " ".join(words[:4])
    return candidate.strip(" .:-").title()


def _scenario_subject_for_heading(
    primary_item: Dict[str, Any],
    normalized_persona: Dict[str, Any],
    normalized_scenario: Dict[str, Any],
    perspective_code: str,
) -> str:
    candidates: List[str] = []
    decision_context = normalized_scenario.get("decision_context", {}) or {}
    source_kpis = normalized_scenario.get("source_kpis", []) or []
    priority_stakeholders = normalized_persona.get("priority_stakeholders", []) or []

    if perspective_code == "stakeholder":
        candidates.extend([_clean_text(str(item)) for item in priority_stakeholders])
    if perspective_code == "ethics":
        candidates.extend([
            _clean_text(str(decision_context.get("Compliancefocus", ""))),
            _clean_text(str(decision_context.get("Governancefocus", ""))),
            _clean_text(str(decision_context.get("Commercialvariance", ""))),
        ])
    if perspective_code == "business":
        candidates.extend([_clean_text(str(item.get("label") or "")) for item in source_kpis])

    candidates.extend([_clean_text(str(item)) for item in (primary_item.get("evidence") or [])])
    candidates.append(_clean_text(str(primary_item.get("label") or "")))
    candidates.extend([_clean_text(str(item.get("label") or "")) for item in source_kpis])
    candidates.extend([_clean_text(str(value)) for value in decision_context.values()])
    candidates.append(_clean_text(str(normalized_scenario.get("scenario_title") or "")))

    for candidate in candidates:
        fragment = _headline_fragment(candidate)
        if not fragment:
            continue
        if fragment.lower() in {
            "expected value",
            "option value",
            "confidence",
            "threshold / red line",
            "missing evidence",
            "ceo",
            "cfo",
            "chro",
            "board chair",
            "commercial director",
            "project director",
            "head of energy",
            "head of scrap procurement",
        }:
            continue
        return fragment

    fallback = _headline_fragment(str(primary_item.get("label") or "")) or "Decision Path"
    return fallback


def _title_for_visible_type(
    type_code: str,
    emotion_code: str,
    primary_item: Dict[str, Any],
    normalized_persona: Dict[str, Any],
    normalized_scenario: Dict[str, Any],
    perspective_code: str,
) -> str:
    subject = _scenario_subject_for_heading(primary_item, normalized_persona, normalized_scenario, perspective_code)
    templates = {
        "downside": {"cautious": "Protect {subject}", "strategic": "Preserve {subject}", "decisive": "Contain {subject}", "analytical": "Quantify {subject}"},
        "reversibility": {"cautious": "Keep {subject} Recoverable", "strategic": "Preserve {subject} Options", "decisive": "Keep {subject} Open", "analytical": "Test {subject} Reversibility"},
        "confidence": {"cautious": "Stabilize {subject}", "strategic": "Back the {subject} Read", "decisive": "Move on {subject}", "analytical": "Test {subject} Confidence"},
        "expected_value": {"cautious": "Protect {subject}", "strategic": "Back {subject}", "decisive": "Move on {subject}", "analytical": "Compare {subject}"},
        "option_value": {"cautious": "Avoid Locking {subject}", "strategic": "Preserve {subject}", "decisive": "Keep {subject} Open", "analytical": "Compare {subject}"},
        "stakeholder_map": {"cautious": "Protect {subject}", "strategic": "Hold {subject}", "decisive": "Mobilize {subject}", "analytical": "Compare {subject}"},
        "trust_impact": {"cautious": "Protect {subject}", "strategic": "Preserve {subject}", "decisive": "Stabilize {subject}", "analytical": "Test {subject}"},
        "harm_potential": {"cautious": "Prevent {subject} Harm", "strategic": "Avoid Lasting {subject} Harm", "decisive": "Stop {subject} Damage", "analytical": "Test {subject} Exposure"},
        "bottleneck": {"cautious": "Protect {subject}", "strategic": "Unlock {subject}", "decisive": "Clear {subject}", "analytical": "Verify {subject}"},
        "time_window": {"cautious": "Protect {subject} Timing", "strategic": "Use The {subject} Window", "decisive": "Move {subject} Now", "analytical": "Test {subject} Timing"},
        "threshold": {"cautious": "Respect The {subject} Trigger", "strategic": "Avoid Crossing {subject}", "decisive": "Act At {subject}", "analytical": "Test {subject}"},
        "missing_evidence": {"cautious": "Do Not Overreach {subject}", "strategic": "Close {subject} Gap", "decisive": "Get The {subject} Read", "analytical": "Close {subject} Gap"},
        "defensibility": {"cautious": "Keep {subject} Defensible", "strategic": "Protect {subject}", "decisive": "Act Without Breaking {subject}", "analytical": "Justify {subject}"},
        "approval_requirement": {"cautious": "Keep {subject} Approved", "strategic": "Protect {subject}", "decisive": "Secure {subject}", "analytical": "Test {subject}"},
    }
    template = templates.get(type_code, {}).get(emotion_code, "Make The {subject} Call")
    return template.format(subject=subject).strip()


def _best_value_text(primary_item: Dict[str, Any], normalized_scenario: Dict[str, Any]) -> str:
    type_code = primary_item.get("type") or ""
    candidates = [
        *(primary_item.get("evidence") or []),
        *[item.get("label", "") for item in normalized_scenario.get("source_kpis", []) if item.get("label")],
        *[str(value) for value in (normalized_scenario.get("decision_context", {}) or {}).values()],
    ]
    cleaned = [_clean_text(item) for item in candidates if _clean_text(item)]
    numeric_pattern = r"[£$€%]|\b\d+(?:\.\d+)?\s*(?:weeks?|wks?|days?|roles?|SMEs?|MWh|MW|months?|conditions?|count|target|coverage|float|delay|extension|consumed|remaining)\b"
    numeric = next((item for item in cleaned if re.search(numeric_pattern, item, flags=re.I)), "")
    if numeric:
        return numeric
    if type_code == "stakeholder_map" and cleaned:
        first = cleaned[0]
        stakeholder_count = max(2, len([item for item in re.split(r",\s*", first) if item.strip()]))
        return f"{stakeholder_count} priority stakeholders in play"
    if type_code in {"trust_impact", "defensibility", "approval_requirement"} and cleaned:
        compact = cleaned[0]
        if len(compact) > 88:
            return _compact_value(compact)
        return compact
    if cleaned:
        compact = cleaned[0]
        if len(compact) > 88:
            return _compact_value(compact)
        return compact
    return primary_item.get("label") or "Signal not yet quantified"


def _decision_for_visible_type(
    emotion_code: str,
    primary_item: Dict[str, Any],
    normalized_persona: Dict[str, Any],
    normalized_scenario: Dict[str, Any],
) -> str:
    type_code = primary_item.get("type") or ""
    signal = _clean_text(primary_item.get("label") or "the leading signal")
    value_text = _best_value_text(primary_item, normalized_scenario)
    voice = normalized_persona.get("decision_voice") or []
    role = normalized_persona.get("role") or "this role"
    scenario_title = normalized_scenario.get("scenario_title") or "this scenario"

    if emotion_code == "cautious":
        if type_code in {"downside", "harm_potential", "threshold", "approval_requirement"}:
            return f"Do not commit further until {signal.lower()} is back inside a safer range."
        if type_code in {"trust_impact", "stakeholder_map"}:
            return f"Protect trust first and avoid a move that burns support before the path is defensible."
        return f"Stay inside the safer route while {signal.lower()} remains the main live constraint."
    if emotion_code == "strategic":
        if type_code in {"expected_value", "option_value", "defensibility"}:
            return f"Choose the path that preserves the strongest long-term outcome while keeping flexibility alive."
        if type_code in {"trust_impact", "stakeholder_map"}:
            return f"Keep the coalition together and choose the route that ages best beyond the immediate pressure."
        return f"Preserve optionality while {signal.lower()} still determines the long-term position."
    if emotion_code == "decisive":
        if type_code in {"bottleneck", "time_window"}:
            return f"Act now on the live blocker before the window tightens further."
        if type_code in {"threshold", "approval_requirement"}:
            return f"Escalate and act immediately once {signal.lower()} reaches the trigger."
        return f"Move quickly on {signal.lower()} and remove the main blocker to progress."
    if type_code in {"missing_evidence", "confidence"}:
        return f"Verify the missing evidence before committing, then act on the strongest supported path."
    if type_code in {"expected_value", "option_value"}:
        return f"Compare the trade-off carefully and commit only when the stronger value path is clear."
    return f"Test the trade-off around {signal.lower()} before locking the decision for {role} in {scenario_title}."


def _persona_relevance(
    type_code: str,
    normalized_persona: Dict[str, Any],
    cell: Dict[str, Any],
    candidate: Dict[str, Any],
) -> float:
    weights = normalized_persona.get("default_perspective_weights", {}) or {}
    base = float(weights.get(cell["perspectiveCode"], 0.25))
    role = (normalized_persona.get("role", "") or "").lower()
    stakeholders = normalized_persona.get("priority_stakeholders", []) or []
    label_blob = _lower_blob([candidate.get("label", ""), candidate.get("summary", "")] + stakeholders)
    if type_code in {"stakeholder_map", "trust_impact"} and stakeholders:
        base += 0.20
    if type_code in {"approval_requirement", "defensibility", "threshold"} and any(term in role for term in ["ceo", "cfo", "chair", "director", "head"]):
        base += 0.15
    if type_code in {"expected_value", "option_value", "bottleneck"} and any(term in role for term in ["director", "commercial", "project", "supply", "cfo", "ceo"]):
        base += 0.15
    if type_code == "harm_potential" and ("worker" in label_blob or "community" in label_blob or "safety" in label_blob):
        base += 0.10
    return min(1.0, max(0.0, base))


def _score_visible_data_for_cell(
    candidate: Dict[str, Any],
    cell: Dict[str, Any],
    normalized_persona: Dict[str, Any],
) -> Dict[str, float]:
    type_code = candidate["type"]
    perspective_score = TYPE_PERSPECTIVE_RELEVANCE.get(type_code, {}).get(cell["perspectiveCode"], 0.50)
    primary_score = TYPE_MODEL_RELEVANCE.get(type_code, {}).get(cell["primary_fit"], 0.50)
    emotion_score = TYPE_LENS_RELEVANCE.get(type_code, {}).get(cell["emotionCode"], 0.50)
    persona_score = _persona_relevance(type_code, normalized_persona, cell, candidate)
    correction_models = [cell.get("secondary_fit", ""), cell.get("support_fit", "")]
    correction_score = max(TYPE_MODEL_RELEVANCE.get(type_code, {}).get(model, 0.45) for model in correction_models)
    total = (
        (0.30 * perspective_score)
        + (0.30 * primary_score)
        + (0.20 * emotion_score)
        + (0.15 * persona_score)
        + (0.05 * correction_score)
    )
    return {
        "perspective": round(perspective_score, 4),
        "primary_model": round(primary_score, 4),
        "emotion": round(emotion_score, 4),
        "persona": round(persona_score, 4),
        "correction": round(correction_score, 4),
        "total": round(total, 4),
    }


def build_fixed_matrix_cell_runtime(
    normalized_persona: Dict[str, Any],
    normalized_scenario: Dict[str, Any],
) -> Dict[str, Any]:
    persona_code = normalized_persona.get("persona_code", "")
    catalog = _build_visible_data_catalog(normalized_persona, normalized_scenario)
    catalog_by_type = {item["type"]: item for item in catalog}
    cells: List[Dict[str, Any]] = []
    for cell in build_fixed_matrix_cells():
        cell_spec = {**cell, **_persona_stack_override(persona_code, cell["id"])}
        desired_types = []
        for label in cell_spec.get("best_data_to_show", []):
            type_code = _visible_data_type_from_label(label)
            if type_code not in desired_types:
                desired_types.append(type_code)
        ranked_items: List[Dict[str, Any]] = []
        for type_code in desired_types:
            candidate = catalog_by_type.get(type_code)
            if not candidate:
                continue
            scores = _score_visible_data_for_cell(candidate, cell_spec, normalized_persona)
            ranked_items.append(
                {
                    **candidate,
                    "matchedFrom": next(
                        (label for label in cell_spec.get("best_data_to_show", []) if _visible_data_type_from_label(label) == type_code),
                        candidate["label"],
                    ),
                    "score": scores["total"],
                    "scoreBreakdown": scores,
                }
            )
        ranked_items.sort(key=lambda item: (-item["score"], desired_types.index(item["type"])))
        display_data = _dynamic_display_data(ranked_items, normalized_scenario)
        top_item = ranked_items[0] if ranked_items else {}
        cell_face = {
            "title": _title_for_visible_type(
                str(top_item.get("type") or ""),
                cell_spec["emotionCode"],
                top_item,
                normalized_persona,
                normalized_scenario,
                cell_spec["perspectiveCode"],
            ),
            "value": _best_value_text(top_item, normalized_scenario),
            "decision": _decision_for_visible_type(cell_spec["emotionCode"], top_item, normalized_persona, normalized_scenario),
        } if top_item else {
            "title": "Review the signal",
            "value": "No value signal available yet",
            "decision": "Open the cell to inspect the strongest available evidence before acting.",
        }
        if display_data:
            cell_face["title"] = ""
            cell_face["value"] = " · ".join(
                f"{item.get('val', '').strip()} {item.get('label', '').strip()}".strip()
                for item in display_data[:2]
            )
        preview_items = [
            {
                "label": item["label"],
                "preview": item["preview"],
                "score": item["score"],
                "rag": item.get("rag", ""),
                "value": item.get("value", ""),
            }
            for item in ranked_items[:2]
        ]
        cells.append(
            {
                "id": cell_spec["id"],
                "decisionLens": cell_spec["emotion"],
                "decisionLensCode": cell_spec["emotionCode"],
                "canonicalPerspective": cell_spec["perspective"],
                "canonicalPerspectiveCode": cell_spec["perspectiveCode"],
                "decisionStyle": cell_spec["decision_style"],
                "whyThisData": cell_spec["why_this_data"],
                "frameworkStack": {
                    "primary": cell_spec["primary_fit"],
                    "secondary": cell_spec["secondary_fit"],
                    "support": cell_spec["support_fit"],
                },
                "frameworkStackHint": f"{cell_spec['primary_fit']} -> {cell_spec['secondary_fit']} -> {cell_spec['support_fit']}",
                "stackRationale": cell_spec.get("stack_rationale") or {},
                "cellFace": cell_face,
                "preview": preview_items,
                "rankedVisibleData": ranked_items,
                "displayData": display_data,
            }
        )
    return {
        "visibleDataCatalog": catalog,
        "cells": cells,
    }


MODEL_TYPE_PRIORITIES: Dict[str, List[str]] = {
    "Prospect Theory": ["downside", "harm_potential", "threshold", "reversibility", "trust_impact"],
    "Expected Utility": ["expected_value", "option_value", "confidence", "threshold", "defensibility"],
    "Bounded Rationality": ["missing_evidence", "confidence", "threshold", "approval_requirement", "bottleneck"],
    "Dual-Process": ["defensibility", "trust_impact", "harm_potential", "confidence", "stakeholder_map"],
    "Recognition-Primed Decision": ["bottleneck", "time_window", "stakeholder_map", "threshold", "reversibility"],
    "OODA": ["time_window", "bottleneck", "threshold", "reversibility", "approval_requirement"],
    "COM-B": ["stakeholder_map", "bottleneck", "approval_requirement", "trust_impact", "reversibility"],
}

MODEL_ROLE_EXPLANATIONS: Dict[str, str] = {
    "Prospect Theory": "The primary model protects against downside before it optimizes upside.",
    "Expected Utility": "The primary model compares likely value across the plausible paths.",
    "Bounded Rationality": "The primary model trims the decision to what can be defended with the evidence already available.",
    "Dual-Process": "The primary model balances principled reasoning with practical judgement.",
    "Recognition-Primed Decision": "The primary model looks for the familiar action pattern that fits the live situation.",
    "OODA": "The primary model favors an executable move that can be observed and adjusted quickly.",
    "COM-B": "The primary model tests whether people, capability, and environment can actually support the move.",
}

def _extract_numeric_signal(candidates: List[str]) -> str:
    numeric_pattern = r"(?:[£$€]\s?\d[\d.,]*(?:–\d[\d.,]*)?(?:[MKk]|\s?(?:m|bn|MWh|MW|t|yrs?|yr|months?|mths|weeks?|wks?|days?|hrs?|hours?))?|~?\d[\d.,]*(?:–\d[\d.,]*)?\s?(?:%|weeks?|wks?|days?|hrs?|hours?|months?|mths|yrs?|yr|roles?|conditions?|calls?|stakeholders?|scenarios?|t|MWh|MW))"
    for candidate in candidates:
        cleaned = _clean_text(candidate)
        if not cleaned:
            continue
        match = re.search(numeric_pattern, cleaned, flags=re.I)
        if match:
            return match.group(0).strip()
    return ""


def _display_value_for_item(item: Dict[str, Any], normalized_scenario: Dict[str, Any]) -> str:
    evidence = [str(piece or "") for piece in (item.get("evidence") or [])]
    summary = [str(item.get("summary") or ""), str(item.get("preview") or ""), str(item.get("label") or "")]
    numeric = _extract_numeric_signal(evidence + summary)
    if numeric:
        return numeric
    type_code = str(item.get("type") or "")
    if type_code == "stakeholder_map":
        stakeholder_text = " ".join(evidence + summary)
        stakeholder_count = max(2, len([part for part in re.split(r",\s*", stakeholder_text) if _clean_text(part)]))
        return f"{stakeholder_count}"
    if type_code in {"confidence", "expected_value", "option_value", "defensibility"}:
        score = float(item.get("score") or 0.0)
        if score >= 0.82:
            return "High"
        if score >= 0.62:
            return "Medium"
        return "Low"
    if type_code == "missing_evidence":
        return "Gap"
    if type_code in {"threshold", "approval_requirement"}:
        return "Trigger"
    if type_code == "time_window":
        return "Window"
    compact = _headline_fragment(str(item.get("label") or ""))
    return compact.split()[0] if compact else "Signal"


def _display_rag_for_item(item: Dict[str, Any]) -> str:
    type_code = str(item.get("type") or "")
    score = float(item.get("score") or 0.0)
    if type_code in {"downside", "harm_potential", "threshold", "approval_requirement", "missing_evidence"}:
        return "r" if score >= 0.62 else "y"
    if type_code in {"bottleneck", "time_window", "trust_impact", "stakeholder_map", "reversibility"}:
        return "y" if score >= 0.58 else "g"
    return "g" if score >= 0.76 else "y"


def _display_label_for_item(item: Dict[str, Any]) -> str:
    generic_labels = {
        "worst-case downside",
        "reversibility of the choice",
        "confidence / certainty level",
        "expected value",
        "option value / flexibility",
        "stakeholder map",
        "trust impact",
        "harm potential",
        "operational bottleneck",
        "time window for action",
        "threshold / red line",
        "missing evidence",
        "defensibility over time",
        "approval requirement",
    }
    label = _clean_text(str(item.get("label") or ""))
    type_code = str(item.get("type") or "")
    summary = _clean_text(str(item.get("summary") or ""))
    evidence = [_clean_text(str(piece or "")) for piece in (item.get("evidence") or []) if _clean_text(str(piece or ""))]
    if label.lower() not in generic_labels:
        return label

    if type_code == "confidence":
        for candidate in evidence[1:] + evidence[:1]:
            fragment = _headline_fragment(candidate)
            if fragment:
                return fragment

    summary_patterns = [
        r"main downside sits in (.*?), which",
        r"most reversible path is (.*?), so",
        r"expected value lens is driven by (.*?), which",
        r"people map is anchored on (.*?), with",
        r"trust consequence runs through (.*?), which",
        r"harm lens is concentrated around (.*?), which",
        r"likely bottleneck is (.*?), which",
        r"action window is defined by (.*?), which",
        r"clearest threshold sits at (.*?), which",
        r"main evidence gap is around (.*?), which",
        r"eventual choice can still be justified against (.*?), once",
        r"approval boundary sits with (.*?), especially",
    ]
    for pattern in summary_patterns:
        match = re.search(pattern, summary, flags=re.I)
        if match:
            fragment = _headline_fragment(match.group(1))
            if fragment:
                return fragment

    for candidate in evidence:
        fragment = _headline_fragment(candidate)
        if fragment:
            return fragment

    if label:
        return label
    return "Key signal"


def _dynamic_display_data(ranked_items: List[Dict[str, Any]], normalized_scenario: Dict[str, Any]) -> List[Dict[str, str]]:
    display_rows: List[Dict[str, str]] = []
    seen_labels = set()
    for item in ranked_items:
        label = _display_label_for_item(item)
        if not label or label.lower() in seen_labels:
            continue
        seen_labels.add(label.lower())
        display_rows.append(
            {
                "val": _display_value_for_item(item, normalized_scenario),
                "label": label,
                "rag": _display_rag_for_item(item),
            }
        )
        if len(display_rows) >= 3:
            break
    return display_rows


def _select_priority_item(ranked_visible_data: List[Dict[str, Any]], model_name: str, used_types: Optional[set] = None) -> Dict[str, Any]:
    used_types = used_types or set()
    priorities = MODEL_TYPE_PRIORITIES.get(model_name, [])
    candidates = [item for item in ranked_visible_data if item.get("type") not in used_types]
    if not candidates:
        return {}
    if priorities:
        ordered = sorted(
            candidates,
            key=lambda item: (
                priorities.index(item.get("type")) if item.get("type") in priorities else len(priorities) + 1,
                -float(item.get("score") or 0.0),
            ),
        )
        if ordered:
            return ordered[0]
    return max(candidates, key=lambda item: float(item.get("score") or 0.0))


def _execution_mode(question_type: str, primary_item: Dict[str, Any], confidence: float) -> str:
    primary_type = primary_item.get("type")
    if primary_type in {"missing_evidence", "confidence"} and confidence < 0.72:
        return "need_more_data"
    if question_type == "comparison":
        return "comparative_recommendation"
    if question_type in {"threshold", "consequence"} or primary_type in {"threshold", "approval_requirement", "time_window"}:
        return "conditional_recommendation"
    return "direct_recommendation"


def execute_fixed_matrix_stack(
    question: str,
    question_type: str,
    cell: Dict[str, Any],
    normalized_persona: Dict[str, Any],
    normalized_scenario: Dict[str, Any],
    confidence: float,
    preferred_visible_type: str = "",
) -> Dict[str, Any]:
    ranked_visible_data = list(cell.get("ranked_visible_data") or [])
    framework_stack = cell.get("framework_stack") or {}
    primary_model = framework_stack.get("primary") or "Expected Utility"
    secondary_model = framework_stack.get("secondary") or ""
    support_model = framework_stack.get("support") or ""
    cell_face = cell.get("cell_face") or {}
    stack_rationale = cell.get("stack_rationale") or {}

    used_types: set = set()
    if preferred_visible_type:
        primary_item = next((item for item in ranked_visible_data if item.get("type") == preferred_visible_type), {})
    else:
        primary_item = {}
    if not primary_item:
        primary_item = _select_priority_item(ranked_visible_data, primary_model, used_types)
    if primary_item.get("type"):
        used_types.add(primary_item["type"])
    secondary_item = _select_priority_item(ranked_visible_data, secondary_model, used_types) if secondary_model else {}
    if secondary_item.get("type"):
        used_types.add(secondary_item["type"])
    support_item = _select_priority_item(ranked_visible_data, support_model, used_types) if support_model else {}

    mode = _execution_mode(question_type, primary_item, confidence)
    persona_role = normalized_persona.get("role") or "the active persona"
    scenario_title = normalized_scenario.get("scenario_title") or "this scenario"
    lens = cell.get("decision_lens_label") or cell.get("decisionLens") or cell.get("emotion_mode") or "this decision lens"
    perspective = cell.get("perspective_label") or cell.get("canonicalPerspective") or cell.get("perspective_code") or "this perspective"
    primary_label = primary_item.get("label") or "the strongest visible signal"
    secondary_label = secondary_item.get("label") or "the main correction"
    support_label = support_item.get("label") or "the execution guardrail"

    if mode == "need_more_data":
        recommended_decision = f"Do not commit fully yet; verify {_lower_blob([primary_label])} before locking the decision."
    elif mode == "comparative_recommendation":
        recommended_decision = f"Favor the path that best protects {primary_label.lower()} while checking {secondary_label.lower()} before committing."
    elif mode == "conditional_recommendation":
        recommended_decision = f"Move through {lens.lower()} × {perspective.lower()} only if {primary_label.lower()} stays inside an acceptable range."
    else:
        recommended_decision = f"Prioritize {primary_label.lower()} through {lens.lower()} × {perspective.lower()} and keep {support_label.lower()} visible while acting."
    if cell_face.get("decision") and mode in {"direct_recommendation", "conditional_recommendation"}:
        recommended_decision = cell_face["decision"]

    decision_risk = (
        secondary_item.get("summary")
        or f"The main risk is underweighting {secondary_label.lower()} while the answer stays anchored to {primary_label.lower()}."
    )
    suggested_next_step = (
        support_item.get("summary")
        or f"Next, test {support_label.lower()} so the decision remains executable for {persona_role}."
    )
    reasoning_summary = (
        f"{stack_rationale.get('primary') or MODEL_ROLE_EXPLANATIONS.get(primary_model, 'The primary model shapes the main call.')} "
        f"{stack_rationale.get('secondary') or (secondary_model and f'{secondary_model} corrects the blind spot around {secondary_label.lower()}.') or ''} "
        f"{stack_rationale.get('support') or (support_model and f'{support_model} checks whether {support_label.lower()} makes the move executable.') or ''}"
    ).strip()
    watch_item = secondary_label
    missing_data = primary_label if mode == "need_more_data" else (
        next((item.get("label") for item in ranked_visible_data if item.get("type") == "missing_evidence"), "") or ""
    )

    evidence = [
        primary_item.get("summary") or primary_item.get("preview") or "",
        secondary_item.get("summary") or secondary_item.get("preview") or "",
        support_item.get("summary") or support_item.get("preview") or "",
        *(primary_item.get("evidence") or []),
        *(secondary_item.get("evidence") or []),
        *(support_item.get("evidence") or []),
    ]

    return {
        "mode": mode,
        "recommended_decision": recommended_decision.strip(),
        "decision_risk": decision_risk.strip(),
        "suggested_next_step": suggested_next_step.strip(),
        "reasoning_summary": reasoning_summary,
        "confidence": confidence,
        "watch_item": watch_item,
        "missing_data": missing_data,
        "matched_visible_data": [item for item in [primary_item, secondary_item, support_item] if item],
        "framework_stack": framework_stack,
        "cell_face": cell_face,
        "evidence_used": [item for item in evidence if item][:6],
        "execution_trace": {
            "persona_role": persona_role,
            "scenario_title": scenario_title,
            "question_type": question_type,
            "primary_model": primary_model,
            "secondary_model": secondary_model,
            "support_model": support_model,
        },
    }


def build_fixed_matrix_cells() -> List[Dict[str, Any]]:
    cells: List[Dict[str, Any]] = []
    for item in CELL_SPECS:
        cells.append(
            {
                "id": f"{item['emotionCode']}::{item['perspectiveCode']}",
                **item,
            }
        )
    return cells


def build_persona_perspective_labels(persona_code: str) -> List[Dict[str, str]]:
    labels = {
        **PERSONA_PERSPECTIVE_UI_LABELS.get(persona_code, {}),
        **(_persona_logic(persona_code).get("perspective_labels") or {}),
    }
    return [
        {
            "canonicalCode": perspective["code"],
            "canonicalLabel": perspective["label"],
            "uiLabel": labels.get(perspective["code"], perspective["label"]),
        }
        for perspective in CANONICAL_PERSPECTIVES
    ]


def normalize_persona_for_fixed_matrix(persona: Dict[str, Any]) -> Dict[str, Any]:
    code = persona.get("code", "")
    summary = persona.get("summary", "")
    role = persona.get("role", "")
    stakeholders = persona.get("primaryStakeholders", "")
    tension = persona.get("hardestTension", "")
    lens = persona.get("lens", "")
    hybrid_logic = _persona_logic(code)
    value_pool = hybrid_logic.get("value_pool") or [item["label"] for item in persona.get("kpiFamilies", [])]
    return {
        "persona_code": code,
        "persona_id": persona.get("id", ""),
        "role": role,
        "mandate": lens or summary,
        "primary_accountabilities": value_pool[:4],
        "key_risks": value_pool[4:8],
        "priority_stakeholders": [item.strip() for item in stakeholders.split(",") if item.strip()],
        "authority_level": "enterprise" if any(term in role.lower() for term in ["ceo", "cfo", "chair"]) else "functional",
        "governance_constraints": [tension] if tension else [],
        "default_decision_bias": PERSONA_DEFAULT_EMOTION_TENDENCY.get(code, "analytical"),
        "default_emotion_tendency": PERSONA_DEFAULT_EMOTION_TENDENCY.get(code, "analytical"),
        "default_perspective_weights": PERSONA_DEFAULT_PERSPECTIVE_WEIGHTS.get(
            code,
            {"self": 0.25, "stakeholder": 0.25, "business": 0.25, "ethics": 0.25},
        ),
        "perspective_labels": build_persona_perspective_labels(code),
        "decision_voice": hybrid_logic.get("decision_voice") or [],
        "hybrid_value_pool": value_pool,
    }


def normalize_scenario_for_fixed_matrix(scenario: Dict[str, Any]) -> Dict[str, Any]:
    options = scenario.get("options", []) or []
    kpis = scenario.get("kpiFamilies", []) or []
    decision_context = scenario.get("decisionContext", {}) or {}
    return {
        "scenario_id": scenario.get("id", ""),
        "scenario_title": scenario.get("scenarioTitle") or scenario.get("label") or "",
        "scenario_summary": scenario.get("summary") or scenario.get("about") or "",
        "tension": scenario.get("tension") or "",
        "decision_context": decision_context,
        "options": [
            {
                "code": item.get("code", ""),
                "label": item.get("label", ""),
                "summary": item.get("summary", ""),
                "risk": item.get("risk", ""),
            }
            for item in options
        ],
        "source_kpis": [
            {
                "code": item.get("code", ""),
                "label": item.get("label", ""),
            }
            for item in kpis
        ],
        "scenario_kinds": scenario.get("scenarioKinds", []) or [],
        "shared_across_personas": bool(scenario.get("sharedAcrossPersonas")),
    }


def build_fixed_matrix_bootstrap() -> Dict[str, Any]:
    return {
        "decisionLenses": DECISION_LENSES,
        "canonicalPerspectives": CANONICAL_PERSPECTIVES,
        "cells": build_fixed_matrix_cells(),
        "visibleDataTypes": VISIBLE_DATA_TYPES,
    }
