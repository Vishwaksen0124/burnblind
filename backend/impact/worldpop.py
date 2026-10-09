"""Population aggregation through the asynchronous WorldPop v2 API."""

from __future__ import annotations

import json
import math
import time
from typing import Any, Callable
from urllib.request import Request, urlopen


API_BASE = "https://api.worldpop.org/v2"


def population_sum(
    geometry: dict[str, Any],
    *,
    year: int,
    resolution: str = "100m",
    api_key: str | None = None,
    timeout_seconds: float = 45,
    poll_seconds: float = 2,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Return a source-backed total for a WGS84 corridor polygon.

    WorldPop computes polygon summaries asynchronously. The endpoint may be
    used without an API key within its published service limits; an optional
    key is sent only as an HTTP header and is never placed in URLs or logs.
    """
    if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("geometry must be a GeoJSON Polygon or MultiPolygon")
    if isinstance(year, bool) or not isinstance(year, int) or not 2015 <= year <= 2030:
        raise ValueError("WorldPop Global2 year must be between 2015 and 2030")
    if resolution not in {"100m", "1km"}:
        raise ValueError("resolution must be 100m or 1km")
    if timeout_seconds <= 0 or poll_seconds <= 0:
        raise ValueError("polling timeouts must be positive")

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    body = json.dumps({"geojson": geometry, "year": year, "resolution": resolution}, separators=(",", ":")).encode()
    submitted = _request_json(opener, Request(f"{API_BASE}/population", data=body, headers=headers, method="POST"), timeout_seconds)
    task_id = submitted.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise RuntimeError("WorldPop API did not return a task identifier")

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = _request_json(opener, Request(f"{API_BASE}/tasks/{task_id}", headers={"Accept": "application/json"}), min(10, timeout_seconds))
        state = result.get("status")
        if state == "success":
            total = result.get("result", {}).get("total_population")
            if isinstance(total, bool) or not isinstance(total, (int, float)) or not math.isfinite(total) or total < 0:
                raise RuntimeError("WorldPop returned an invalid population total")
            return {
                "population_estimate": float(total),
                "population_year": year,
                "resolution": resolution,
                "source": "WorldPop Global2",
                "source_version": "worldpop-global2-api-v2",
                "method": "POPULATION_SUM_WITHIN_DIRECTIONAL_SCREENING_CORRIDOR",
                "limitations": [
                    "Population is a modeled estimate for the selected year.",
                    "The corridor is a screening geometry, not a smoke dispersion model.",
                    "This estimate does not predict smoke concentration or health impact.",
                ],
            }
        if state in {"failure", "failed", "error"}:
            raise RuntimeError("WorldPop population task failed")
        sleeper(min(poll_seconds, max(0, deadline - time.monotonic())))
    raise TimeoutError("WorldPop population task exceeded the configured wait limit")


def _request_json(opener: Callable[..., Any], request: Request, timeout: float) -> dict[str, Any]:
    try:
        with opener(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status < 200 or status >= 300:
                raise RuntimeError(f"WorldPop API returned HTTP {status}")
            result = json.loads(response.read())
    except Exception as exc:
        if isinstance(exc, (TimeoutError, RuntimeError)):
            raise
        raise RuntimeError("WorldPop API request failed") from exc
    if not isinstance(result, dict):
        raise RuntimeError("WorldPop returned a malformed response")
    return result
