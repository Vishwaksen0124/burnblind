"""Normalize explicit event evidence into deterministic scoring inputs.

Normalization parameters are passed by the application and should be stored
alongside each scoring result. This module never fills a missing source with a
zero or a negative observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Any, Mapping

from backend.scoring.engine import ScoreFeatures


@dataclass(frozen=True, slots=True)
class DerivedFeaturePacket:
    features: ScoreFeatures
    evidence_ids_by_feature: dict[str, tuple[str, ...]]
    available_feature_count: int
    total_feature_count: int
    version: str


def derive_score_features(
    packet: Mapping[str, Any],
    *,
    event_time_utc: datetime,
    normalization: Mapping[str, float],
    version: str,
) -> DerivedFeaturePacket:
    """Create reproducible normalized inputs using only supplied evidence.

    Expected packet sections: ``coverage``, ``observations``, ``history``,
    ``sensor_comparison``, ``exposure`` and optional ``urgency``. Each used
    value must cite evidence IDs. Event-time checks prevent future leakage.
    """
    event_time = _aware(event_time_utc, "event_time_utc")
    if not version:
        raise ValueError("feature version is required")
    for name in ("max_observation_gap_hours", "thermal_signal_max_delta_k", "historical_hits_per_year_max", "exposure_population_max"):
        value = normalization.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"normalization.{name} must be finite and positive")

    coverage = _section(packet, "coverage")
    coverage_ids = _ids(coverage.get("evidence_ids"))
    if any(coverage.get(name) is not None for name in ("observation_gap_hours", "expected_sensor_count", "available_sensor_count", "valid_observation_fraction", "timing_risk")) and not coverage_ids:
        raise ValueError("coverage measurements require evidence_ids")
    observation_gap = None
    gap_hours = coverage.get("observation_gap_hours")
    if gap_hours is not None:
        gap_hours = _nonnegative(gap_hours, "coverage.observation_gap_hours")
        observation_gap = _unit(gap_hours / normalization["max_observation_gap_hours"])

    sensor_gap = None
    expected = coverage.get("expected_sensor_count")
    available = coverage.get("available_sensor_count")
    if expected is not None or available is not None:
        expected = _positive_integer(expected, "coverage.expected_sensor_count")
        available = _nonnegative_integer(available, "coverage.available_sensor_count")
        if available > expected:
            raise ValueError("coverage.available_sensor_count cannot exceed expected_sensor_count")
        sensor_gap = (expected - available) / expected

    quality_risk = None
    valid_fraction = coverage.get("valid_observation_fraction")
    if valid_fraction is not None:
        quality_risk = 1 - _unit(valid_fraction)

    timing_risk = None
    if coverage.get("timing_risk") is not None:
        timing_risk = _unit(coverage["timing_risk"])

    observation_rows = packet.get("observations", [])
    if not isinstance(observation_rows, list):
        raise ValueError("observations must be a list")
    thermal_values = []
    thermal_ids = []
    for row in observation_rows:
        if not isinstance(row, dict):
            raise ValueError("each observation must be an object")
        timestamp = _aware(_parse_time(row.get("observed_at_utc")), "observation.observed_at_utc")
        if timestamp > event_time:
            raise ValueError("observation occurs after the event time")
        delta = row.get("brightness_temperature_difference_ref")
        if delta is not None:
            thermal_values.append(_nonnegative(delta, "brightness_temperature_difference_ref"))
            row_ids = _ids(row.get("evidence_ids", [row.get("evidence_id")]))
            if not row_ids:
                raise ValueError("thermal observations require evidence_ids")
            thermal_ids.extend(row_ids)
    thermal_signal = None
    if thermal_values:
        thermal_signal = _unit((sum(thermal_values) / len(thermal_values)) / normalization["thermal_signal_max_delta_k"])

    history = _section(packet, "history")
    historical_activity = None
    historical_ids = _ids(history.get("evidence_ids"))
    count = history.get("detection_count")
    years = history.get("years_covered")
    if count is not None or years is not None:
        if not historical_ids:
            raise ValueError("historical context measurements require evidence_ids")
        count = _nonnegative_integer(count, "history.detection_count")
        years = _positive_integer(years, "history.years_covered")
        last = _aware(_parse_time(history.get("latest_observation_at_utc")), "history.latest_observation_at_utc")
        if last > event_time:
            raise ValueError("historical context includes records after the event time")
        historical_activity = _unit(count / (years * normalization["historical_hits_per_year_max"]))

    comparison = _section(packet, "sensor_comparison")
    comparison_status = comparison.get("status")
    sensor_disagreement = comparison_status == "DISAGREEMENT"
    independent_support = 1.0 if comparison_status == "AGREEMENT" else 0.0 if sensor_disagreement else None
    comparison_ids = _ids(comparison.get("evidence_ids")) if independent_support is not None else ()
    if independent_support is not None and not comparison_ids:
        raise ValueError("sensor comparison requires evidence_ids")

    exposure = _section(packet, "exposure")
    exposure_score = None
    exposure_ids = ()
    population = exposure.get("population_estimate")
    if population is not None:
        population = _nonnegative(population, "exposure.population_estimate")
        exposure_score = _unit(population / normalization["exposure_population_max"])
        exposure_ids = _ids(exposure.get("evidence_ids"))
        if not exposure_ids:
            raise ValueError("population exposure estimates require evidence_ids")

    urgency = _section(packet, "urgency")
    urgency_score = _unit(urgency["score"]) if urgency.get("score") is not None else None
    urgency_ids = _ids(urgency.get("evidence_ids")) if urgency_score is not None else ()
    if urgency_score is not None and not urgency_ids:
        raise ValueError("urgency inputs require evidence_ids")

    evidence = {
        "observation_gap_risk": coverage_ids if observation_gap is not None else (),
        "sensor_coverage_gap": coverage_ids if sensor_gap is not None else (),
        "data_quality_risk": coverage_ids if quality_risk is not None else (),
        "timing_risk": coverage_ids if timing_risk is not None else (),
        "thermal_signal": tuple(sorted(set(thermal_ids))) if thermal_signal is not None else (),
        "historical_activity": historical_ids if historical_activity is not None else (),
        "independent_detection_support": comparison_ids,
        "exposure_score": exposure_ids,
        "urgency_score": urgency_ids,
    }
    values = {
        "observation_gap_risk": observation_gap,
        "sensor_coverage_gap": sensor_gap,
        "data_quality_risk": quality_risk,
        "timing_risk": timing_risk,
        "thermal_signal": thermal_signal,
        "historical_activity": historical_activity,
        "independent_detection_support": independent_support,
        "exposure_score": exposure_score,
        "urgency_score": urgency_score,
        "sensor_disagreement": sensor_disagreement,
    }
    features = ScoreFeatures(**values)
    total = 9
    available_count = sum(value is not None for key, value in values.items() if key != "sensor_disagreement")
    return DerivedFeaturePacket(features, evidence, available_count, total, version)


def _section(packet: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = packet.get(name, {})
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _ids(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list) or isinstance(value, tuple):
        values = value
    else:
        raise ValueError("evidence_ids must be a string or list of strings")
    if not all(isinstance(item, str) and item.strip() for item in values):
        raise ValueError("evidence IDs must be non-empty strings")
    return tuple(sorted(set(values)))


def _unit(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("normalized values must be finite numbers")
    return max(0.0, min(1.0, float(value)))


def _nonnegative(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return float(value)


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _aware(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware timestamp")
    return value.astimezone(timezone.utc)
