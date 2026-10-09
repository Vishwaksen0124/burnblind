"""Source-backed environmental enrichment, independent of the LLM agent."""

from __future__ import annotations

from datetime import timezone
import hashlib
import json
from typing import Any, Callable

from backend.api.repository import CandidateEventRepository


class EnvironmentalAnalysisService:
    """Enrich one event using weather, population, and attached sensor records.

    This service never imports Strands or calls an investigation/model provider.
    """

    def __init__(
        self,
        events: CandidateEventRepository,
        evidence: Any,
        weather_lookup: Callable[..., Any] | None = None,
        population_lookup: Callable[..., Any] | None = None,
    ):
        self.events = events
        self.evidence = evidence
        self.weather_lookup = weather_lookup
        self.population_lookup = population_lookup

    def analyze(self, event_id: str) -> dict[str, Any]:
        event = self.events.get(event_id)
        if event is None:
            return {"event_id": event_id, "status": "NOT_FOUND"}

        rows = self.evidence.list_for_event(event_id)
        saved_weather = next((row.get("record") for row in reversed(rows)
                              if row.get("evidence_type") == "WEATHER_ESTIMATE" and isinstance(row.get("record"), dict)
                              and row["record"].get("status") == "OK"), None)
        try:
            weather = saved_weather or self._weather(event)
        except Exception as exc:
            weather = {"status": "UNAVAILABLE", "detail": f"Weather source error: {type(exc).__name__}."}

        saved_exposure = next((row.get("record") for row in reversed(rows)
                               if row.get("evidence_type") == "POPULATION_EXPOSURE_ESTIMATE" and isinstance(row.get("record"), dict)
                               and row["record"].get("status") in {"OK", "ESTIMATED"}), None)
        exposure = saved_exposure or {"status": "UNAVAILABLE", "detail": "Sourced event-time wind is required."}
        if saved_exposure is None and weather.get("status") == "OK":
            try:
                exposure = self._exposure(event, weather)
            except Exception as exc:
                exposure = {"status": "UNAVAILABLE", "detail": f"Population source error: {type(exc).__name__}."}

        try:
            comparison = self._comparison(event)
        except Exception as exc:
            comparison = {"status": "UNAVAILABLE", "detail": f"Sensor comparison error: {type(exc).__name__}."}

        coverage = [row for row in self.evidence.list_for_event(event_id)
                    if row.get("evidence_type") == "SENSOR_COVERAGE"]
        coverage_ids = [row.get("observation_id") for row in coverage if row.get("observation_id")]
        valid_coverage = [
            row for row in coverage
            if isinstance(row.get("record"), dict)
            and row["record"].get("quality_valid") is True
        ]
        blind_spot = (
            {
                "status": "AVAILABLE",
                "score": 0.0,
                "detail": "Quality-valid independent sensor coverage is attached for this event.",
                "evidence_ids": coverage_ids,
            }
            if valid_coverage else {
                "status": "UNAVAILABLE",
                "detail": "Blind-spot scoring requires sourced sensor coverage and quality measurements.",
                "evidence_ids": coverage_ids,
            }
        )
        historical_context = {
            "status": "UNAVAILABLE",
            "detail": "No separately sourced historical fire-activity context is attached to this event.",
        }

        complete = weather.get("status") == "OK" and exposure.get("status") in {"OK", "ESTIMATED"}
        context = {
            "environmental_analysis": {
                "status": "COMPLETE" if complete else "PARTIAL",
                "updated_at_utc": _iso_now(),
                "weather": weather,
                "historical_context": historical_context,
            },
            "exposure": exposure,
            "sensor_comparison": comparison,
            "blind_spot": blind_spot,
            "monitoring_coverage": {
                "status": "AVAILABLE" if coverage else "UNAVAILABLE",
                "evidence_ids": coverage_ids,
                "detail": None if valid_coverage else "No source-backed sensor coverage and quality record is attached.",
            },
        }
        writer = getattr(self.events, "put_feature_context", None)
        if writer:
            writer(event_id, context)
            if complete:
                self._persist_score_features(event, rows, context, writer)
        return {"event_id": event_id, **context}

    def _persist_score_features(self, event: Any, rows: list[dict[str, Any]], context: dict[str, Any], writer: Any) -> None:
        """Persist only normalized, source-backed inputs for deterministic scoring."""
        from backend.processing.feature_derivation import derive_score_features

        observations = [
            {
                "observed_at_utc": row.get("observed_at_utc"),
                "brightness_temperature_difference_ref": row.get("brightness_temperature_difference_ref"),
                "evidence_id": row.get("observation_id"),
            }
            for row in rows
            if row.get("brightness_temperature_difference_ref") is not None
        ]
        comparison = context.get("sensor_comparison") or {}
        exposure = context.get("exposure") or {}
        packet = {
            "observations": observations,
            "sensor_comparison": {
                **comparison,
                "evidence_ids": [comparison["evidence_id"]] if comparison.get("evidence_id") else [],
            },
            "exposure": {
                "population_estimate": exposure.get("population_estimate"),
                "evidence_ids": [exposure["evidence_id"]] if exposure.get("evidence_id") else [],
            },
        }
        derived = derive_score_features(
            packet,
            event_time_utc=event.detected_at_utc,
            normalization={
                "max_observation_gap_hours": 24,
                "thermal_signal_max_delta_k": 30,
                "historical_hits_per_year_max": 10,
                "exposure_population_max": 1_000_000,
            },
            version="features-v2-environmental",
        )
        writer(event.event_id, {"score_features": {
            name: getattr(derived.features, name)
            for name in (
                "observation_gap_risk", "sensor_coverage_gap", "data_quality_risk",
                "timing_risk", "thermal_signal", "historical_activity",
                "independent_detection_support", "exposure_score", "urgency_score",
                "sensor_disagreement",
            )
            if getattr(derived.features, name) is not None or name == "sensor_disagreement"
        }})

    def _weather(self, event: Any) -> dict[str, Any]:
        if self.weather_lookup is None:
            from backend.ingestion.open_meteo import historical_wind
            lookup = historical_wind
        else:
            lookup = self.weather_lookup
        observation = lookup(event.latitude, event.longitude, event.detected_at_utc)
        if observation.wind_speed_m_s is None or observation.wind_direction_degrees is None:
            return {"status": "UNAVAILABLE", "source": observation.source}
        observed = _iso(observation.observed_at_utc)
        evidence_id = "wx_" + _digest(f"{event.event_id}:{observed}")
        result = {
            "status": "OK", "evidence_id": evidence_id, "source": observation.source,
            "source_version": observation.source_version, "observed_at_utc": observed,
            "wind_speed_m_s": observation.wind_speed_m_s,
            "wind_direction_degrees": observation.wind_direction_degrees,
            "temperature_c": observation.temperature_c,
            "relative_humidity_percent": observation.relative_humidity_percent,
            "precipitation_mm": observation.precipitation_mm,
            "cloud_cover_percent": observation.cloud_cover_percent,
            "interpretation": "Historical reanalysis estimate; not a direct local measurement.",
        }
        self.evidence.put_derived_record({
            "observation_id": evidence_id, "event_id": event.event_id,
            "event_time_utc": _iso(event.detected_at_utc), "observed_at_utc": observed,
            "source": observation.source, "evidence_type": "WEATHER_ESTIMATE",
            "latitude": event.latitude, "longitude": event.longitude, "record": result,
        })
        return result

    def _exposure(self, event: Any, weather: dict[str, Any]) -> dict[str, Any]:
        from backend.impact.corridor import downwind_corridor
        from backend.impact.worldpop import population_sum

        corridor = downwind_corridor(
            event.latitude, event.longitude, weather["wind_speed_m_s"],
            weather["wind_direction_degrees"], duration_hours=6, width_km=10,
        )
        if corridor.geometry is None:
            return {"status": "UNAVAILABLE", "detail": "Impact corridor could not be constructed."}
        lookup = self.population_lookup or population_sum
        estimate = lookup(corridor.geometry, year=event.detected_at_utc.year, resolution="100m")
        evidence_id = "wp_" + _digest(f"{event.event_id}:{event.detected_at_utc.year}:worldpop-global2-api-v2")
        result = {
            "status": "ESTIMATED", "evidence_id": evidence_id, **estimate,
            "corridor_geojson": corridor.geometry,
            "corridor_area_approx_km2": round(corridor.distance_km * 10, 3),
            "downwind_bearing_degrees": corridor.downwind_bearing_degrees,
            "wind_speed_m_s": weather["wind_speed_m_s"],
            "wind_direction_degrees": weather["wind_direction_degrees"],
            "limitations": list(estimate.get("limitations", [])) + list(corridor.assumptions),
        }
        self.evidence.put_derived_record({
            "observation_id": evidence_id, "event_id": event.event_id,
            "event_time_utc": _iso(event.detected_at_utc), "observed_at_utc": _iso(event.detected_at_utc),
            "source": estimate["source"], "evidence_type": "POPULATION_EXPOSURE_ESTIMATE",
            "latitude": event.latitude, "longitude": event.longitude, "record": result,
        })
        return result

    def _comparison(self, event: Any) -> dict[str, Any]:
        rows = self.evidence.list_for_event(event.event_id)
        from backend.processing.evidence_comparison import compare_attached_evidence
        comparison = compare_attached_evidence(event, rows)
        if comparison.get("status") != "INDEPENDENT_OBSERVATION_UNAVAILABLE":
            evidence_id = "cmp_" + _digest(event.event_id)
            self.evidence.put_derived_record({
                "observation_id": evidence_id, "event_id": event.event_id,
                "event_time_utc": _iso(event.detected_at_utc), "observed_at_utc": _iso(event.detected_at_utc),
                "source": "BURNBLIND_CROSS_SENSOR_COMPARISON", "evidence_type": "SENSOR_COMPARISON",
                "latitude": event.latitude, "longitude": event.longitude, "record": comparison,
            })
        return comparison


