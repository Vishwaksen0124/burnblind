"""Versioned deterministic score calculation and investigation gating."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ScoreFeatures:
    observation_gap_risk: float | None = None
    sensor_coverage_gap: float | None = None
    data_quality_risk: float | None = None
    timing_risk: float | None = None
    thermal_signal: float | None = None
    historical_activity: float | None = None
    independent_detection_support: float | None = None
    exposure_score: float | None = None
    urgency_score: float | None = None
    sensor_disagreement: bool = False

    def __post_init__(self) -> None:
        for name in _FEATURE_NAMES:
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= 1
            ):
                raise ValueError(f"{name} must be None or a normalized value in [0, 1]")
        if not isinstance(self.sensor_disagreement, bool):
            raise ValueError("sensor_disagreement must be boolean")


@dataclass(frozen=True, slots=True)
class ScoreConfig:
    version: str
    feature_version: str
    blindness_weights: Mapping[str, float]
    fire_likelihood_weights: Mapping[str, float]
    sensor_disagreement_penalty: float
    triggers: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.version or not self.feature_version:
            raise ValueError("score and feature versions are required")
        _validate_weights("blindness", self.blindness_weights)
        _validate_weights("fire_likelihood", self.fire_likelihood_weights)
        _validate_unit("sensor_disagreement_penalty", self.sensor_disagreement_penalty)
        required_triggers = {
            "priority_high",
            "uncertainty_high",
            "blindness_high",
            "fire_likelihood_moderate",
            "exposure_high",
        }
        if set(self.triggers) != required_triggers:
            raise ValueError("trigger configuration keys do not match the policy contract")
        for name, value in self.triggers.items():
            _validate_unit(f"trigger {name}", value)


@dataclass(frozen=True, slots=True)
class ScoreResult:
    blindness_score: float | None
    fire_likelihood_score: float | None
    uncertainty: float
    priority_score: float | None
    score_version: str
    feature_version: str
    evidence_completeness: float


@dataclass(frozen=True, slots=True)
class InvestigationTrigger:
    should_investigate: bool
    reasons: tuple[str, ...]


_BLINDNESS_FEATURES = (
    "observation_gap_risk",
    "sensor_coverage_gap",
    "data_quality_risk",
    "timing_risk",
)
_LIKELIHOOD_FEATURES = (
    "thermal_signal",
    "historical_activity",
    "independent_detection_support",
)
_FEATURE_NAMES = _BLINDNESS_FEATURES + _LIKELIHOOD_FEATURES + ("exposure_score", "urgency_score")


def _validate_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be normalized in [0, 1]")


def _validate_weights(name: str, weights: Mapping[str, float]) -> None:
    if not weights:
        raise ValueError(f"{name} weights cannot be empty")
    expected = set(_BLINDNESS_FEATURES if name == "blindness" else _LIKELIHOOD_FEATURES)
    if set(weights) != expected:
        raise ValueError(f"{name} weights must define exactly: {', '.join(sorted(expected))}")
    for key, value in weights.items():
        if not isinstance(key, str) or key not in _FEATURE_NAMES:
            raise ValueError(f"unknown {name} feature weight: {key}")
        _validate_unit(f"{name} weight {key}", value)
    if sum(weights.values()) <= 0:
        raise ValueError(f"{name} weights must have a positive sum")


def load_score_config(path: str | Path) -> ScoreConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        weights = payload["weights"]
        uncertainty = payload["uncertainty"]
        return ScoreConfig(
            version=payload["version"],
            feature_version=payload["feature_version"],
            blindness_weights=weights["blindness"],
            fire_likelihood_weights=weights["fire_likelihood"],
            sensor_disagreement_penalty=uncertainty["sensor_disagreement_penalty"],
            triggers=payload["triggers"],
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"invalid score configuration: {exc}") from exc


def _weighted_available_score(features: ScoreFeatures, weights: Mapping[str, float]) -> float | None:
    available = [
        (getattr(features, name), weight)
        for name, weight in weights.items()
        if getattr(features, name) is not None and weight > 0
    ]
    if not available:
        return None
    weight_sum = sum(weight for _, weight in available)
    return sum(float(value) * weight for value, weight in available) / weight_sum


def score_event(features: ScoreFeatures, config: ScoreConfig) -> ScoreResult:
    """Calculate reproducible heuristic scores from normalized evidence."""
    blindness = _weighted_available_score(features, config.blindness_weights)
    likelihood = _weighted_available_score(features, config.fire_likelihood_weights)
    available_count = sum(getattr(features, name) is not None for name in _FEATURE_NAMES)
    completeness = available_count / len(_FEATURE_NAMES)
    uncertainty = 1.0 - completeness
    if features.sensor_disagreement:
        uncertainty = min(1.0, uncertainty + config.sensor_disagreement_penalty)

    priority = None
    if all(value is not None for value in (blindness, likelihood, features.exposure_score, features.urgency_score)):
        priority = float(blindness) * float(likelihood) * float(features.exposure_score) * float(features.urgency_score)

    return ScoreResult(
        blindness_score=blindness,
        fire_likelihood_score=likelihood,
        uncertainty=uncertainty,
        priority_score=priority,
        score_version=config.version,
        feature_version=config.feature_version,
        evidence_completeness=completeness,
    )


def investigation_trigger(result: ScoreResult, config: ScoreConfig, exposure_score: float | None) -> InvestigationTrigger:
    """Apply the documented high-priority/uncertainty/blindness/exposure gate."""
    if exposure_score is not None:
        _validate_unit("exposure_score", exposure_score)
    thresholds = config.triggers
    reasons: list[str] = []
    if result.priority_score is not None and result.priority_score >= thresholds["priority_high"]:
        reasons.append("HIGH_PRIORITY")
    if result.uncertainty >= thresholds["uncertainty_high"]:
        reasons.append("HIGH_UNCERTAINTY")
    if (
        result.blindness_score is not None
        and result.blindness_score >= thresholds["blindness_high"]
        and result.fire_likelihood_score is not None
        and result.fire_likelihood_score >= thresholds["fire_likelihood_moderate"]
    ):
        reasons.append("HIGH_BLINDNESS_WITH_MODERATE_FIRE_LIKELIHOOD")
    if exposure_score is not None and exposure_score >= thresholds["exposure_high"]:
        reasons.append("HIGH_EXPOSURE")
    return InvestigationTrigger(bool(reasons), tuple(reasons))
