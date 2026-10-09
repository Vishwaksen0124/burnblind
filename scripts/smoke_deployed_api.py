"""Read-only contract and anonymous-write smoke checks for a deployed API."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _request(url: str, *, origin: str, method: str = "GET", body: dict | None = None):
    headers = {"Origin": origin, "Accept": "application/json"}
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, headers=headers, method=method)
    try:
        http_response = urlopen(request, timeout=15)
    except HTTPError as exc:
        http_response = exc
    except URLError as exc:
        raise RuntimeError(f"request failed for {url}: {exc.reason}") from exc
    with http_response:
        raw = http_response.read()
        result = json.loads(raw) if raw else None
        return http_response.status, dict(http_response.headers.items()), result


def run_smoke(api_base_url: str, origin: str) -> None:
    api_base = api_base_url.rstrip("/")
    if not api_base.endswith("/api"):
        api_base += "/api"

    checks = (
        ("health", "/health", lambda value: value.get("status") == "ok"),
        ("events", "/events?limit=1", lambda value: isinstance(value.get("items"), list)),
        ("action center", "/action-center?limit=1", lambda value: isinstance(value.get("items"), list)),
        ("blind-spot layer", "/map-layers?layer=blind-spots&limit=1", lambda value: value.get("layer") == "blind-spots" and isinstance(value.get("items"), list)),
        ("investigations", "/investigations?limit=1", lambda value: isinstance(value.get("items"), list)),
    )
    for name, path, validate in checks:
        status, headers, body = _request(api_base + path, origin=origin)
        if status != 200 or not isinstance(body, dict) or not validate(body):
            raise RuntimeError(f"{name} smoke failed: HTTP {status}, response contract mismatch")
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        if normalized_headers.get("access-control-allow-origin") != origin:
            raise RuntimeError(f"{name} smoke failed: dashboard CORS origin was not returned")
        print(f"PASS {name}: HTTP 200")

    # This reserved, nonexistent ID makes an accidental missing auth rule
    # harmless: the API cannot enqueue or append an outcome for a real event.
    probe_id = "evt_deploy_smoke_nonexistent"
    mutations = (
        ("investigation authorization", f"/events/{probe_id}/investigate", {}),
        ("review authorization", f"/events/{probe_id}/review", {"outcome": "CONFIRMED", "notes": "deployment smoke probe"}),
    )
    for name, path, body in mutations:
        status, _, _ = _request(api_base + path, origin=origin, method="POST", body=body)
        if status != 401:
            raise RuntimeError(f"{name} smoke failed: expected HTTP 401, got HTTP {status}")
        print(f"PASS {name}: anonymous request rejected (HTTP 401)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("api_base_url", help="API Gateway stage URL, with or without the /api suffix")
    parser.add_argument("--origin", required=True, help="deployed dashboard origin used for CORS validation")
    args = parser.parse_args()
    run_smoke(args.api_base_url, args.origin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
