"""Conservative cross-sensor comparison with explicit coverage semantics."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Iterable

from pyproj import Geod

from backend.common.models import FireObservation


_GEOD = Geod(ellps="WGS84")
COMPARISON_STATUSES = frozenset({"AGREEMENT", "DISAGREEMENT", "INDEPENDENT_OBSERVATION_UNAVAILABLE", "INCONCLUSIVE"})


def compare_sensor_observations(
    records: Iterable[FireObservation],
    primary_source: str,
    comparison_source: str,
    *,
    coverage_records: Iterable[dict[str, Any]] = (),
    max_time_delta_minutes: float = 30,
    max_distance_km: float = 5,
) -> dict[str, Any]:
    """Compare actual observations; only valid explicit coverage can disagree.

    A missing comparison detection is never treated as a negative. A negative
    comparison requires a quality-valid coverage record explicitly stating
    that the comparison source observed this location and recorded no event.
    """
    for name, value in (("max_time_delta_minutes", max_time_delta_minutes), ("max_distance_km", max_distance_km)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative")
    if not primary_source or not comparison_source or primary_source == comparison_source:
        raise ValueError("primary and comparison sources must be distinct non-empty names")

    rows = list(records)
    primary = [row for row in rows if row.source == primary_source]
    comparison = [row for row in rows if row.source == comparison_source]
    pairs = []
    for left in primary:
        for right in comparison:
            delta_minutes = abs((left.observed_at_utc - right.observed_at_utc).total_seconds()) / 60
            _, _, distance_m = _GEOD.inv(left.longitude, left.latitude, right.longitude, right.latitude)
            distance_km = distance_m / 1000
            if delta_minutes <= max_time_delta_minutes and distance_km <= max_distance_km:
                pairs.append({
                    "primary_evidence_id": left.fire_id,
                    "comparison_evidence_id": right.fire_id,
                    "temporal_delta_minutes": round(delta_minutes, 3),
                    "spatial_delta_km": round(distance_km, 4),
                })
    if pairs:
        return {
            "status": "AGREEMENT",
            "primary_source": primary_source,
            "comparison_source": comparison_source,
            "matches": pairs,
            "reason": "Supplied source detections match within the configured spatial and temporal tolerances.",
        }

    valid_negative_coverage = []
    for coverage in coverage_records:
        if not primary or coverage.get("source") != comparison_source:
            continue
        if coverage.get("quality_valid") is not True or coverage.get("detection_present") is not False:
            continue
        covered_at = _parse_timestamp(coverage.get("observed_at_utc"))
        if covered_at is None:
            continue
        try:
            coverage_lat = float(coverage["latitude"])
            coverage_lon = float(coverage["longitude"])
            radius_km = float(coverage["coverage_radius_km"])
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in (coverage_lat, coverage_lon, radius_km)) or radius_km < 0:
            continue
        for left in primary:
            delta_minutes = abs((left.observed_at_utc - covered_at).total_seconds()) / 60
            _, _, distance_m = _GEOD.inv(left.longitude, left.latitude, coverage_lon, coverage_lat)
            distance_km = distance_m / 1000
            if delta_minutes <= max_time_delta_minutes and distance_km <= min(max_distance_km, radius_km):
                evidence_id = coverage.get("evidence_id")
                if not isinstance(evidence_id, str) or not evidence_id:
                    continue
                valid_negative_coverage.append({
                    "primary_evidence_id": left.fire_id,
                    "comparison_evidence_id": evidence_id,
                    "temporal_delta_minutes": round(delta_minutes, 3),
                    "spatial_delta_km": round(distance_km, 4),
                })
    if valid_negative_coverage:
        return {
            "status": "DISAGREEMENT",
            "primary_source": primary_source,
            "comparison_source": comparison_source,
            "matches": valid_negative_coverage,
            "reason": "A primary detection conflicts with a supplied quality-valid comparison coverage record that explicitly reports no detection.",
        }

    if primary and comparison:
        return {
            "status": "INCONCLUSIVE",
            "primary_source": primary_source,
            "comparison_source": comparison_source,
            "matches": [],
            "reason": "Both sources have records, but none meet the configured matching tolerances; a non-match alone is not a disagreement.",
        }
    return {
        "status": "INDEPENDENT_OBSERVATION_UNAVAILABLE",
        "primary_source": primary_source,
        "comparison_source": comparison_source,
        "matches": [],
        "reason": "No matching detection or explicit quality-valid negative coverage record is available.",
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None or result.utcoffset() is None:
        return None
    return result.astimezone(timezone.utc)
