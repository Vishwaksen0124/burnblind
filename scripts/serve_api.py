"""Run the read-only historical replay API on localhost."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.api.handler import handle_request
from backend.api.repository import load_replay_repository


class ApiHandler(BaseHTTPRequestHandler):
    repository = None

    def _dispatch(self):
        parsed = urlparse(self.path)
        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace") if length else None
        result = handle_request(
            self.command,
            parsed.path,
            query,
            self.repository,
            self.headers.get("X-Correlation-Id"),
            body,
        )
        payload = result.gateway_response()["body"].encode("utf-8")
        self.send_response(result.status_code)
        for name, value in result.headers.items():
            self.send_header(name, value)
        if result.status_code != 204:
            self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD" and result.status_code != 204:
            self.wfile.write(payload)

    do_GET = _dispatch
    do_POST = _dispatch
    do_OPTIONS = _dispatch

    def log_message(self, format, *args):
        # Avoid logging query values that may contain sensitive operator filters.
        print(f"{self.client_address[0]} {self.command} {urlparse(self.path).path} {args[1] if len(args) > 1 else ''}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=ROOT / "data/sample/gk2a_historical_2025.jsonl")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    ApiHandler.repository = load_replay_repository(str(args.sample))
    server = ThreadingHTTPServer((args.host, args.port), ApiHandler)
    print(f"BurnBlind replay API: http://{args.host}:{args.port}/api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
