import copy as _copy
import email.parser
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

import re as _re

from decision_engine import (
    analyze_markdown,
    build_combined_doc_for_persona,
    parse_shared_scenario,
    resolve_question,
)
from matrix_catalog import PERSONA_DIR, _parse_persona_file, load_matrix_bootstrap

# In-memory cache for the last shared scenario analysis
# {persona_code: full analyze_markdown result}
_shared_cache: Dict[str, Any] = {}
_shared_scenario_meta: Dict[str, Any] = {}


ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "static"


def parse_upload(headers, rfile):
    content_type = headers.get("Content-Type", "")
    content_length = int(headers.get("Content-Length", 0))
    body = rfile.read(content_length)
    raw = b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + body
    msg = email.parser.BytesParser().parsebytes(raw)
    for part in msg.walk():
        if part.get_content_disposition() == "form-data":
            params = dict(part.get_params(header="content-disposition") or [])
            if params.get("name") == "file":
                return params.get("filename", "upload.md"), part.get_payload(decode=True)
    return None, None


def _inject_shared_scenario(bootstrap: Dict[str, Any]) -> Dict[str, Any]:
    """Deep-copy the bootstrap and append the shared scenario to every persona."""
    if not _shared_scenario_meta:
        return bootstrap
    result = _copy.deepcopy(bootstrap)
    title = _shared_scenario_meta.get("title", "Shared Scenario")
    meta_tension = _shared_scenario_meta.get("metaTension", "")
    for persona in result.get("personas", []):
        code = persona["code"]
        # Prefer per-persona analysis if available, fall back to persona profile KPIs
        analysis = _shared_cache.get(code)
        section = _shared_scenario_meta.get("personaSections", {}).get(code, {})
        if analysis:
            kpis = [
                {"code": k["code"], "label": k["label"]}
                for k in analysis.get("parsed", {}).get("nativeKpis", [])
            ]
            about = analysis.get("parsed", {}).get("scenario", "")
        else:
            kpis = persona.get("kpiFamilies", [])
            about = ""
        options = [
            {
                "code": opt["code"],
                "label": opt["label"],
                "summary": opt.get("description", ""),
                "risk": "",
                "keywords": [w for w in opt.get("label", "").lower().split() if len(w) > 3],
            }
            for opt in section.get("options", [])
        ]
        scenario_obj = {
            "id": f"shared-{code.lower()}",
            "code": code,
            "name": f"{title} — {code}",
            "label": title,
            "personaCode": code,
            "personaName": persona.get("name", code),
            "scenarioTitle": title,
            "about": about,
            "tension": section.get("tension", meta_tension),
            "decisionContext": {},
            "kpiFamilies": kpis,
            "options": options,
            "keywords": [w for w in title.lower().split() if len(w) > 3],
            "isShared": True,
        }
        persona.setdefault("scenarios", []).append(scenario_obj)
    return result


class DecisionAppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.serve_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/health":
            self.respond_json({"status": "ok"})
            return
        if self.path == "/matrix-bootstrap":
            self.respond_json(_inject_shared_scenario(load_matrix_bootstrap()))
            return
        if self.path == "/shared-cache":
            if not _shared_cache:
                self.respond_json({"status": "empty", "message": "No shared scenario loaded yet."})
            else:
                self.respond_json({
                    "status": "ok",
                    "scenario": _shared_scenario_meta,
                    "personaCount": len(_shared_cache),
                    "personaCodes": sorted(_shared_cache.keys()),
                })
            return
        if self.path.startswith("/static/"):
            target = (ROOT / self.path.lstrip("/")).resolve()
            if STATIC_ROOT not in target.parents and target != STATIC_ROOT:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            mime = "text/plain; charset=utf-8"
            if target.suffix == ".css":
                mime = "text/css; charset=utf-8"
            elif target.suffix == ".js":
                mime = "application/javascript; charset=utf-8"
            self.serve_file(target, mime)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/analyze":
            self._handle_analyze()
        elif self.path == "/resolve-question":
            self._handle_resolve_question()
        elif self.path == "/analyze-shared":
            self._handle_analyze_shared()
        elif self.path == "/resolve-question-shared":
            self._handle_resolve_question_shared()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_analyze(self) -> None:
        filename, raw_bytes = parse_upload(self.headers, self.rfile)
        if raw_bytes is None:
            self.respond_json(
                {"status": "error", "message": "No markdown file was uploaded."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            payload = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            self.respond_json(
                {"status": "error", "message": "The uploaded file must be UTF-8 markdown."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        result = analyze_markdown(payload, os.path.basename(filename or "upload.md"))
        self.respond_json(result)

    def _handle_resolve_question(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.respond_json(
                {"status": "error", "message": "Request body must be valid JSON."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        question = body.get("question", "").strip()
        if not question:
            self.respond_json(
                {"status": "error", "message": "Missing required field: question"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        ctx = body.get("context", {})
        kpis = ctx.get("kpis", [])
        scenario = ctx.get("scenario", "")
        tension = ctx.get("tension", "")
        time_horizon = ctx.get("timeHorizon", "")
        normalized_persona = ctx.get("normalizedPersona", {})
        matrix_perspectives = ctx.get("matrixPerspectives", [])
        matrix_emotion_modes = ctx.get("matrixEmotionModes", [])

        if not kpis:
            self.respond_json(
                {"status": "error", "message": "Missing required context field: kpis"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        result = resolve_question(
            question_text=question,
            kpis=kpis,
            scenario=scenario,
            tension=tension,
            time_horizon=time_horizon,
            normalized_persona=normalized_persona,
            matrix_perspectives=matrix_perspectives,
            matrix_emotion_modes=matrix_emotion_modes,
        )
        self.respond_json({"status": "ok", "resolution": result})

    def _handle_analyze_shared(self) -> None:
        global _shared_cache, _shared_scenario_meta
        filename, raw_bytes = parse_upload(self.headers, self.rfile)
        if raw_bytes is None:
            self.respond_json(
                {"status": "error", "message": "No markdown file was uploaded."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            scenario_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            self.respond_json(
                {"status": "error", "message": "File must be UTF-8 markdown."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        parsed_shared = parse_shared_scenario(scenario_text)
        if not parsed_shared["personaSections"]:
            self.respond_json(
                {"status": "error", "message": "No persona sections found. Expected ### P1 · Name (Role) headings."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        # Load persona profiles from disk
        persona_files = sorted(
            PERSONA_DIR.glob("P*.md"),
            key=lambda p: int(_re.search(r"P(\d+)", p.name).group(1)),
        )
        persona_profiles: Dict[str, Any] = {}
        for pf in persona_files:
            try:
                profile = _parse_persona_file(pf)
                persona_profiles[profile["code"]] = profile
            except Exception:
                pass

        # Run analysis for every persona section found
        new_cache: Dict[str, Any] = {}
        errors: Dict[str, str] = {}
        for code, section in parsed_shared["personaSections"].items():
            profile = persona_profiles.get(code)
            if not profile:
                errors[code] = f"No persona profile on disk for {code}"
                continue
            try:
                combined_doc = build_combined_doc_for_persona(
                    code, profile, section, parsed_shared["sharedEvent"]
                )
                result = analyze_markdown(combined_doc, f"{code}_shared.md")
                new_cache[code] = result
            except Exception as exc:
                errors[code] = str(exc)

        _shared_cache = new_cache
        _shared_scenario_meta = {
            "title": parsed_shared["title"],
            "metaTension": parsed_shared["metaTension"],
            "personaSections": {
                code: {
                    "name": s["name"],
                    "roleHint": s["roleHint"],
                    "decision": s["decision"],
                    "options": s["options"],
                    "tension": s["tension"],
                    "timeHorizon": s["timeHorizon"],
                    "kpiRefs": s["kpiRefs"],
                }
                for code, s in parsed_shared["personaSections"].items()
            },
        }

        summary = {
            code: {
                "status": res.get("status"),
                "matrixShape": res.get("matrix", {}).get("shape"),
                "perspectives": [p["label"] for p in res.get("matrix", {}).get("perspectives", [])],
                "emotionModes": [e["name"] for e in res.get("matrix", {}).get("emotionModes", [])],
                "topKpis": [
                    item["label"]
                    for item in (res.get("emotionVariants") or [{}])[0].get("kpiOrdering", [])[:3]
                ] if res.get("emotionVariants") else [],
            }
            for code, res in new_cache.items()
        }

        self.respond_json({
            "status": "ok",
            "scenario": _shared_scenario_meta,
            "personaCount": len(new_cache),
            "errors": errors,
            "summary": summary,
        })

    def _handle_resolve_question_shared(self) -> None:
        """Resolve a question against the cached shared scenario for a specific persona."""
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.respond_json(
                {"status": "error", "message": "Request body must be valid JSON."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        question = body.get("question", "").strip()
        persona_code = body.get("personaCode", "").strip().upper()

        if not question:
            self.respond_json({"status": "error", "message": "Missing field: question"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not persona_code:
            self.respond_json({"status": "error", "message": "Missing field: personaCode (e.g. P1)"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not _shared_cache:
            self.respond_json({"status": "error", "message": "No shared scenario loaded. POST to /analyze-shared first."}, status=HTTPStatus.BAD_REQUEST)
            return
        if persona_code not in _shared_cache:
            self.respond_json(
                {"status": "error", "message": f"{persona_code} not found in cache. Available: {sorted(_shared_cache.keys())}"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        analysis = _shared_cache[persona_code]
        kpis = [
            {"code": k["code"], "label": k["label"], "family": k.get("family")}
            for k in analysis["parsed"].get("nativeKpis", [])
        ]
        result = resolve_question(
            question_text=question,
            kpis=kpis,
            scenario=analysis["parsed"].get("scenario", ""),
            tension=analysis["parsed"].get("tension", ""),
            time_horizon=analysis["parsed"].get("timeHorizon", ""),
            normalized_persona=analysis.get("normalizedPersona", {}),
            matrix_perspectives=analysis.get("matrix", {}).get("perspectives", []),
            matrix_emotion_modes=analysis.get("matrix", {}).get("emotionModes", []),
        )
        self.respond_json({
            "status": "ok",
            "personaCode": persona_code,
            "personaName": analysis.get("normalizedPersona", {}).get("roleLabel", persona_code),
            "resolution": result,
        })

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        return


def run() -> None:
    port = int(os.environ.get("PORT", "8010"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DecisionAppHandler)
    print(f"Decision app listening on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
