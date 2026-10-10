"""Build strict, event-scoped sensor comparisons from attached evidence rows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.common.models import FireObservation
from backend.processing.comparison import compare_sensor_observations


NON_SENSOR_TYPES = {"WEATHER_ESTIMATE", "POPULATION_EXPOSURE_ESTIMATE", "SENSOR_COMPARISON", "SENSOR_COVERAGE"}


def compare_attached_evidence(event: Any, rows: list[dict[str, Any]]) -> dict[str, Any]:
    satellite_by_id = {}
    for row in rows:
        if row.get("evidence_type") in NON_SENSOR_TYPES or not row.get("source"):
            continue
        observation_id = row.get("observation_id")
        if observation_id:
            satellite_by_id.setdefault(str(observation_id), row)
    satellite = list(satellite_by_id.values())
    coverage = [row for row in rows if row.get("evidence_type") == "SENSOR_COVERAGE"]
    # A positive detection is an observation, not proof of a sensor coverage
    # footprint. Only explicit quality-valid *negative* coverage records may
    # introduce a comparison source without a matching observation.
    negative_coverage = [
        row for row in coverage
        if (row.get("record") or {}).get("quality_valid") is True
        and (row.get("record") or {}).get("detection_present") is False
        and (row.get("record") or {}).get("evidence_id")
        and ((row.get("record") or {}).get("source") or row.get("source"))
    ]
    sources = sorted({str(row["source"]) for row in satellite} | {
        str((row.get("record") or {}).get("source") or row.get("source"))
        for row in negative_coverage
    })
    if len(sources) < 2:
        return {
            "status": "INDEPENDENT_OBSERVATION_UNAVAILABLE", "sources": sources,
            "evidence_ids": [],
            "caveat": "No independent source observation or coverage record is attached; absence is not a non-detection.",
        }
    observations = []
    for row in satellite:
        timestamp = _parse_time(row.get("observed_at_utc"))
        if timestamp is None or not row.get("observation_id"):
            continue
        try:
            observations.append(FireObservation(
                fire_id=str(row["observation_id"]), source=str(row["source"]),
                observed_at_utc=timestamp, latitude=float(row["latitude"]),
                longitude=float(row["longitude"]), grid_id=str(row.get("grid_id") or event.grid_id),
                confidence=None, source_version=str(row.get("source_version") or "attached-evidence"),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    primary = next((source for source in sources if source in event.sources), sources[0])
    independent_sources = [source for source in sources if source != primary]
    if not independent_sources:
        return {"status": "INDEPENDENT_OBSERVATION_UNAVAILABLE", "sources": sources, "evidence_ids": []}
    result = compare_sensor_observations(
        observations, primary, independent_sources[0],
        coverage_records=[row.get("record", {}) for row in negative_coverage],
    )
    result["evidence_ids"] = sorted({identifier for match in result.get("matches", [])
                                    for identifier in (match.get("primary_evidence_id"), match.get("comparison_evidence_id"))
                                    if identifier})
    return result


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo and parsed.utcoffset() is not None else None