class EnvironmentalAnalysisLauncher:
    """Queue one event-scoped deterministic enrichment job; never invokes a model."""

    def __init__(self, events: CandidateEventRepository, queue_url: str, sqs: Any):
        self.events = events
        self.queue_url = queue_url
        self.sqs = sqs

    def enqueue(self, event_id: str, request_id: str) -> dict[str, Any]:
        if self.events.get(event_id) is None:
            return {"event_id": event_id, "status": "NOT_FOUND"}
        reader = getattr(self.events, "get_feature_context", None)
        existing = (reader(event_id) or {}).get("environmental_analysis") if reader else None
        if isinstance(existing, dict) and existing.get("status") == "PROCESSING":
            return {"event_id": event_id, "status": "PROCESSING", "already_queued": True}
        if isinstance(existing, dict) and existing.get("status") == "COMPLETE":
            return {"event_id": event_id, "status": existing["status"], "already_analyzed": True}
        writer = getattr(self.events, "put_feature_context", None)
        if writer:
            writer(event_id, {"environmental_analysis": {
                "status": "PROCESSING", "requested_at_utc": _iso_now(), "request_id": request_id,
            }})
        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps({"event_id": event_id, "request_id": request_id}, separators=(",", ":")),
                MessageGroupId=event_id,
                MessageDeduplicationId=f"{event_id}:{request_id}",
            )
        except Exception:
            if writer:
                writer(event_id, {"environmental_analysis": {
                    "status": "FAILED", "updated_at_utc": _iso_now(),
                    "detail": "Environmental job could not be queued.",
                }})
            raise
        return {"event_id": event_id, "status": "PROCESSING", "already_queued": False}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def _iso(value: Any) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_now() -> str:
    from datetime import datetime
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
