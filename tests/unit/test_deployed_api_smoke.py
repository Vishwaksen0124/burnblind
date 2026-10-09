from __future__ import annotations

import pytest

from scripts import smoke_deployed_api


def test_deployed_api_smoke_checks_public_contract_cors_and_write_guards(monkeypatch):
    origin = "https://dashboard.example"
    success_headers = {"access-control-allow-origin": origin}
    replies = iter(
        [
            (200, success_headers, {"status": "ok"}),
            (200, success_headers, {"items": []}),
            (200, success_headers, {"items": []}),
            (200, success_headers, {"layer": "blind-spots", "items": []}),
            (200, success_headers, {"items": []}),
            (401, {}, {"message": "Unauthorized"}),
            (401, {}, {"message": "Unauthorized"}),
        ]
    )
    calls = []

    def request(url, **kwargs):
        calls.append((url, kwargs))
        return next(replies)

    monkeypatch.setattr(smoke_deployed_api, "_request", request)

    smoke_deployed_api.run_smoke("https://api.example/prod/", origin)

    assert [kwargs.get("method", "GET") for _, kwargs in calls] == [
        "GET", "GET", "GET", "GET", "GET", "POST", "POST"
    ]
    assert all(url.startswith("https://api.example/prod/api/") for url, _ in calls)
    assert calls[-2][0].endswith("evt_deploy_smoke_nonexistent/investigate")
    assert calls[-1][0].endswith("evt_deploy_smoke_nonexistent/review")


def test_deployed_api_smoke_fails_when_mutation_is_not_rejected(monkeypatch):
    origin = "https://dashboard.example"
    success_headers = {"Access-Control-Allow-Origin": origin}
    replies = iter(
        [
            (200, success_headers, {"status": "ok"}),
            (200, success_headers, {"items": []}),
            (200, success_headers, {"items": []}),
            (200, success_headers, {"layer": "blind-spots", "items": []}),
            (200, success_headers, {"items": []}),
            (404, {}, {"error": "not found"}),
        ]
    )
    monkeypatch.setattr(smoke_deployed_api, "_request", lambda *_args, **_kwargs: next(replies))

    with pytest.raises(RuntimeError, match="expected HTTP 401, got HTTP 404"):
        smoke_deployed_api.run_smoke("https://api.example/prod/api", origin)
