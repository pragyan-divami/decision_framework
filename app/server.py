import email.parser
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from decision_engine import analyze_markdown
from matrix_catalog import load_matrix_bootstrap


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


class DecisionAppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self.serve_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/health":
            self.respond_json({"status": "ok"})
            return
        if self.path == "/matrix-bootstrap":
            self.respond_json(load_matrix_bootstrap())
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
        if self.path != "/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

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
