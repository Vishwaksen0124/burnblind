"""Canonical, dependency-free data contracts for BurnBlind.

These models validate boundary data; they do not calculate environmental scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import math
import re
from typing import TypeVar


class ContractError(ValueError):
    """Raised when external or persisted data violates a canonical contract."""


class EventStatus(StrEnum):
    NEW = "NEW"
    CANDIDATE = "CANDIDATE"
    PRIORITIZED = "PRIORITIZED"
    INVESTIGATION_QUEUED = "INVESTIGATION_QUEUED"
    INVESTIGATING = "INVESTIGATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"


class InvestigationStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Classification(StrEnum):
    HIGH_PRIORITY = "HIGH_PRIORITY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class RecommendedAction(StrEnum):
    HUMAN_VERIFICATION = "HUMAN_VERIFICATION"
    CONTINUE_MONITORING = "CONTINUE_MONITORING"
    NO_FURTHER_ACTION = "NO_FURTHER_ACTION"


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_T = TypeVar("_T", bound=StrEnum)


def _identifier(value: str, name: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ContractError(f"{name} must be a non-empty safe identifier (max 128 chars)")
    return value


def _timestamp(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ContractError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _coordinate(latitude: float, longitude: float) -> None:
    for name, value, low, high in (
        ("latitude", latitude, -90, 90),
        ("longitude", longitude, -180, 180),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ContractError(f"{name} must be numeric")
        if not math.isfinite(value) or not low <= value <= high:
            raise ContractError(f"{name} must be between {low} and {high}")


def _score(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{name} must be numeric")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ContractError(f"{name} must be between 0 and 1")


def _enum(value: _T, enum_type: type[_T], name: str) -> _T:
    try:
        return enum_type(value)
    except (ValueError, TypeError) as exc:
        raise ContractError(f"{name} must be one of {[item.value for item in enum_type]}") from exc


def _nonnegative(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{name} must be numeric")
    if not math.isfinite(value) or value < 0:
        raise ContractError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    source: str
    timestamp_utc: datetime
    latitude: float
    longitude: float
    grid_id: str
    thermal_anomaly: float | None
    quality: float | None
    source_version: str

    def __post_init__(self) -> None:
        for name in ("observation_id", "source", "grid_id", "source_version"):
            _identifier(getattr(self, name), name)
        object.__setattr__(self, "timestamp_utc", _timestamp(self.timestamp_utc, "timestamp_utc"))
        _coordinate(self.latitude, self.longitude)
        if self.thermal_anomaly is not None:
            if isinstance(self.thermal_anomaly, bool) or not isinstance(self.thermal_anomaly, (int, float)) or not math.isfinite(self.thermal_anomaly):
                raise ContractError("thermal_anomaly must be finite when provided")
        if self.quality is not None:
            _score(self.quality, "quality")


@dataclass(frozen=True, slots=True)
class FireObservation:
    fire_id: str
    source: str
    observed_at_utc: datetime
    latitude: float
    longitude: float
    grid_id: str
    confidence: float | None
    source_version: str
    brightness_temperature_difference_ref: float | None = None
    brightness_temperature_038_micron_k: float | None = None
    brightness_temperature_112_micron_k: float | None = None
    confidence_flag: int | None = None
    source_confidence: str | None = None
    brightness_temperature_channel_1_k: float | None = None
    brightness_temperature_channel_2_k: float | None = None
    channel_1_name: str | None = None
    channel_2_name: str | None = None
    frp_mw: float | None = None
    scan_size_km: float | None = None
    track_size_km: float | None = None
    satellite: str | None = None
    instrument: str | None = None
    daynight: str | None = None

    def __post_init__(self) -> None:
        for name in ("fire_id", "source", "grid_id", "source_version"):
            _identifier(getattr(self, name), name)
        object.__setattr__(self, "observed_at_utc", _timestamp(self.observed_at_utc, "observed_at_utc"))
        _coordinate(self.latitude, self.longitude)
        if self.confidence is not None:
            _score(self.confidence, "confidence")
        for name in (
            "brightness_temperature_difference_ref",
            "brightness_temperature_038_micron_k",
            "brightness_temperature_112_micron_k",
            "brightness_temperature_channel_1_k",
            "brightness_temperature_channel_2_k",
        ):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ContractError(f"{name} must be finite when provided")
        if self.confidence_flag is not None and (
            isinstance(self.confidence_flag, bool)
            or not isinstance(self.confidence_flag, int)
            or self.confidence_flag < 0
        ):
            raise ContractError("confidence_flag must be a non-negative integer when provided")
        for name in ("frp_mw", "scan_size_km", "track_size_km"):
            value = getattr(self, name)
            if value is not None:
                _nonnegative(value, name)
        for name in (
            "source_confidence",
            "channel_1_name",
            "channel_2_name",
            "satellite",
            "instrument",
            "daynight",
        ):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ContractError(f"{name} must be a non-empty string when provided")


@dataclass(frozen=True, slots=True)
class WeatherObservation:
    observed_at_utc: datetime
    latitude: float
    longitude: float
    wind_speed_m_s: float | None
    wind_direction_degrees: float | None
    source: str
    source_version: str
    temperature_c: float | None = None
    relative_humidity_percent: float | None = None
    precipitation_mm: float | None = None
    cloud_cover_percent: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at_utc", _timestamp(self.observed_at_utc, "observed_at_utc"))
        _coordinate(self.latitude, self.longitude)
        for name in ("source", "source_version"):
            _identifier(getattr(self, name), name)
        if self.wind_speed_m_s is not None:
            _nonnegative(self.wind_speed_m_s, "wind_speed_m_s")
        if self.wind_direction_degrees is not None:
            if isinstance(self.wind_direction_degrees, bool) or not isinstance(self.wind_direction_degrees, (int, float)) or not math.isfinite(self.wind_direction_degrees) or not 0 <= self.wind_direction_degrees < 360:
                raise ContractError("wind_direction_degrees must be in [0, 360)")
        if self.temperature_c is not None and not isinstance(self.temperature_c, (int, float)):
            raise ContractError("temperature_c must be numeric when provided")
        if self.relative_humidity_percent is not None and not 0 <= self.relative_humidity_percent <= 100:
            raise ContractError("relative_humidity_percent must be in [0, 100]")
        if self.precipitation_mm is not None:
            _nonnegative(self.precipitation_mm, "precipitation_mm")
        if self.cloud_cover_percent is not None and not 0 <= self.cloud_cover_percent <= 100:
            raise ContractError("cloud_cover_percent must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class PopulationEstimate:
    grid_id: str
    population: float
    estimate_year: int
    source: str
    source_version: str

    def __post_init__(self) -> None:
        for name in ("grid_id", "source", "source_version"):
            _identifier(getattr(self, name), name)
        _nonnegative(self.population, "population")
        if isinstance(self.estimate_year, bool) or not isinstance(self.estimate_year, int) or not 1900 <= self.estimate_year <= 2200:
            raise ContractError("estimate_year must be a plausible four-digit year")


@dataclass(frozen=True, slots=True)
class Event:
    event_id: str
    grid_id: str
    detected_at_utc: datetime
    latitude: float
    longitude: float
    observation_gap_hours: float | None
    blindness_score: float
    fire_likelihood: float
    uncertainty: float
    exposure_estimate: float | None
    priority_score: float | None
    status: EventStatus
    investigation_status: InvestigationStatus
    feature_version: str
    scoring_version: str

    def __post_init__(self) -> None:
        for name in ("event_id", "grid_id", "feature_version", "scoring_version"):
            _identifier(getattr(self, name), name)
        object.__setattr__(self, "detected_at_utc", _timestamp(self.detected_at_utc, "detected_at_utc"))
        _coordinate(self.latitude, self.longitude)
        for name in ("blindness_score", "fire_likelihood", "uncertainty"):
            _score(getattr(self, name), name)
        if self.priority_score is not None:
            _score(self.priority_score, "priority_score")
        for name in ("observation_gap_hours", "exposure_estimate"):
            value = getattr(self, name)
            if value is not None:
                _nonnegative(value, name)
        object.__setattr__(self, "status", _enum(self.status, EventStatus, "status"))
        object.__setattr__(self, "investigation_status", _enum(self.investigation_status, InvestigationStatus, "investigation_status"))


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    evidence_id: str
    evidence_type: str
    source: str
    summary: str

    def __post_init__(self) -> None:
        for name in ("evidence_id", "evidence_type", "source"):
            _identifier(getattr(self, name), name)
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise ContractError("summary must be a non-empty string")


@dataclass(frozen=True, slots=True)
class CandidateEvent:
    """A deterministic cluster of source detections awaiting full scoring."""

    event_id: str
    grid_id: str
    detected_at_utc: datetime
    last_observed_at_utc: datetime
    latitude: float
    longitude: float
    detection_count: int
    sources: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    data_mode: str
    processing_version: str

    def __post_init__(self) -> None:
        for name in ("event_id", "grid_id", "data_mode", "processing_version"):
            _identifier(getattr(self, name), name)
        object.__setattr__(self, "detected_at_utc", _timestamp(self.detected_at_utc, "detected_at_utc"))
        object.__setattr__(self, "last_observed_at_utc", _timestamp(self.last_observed_at_utc, "last_observed_at_utc"))
        if self.last_observed_at_utc < self.detected_at_utc:
            raise ContractError("last_observed_at_utc cannot precede detected_at_utc")
        _coordinate(self.latitude, self.longitude)
        if isinstance(self.detection_count, bool) or not isinstance(self.detection_count, int) or self.detection_count < 1:
            raise ContractError("detection_count must be a positive integer")
        if not self.sources or not all(isinstance(item, str) and item.strip() for item in self.sources):
            raise ContractError("sources must contain non-empty source identifiers")
        if not self.evidence_ids or not all(isinstance(item, str) and item.strip() for item in self.evidence_ids):
            raise ContractError("evidence_ids must contain non-empty identifiers")


@dataclass(frozen=True, slots=True)
class Investigation:
    investigation_id: str
    event_id: str
    agent_version: str
    prompt_version: str
    started_at_utc: datetime
    completed_at_utc: datetime | None
    classification: Classification
    confidence: float | None
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)
    contradictions: tuple[str, ...] = field(default_factory=tuple)
    missing_evidence: tuple[str, ...] = field(default_factory=tuple)
    reasoning_summary: str = ""
    recommended_action: RecommendedAction = RecommendedAction.HUMAN_VERIFICATION

    def __post_init__(self) -> None:
        for name in ("investigation_id", "event_id", "agent_version", "prompt_version"):
            _identifier(getattr(self, name), name)
        object.__setattr__(self, "started_at_utc", _timestamp(self.started_at_utc, "started_at_utc"))
        if self.completed_at_utc is not None:
            completed = _timestamp(self.completed_at_utc, "completed_at_utc")
            if completed < self.started_at_utc:
                raise ContractError("completed_at_utc cannot precede started_at_utc")
            object.__setattr__(self, "completed_at_utc", completed)
        if self.confidence is not None:
            _score(self.confidence, "confidence")
        object.__setattr__(self, "classification", _enum(self.classification, Classification, "classification"))
        object.__setattr__(self, "recommended_action", _enum(self.recommended_action, RecommendedAction, "recommended_action"))
        if not all(isinstance(item, EvidenceReference) for item in self.evidence):
            raise ContractError("evidence must contain EvidenceReference values")
        for name in ("contradictions", "missing_evidence"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ContractError(f"{name} must be a tuple of non-empty strings")
        if not isinstance(self.reasoning_summary, str):
            raise ContractError("reasoning_summary must be a string")
