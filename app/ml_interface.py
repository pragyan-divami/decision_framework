import json
import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore")

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None


MODEL_DIR = Path(__file__).resolve().parent / "models"

DOMAIN_CODES = {
    "procurement": 0,
    "finance_opco": 1,
    "operations": 2,
    "sustainability": 3,
    "it_services": 4,
    "sales_fmcg": 5,
    "heavy_manufacturing": 6,
    "human_resources": 7,
    "finance_group": 8,
    "healthcare_ethics": 9,
}

SENIORITY_CODES = {
    "group_cxo": 3,
    "opco_cxo": 2,
    "bu_head": 1,
    "plant_head": 0,
}

EMOTION_CODES = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}

EMOTION_INTRINSICS = {
    "A": [0.1, 0.3, 0.4, 0.2, 0.5],
    "B": [0.7, 0.9, 0.3, 0.4, 0.6],
    "C": [0.4, 0.5, 0.9, 0.3, 0.3],
    "D": [0.8, 0.4, 0.3, 0.95, 0.4],
    "E": [0.5, 0.6, 0.2, 0.5, 0.95],
    "F": [0.6, 0.5, 0.5, 0.6, 0.6],
}


def _infer_domain(persona: Dict[str, Any]) -> str:
    domain = str(persona.get("domainPack", "")).lower()
    role = str(persona.get("roleLabel") or persona.get("role") or persona.get("raw") or "").lower()
    mapping = {
        "procurement": "procurement",
        "finance_balance_sheet": "finance_opco",
        "strategy_governance": "finance_group",
        "operations_supply_chain": "operations",
        "hr_org_behavior": "human_resources",
        "healthcare_safety": "healthcare_ethics",
        "ethics_public_trust": "healthcare_ethics",
    }
    for key, code in mapping.items():
        if key in domain:
            return code
    if "procurement" in role:
        return "procurement"
    if "cfo" in role or "finance" in role:
        return "finance_opco"
    if "plant" in role or "operations" in role or "coo" in role:
        return "operations"
    if "human resources" in role or "chro" in role or "talent" in role:
        return "human_resources"
    if "medical" in role or "clinical" in role or "ethics" in role:
        return "healthcare_ethics"
    return "procurement"


def _infer_seniority(persona: Dict[str, Any]) -> str:
    scope = str(persona.get("responsibilityScope", "")).lower()
    authority = str(persona.get("decisionAuthority", "")).lower()
    role = str(persona.get("roleLabel") or persona.get("role") or persona.get("raw") or "").lower()
    if "group" in scope or "group" in role or "executive" in authority or "board" in authority:
        return "group_cxo"
    if "cfo" in role or "coo" in role or "cso" in role or "chief" in role:
        return "opco_cxo"
    if "vp" in role or "head" in role or "director" in role:
        return "bu_head"
    if "plant" in role or "site" in role:
        return "plant_head"
    return "opco_cxo"


def _build_features(persona: Dict[str, Any], emotion_code: str, num_kpis: int, num_options: int):
    if np is None:
        return None
    domain = _infer_domain(persona)
    seniority = _infer_seniority(persona)
    features = [
        EMOTION_CODES.get(emotion_code, 0),
        *EMOTION_INTRINSICS.get(emotion_code, [0.5] * 5),
        DOMAIN_CODES.get(domain, 0),
        SENIORITY_CODES.get(seniority, 0),
        num_kpis,
        num_options,
        1.0 if domain in ("heavy_manufacturing", "healthcare_ethics") else 0.0,
        1.0 if domain in ("finance_opco", "finance_group") else 0.0,
        1.0 if domain == "human_resources" else 0.0,
        1.0 if domain == "sustainability" else 0.0,
        1.0 if seniority == "group_cxo" else 0.0,
    ]
    return np.array(features, dtype=np.float32).reshape(1, -1)


class WeightPredictor:
    def __init__(self, weight_model=None, option_model=None, option_encoder=None, eval_report: Optional[Dict[str, Any]] = None):
        self._weight_model = weight_model
        self._option_model = option_model
        self._option_encoder = option_encoder
        self.eval_report = eval_report or {}

    @classmethod
    def load(cls, model_dir: Optional[Path] = None) -> "WeightPredictor":
        d = model_dir or MODEL_DIR
        if np is None:
            return cls()
        try:
            weight_model = pickle.load(open(d / "weight_regressor.pkl", "rb"))
            option_model = pickle.load(open(d / "option_classifier.pkl", "rb"))
            option_encoder = pickle.load(open(d / "option_encoder.pkl", "rb"))
            eval_report = json.load(open(d / "eval_report.json", "r"))
            return cls(weight_model, option_model, option_encoder, eval_report)
        except Exception:
            return cls()

    @property
    def available(self) -> bool:
        return self._weight_model is not None and np is not None

    def predict_weights(self, persona: Dict[str, Any], kpis: List[Dict[str, Any]], num_options: int = 3) -> Dict[str, Dict[str, float]]:
        kpi_codes = [k["code"] for k in kpis]
        if not self.available or not kpi_codes:
            equal = round(100.0 / max(1, len(kpi_codes)), 2)
            return {code: {k: equal for k in kpi_codes} for code in "ABCDEF"}

        result: Dict[str, Dict[str, float]] = {}
        for emotion_code in "ABCDEF":
            features = _build_features(persona, emotion_code, len(kpi_codes), num_options)
            raw_weights = self._weight_model.predict(features)[0]
            total = float(raw_weights.sum())
            if total > 0:
                normalized = raw_weights / total * 100.0
            else:
                normalized = np.full(len(raw_weights), 100.0 / max(1, len(raw_weights)))
            normalized = np.maximum(normalized, 2.0)
            normalized = normalized / normalized.sum() * 100.0
            row: Dict[str, float] = {}
            for idx, code in enumerate(kpi_codes):
                if idx < len(normalized):
                    row[code] = round(float(normalized[idx]), 2)
                else:
                    row[code] = round(100.0 / max(1, len(kpi_codes)), 2)
            result[emotion_code] = row
        return result

    def weight_confidence(self) -> float:
        mae = float(self.eval_report.get("weight_overall_mae", 20.0))
        return max(0.0, min(1.0, 1.0 - mae / 20.0))

    def option_confidence(self) -> float:
        acc = float(self.eval_report.get("option_accuracy", 0.0))
        return max(0.0, min(1.0, acc))

    def summary(self) -> str:
        if not self.available:
            return "No trained ML models available"
        return (
            f"ML weights active (weight MAE={self.eval_report.get('weight_overall_mae', 'n/a')}, "
            f"option acc={self.eval_report.get('option_accuracy', 'n/a')})"
        )
