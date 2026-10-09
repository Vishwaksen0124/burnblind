import json

import pytest

from backend.impact.worldpop import population_sum


class Response:
    status = 200

    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


def geometry():
    return {"type": "Polygon", "coordinates": [[[75.0, 30.0], [75.1, 30.0], [75.1, 30.1], [75.0, 30.0]]]}


def test_worldpop_async_job_returns_attributed_estimate_and_keeps_key_in_header():
    results = iter([
        {"task_id": "task-123"},
        {"task_id": "task-123", "status": "running"},
        {"task_id": "task-123", "status": "success", "result": {"total_population": 1234}},
    ])
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return Response(next(results))

    result = population_sum(geometry(), year=2025, api_key="never-in-url", opener=opener, sleeper=lambda _delay: None)

    assert result["population_estimate"] == 1234.0
    assert result["source"] == "WorldPop Global2"
    assert requests[0][0].get_header("X-api-key") == "never-in-url"
    assert "never-in-url" not in requests[0][0].full_url
    assert requests[1][0].full_url.endswith("/tasks/task-123")


def test_worldpop_rejects_bad_responses_and_unsupported_years():
    with pytest.raises(ValueError, match="year"):
        population_sum(geometry(), year=2031)

    with pytest.raises(RuntimeError, match="task identifier"):
        population_sum(geometry(), year=2025, opener=lambda *_args, **_kwargs: Response({}), sleeper=lambda _delay: None)
