"""Read-only evidence tools exposed to the Investigation Agent."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Callable

from backend.api.repository import CandidateEventRepository


class DynamoEvidenceRepository:
    """Load source observations attached to one candidate event."""

    def __init__(self, table_name: str, table: Any | None = None):
        if table is None:
            import boto3

            table = boto3.resource("dynamodb").Table(table_name)
        self._table = table

    def list_for_event(self, event_id: str, limit: int = 100) -> list[dict[str, Any]]:
        from boto3.dynamodb.conditions import Key

        result = self._table.query(
            IndexName="event-id-observed-at",
            KeyConditionExpression=Key("event_id").eq(event_id),
            ScanIndexForward=True,
            Limit=limit,
        )
        return [_plain(item) for item in result.get("Items", [])]

    def put_derived_record(self, record: dict[str, Any]) -> None:
        """Idempotently persist source-backed weather/exposure evidence."""
        self._table.put_item(Item=_dynamo_safe(record))

    def get_latest_derived(self, event_id: str, evidence_type: str) -> dict[str, Any] | None:
        return next((
            row.get("record") for row in reversed(self.list_for_event(event_id))
            if row.get("evidence_type") == evidence_type and isinstance(row.get("record"), dict)
        ), None)


def build_evidence_tools(
    events: CandidateEventRepository,
    evidence: DynamoEvidenceRepository,
    registry: dict[str, dict[str, str]],
    weather_lookup: Callable[..., Any] | None = None,
    population_lookup: Callable[..., Any] | None = None,
    target_event_id: str | None = None,
) -> list[Callable[..., Any]]:
    """Create request-scoped tools; no AWS clients or evidence are global."""
    from strands import tool

    def scoped_event(event_id: str):
        if target_event_id is not None and event_id != target_event_id:
            return None
        return events.get(event_id)

    @tool
    def get_event(event_id: str) -> dict[str, Any]:
        """Read the candidate event, event time, location and assessment availability."""
        event = scoped_event(event_id)
        if event is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        scoring_reader = getattr(events, "get_scoring_context", None)
        assessment = scoring_reader(event_id) if scoring_reader and event_id == target_event_id else None
        return {
            "status": "OK",
            "event_id": event.event_id,
            "detected_at_utc": _iso(event.detected_at_utc),
            "last_observed_at_utc": _iso(event.last_observed_at_utc),
            "latitude": event.latitude,
            "longitude": event.longitude,
            "detection_count": event.detection_count,
            "sources": list(event.sources),
            "evidence_ids": list(event.evidence_ids),
            "assessment": assessment or "No deterministic score features have been attached to this event.",
        }

    @tool
    def get_satellite_evidence(event_id: str, window_hours: int = 6) -> dict[str, Any]:
        """Read timestamped satellite source records attached to this event."""
        if not 1 <= window_hours <= 24:
            return {"status": "INVALID_WINDOW", "allowed_hours": [1, 24]}
        event = scoped_event(event_id)
        if event is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        start = event.detected_at_utc - timedelta(hours=window_hours)
        end = event.last_observed_at_utc + timedelta(hours=window_hours)
        records = evidence.list_for_event(event_id)
        observations = []
        for row in records:
            if row.get("evidence_type") in {"WEATHER_ESTIMATE", "POPULATION_EXPOSURE_ESTIMATE", "SENSOR_COMPARISON"}:
                continue
            timestamp = _parse_time(row.get("observed_at_utc"))
            if timestamp is None or not start <= timestamp <= end:
                continue
            evidence_id = str(row.get("observation_id", ""))
            source = str(row.get("source", "UNKNOWN"))
            if not evidence_id:
                continue
            registry[evidence_id] = {"type": "SATELLITE", "source": source}
            thermal_difference = row.get("brightness_temperature_difference_ref")
            observations.append({
                "evidence_id": evidence_id,
                "source": source,
                "observed_at_utc": _iso(timestamp),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "confidence_flag": row.get("confidence_flag"),
                "brightness_temperature_difference_ref": float(thermal_difference) if thermal_difference is not None else None,
            })
        return {"status": "OK" if observations else "NO_RECORDS", "observations": observations[:30]}

    @tool
    def get_historical_context(event_id: str) -> dict[str, Any]:
        """Read documented historical activity near the event, if published to the API."""
        if scoped_event(event_id) is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        return {
            "status": "UNAVAILABLE",
            "detail": "Historical context is not attached to deployed candidate events.",
        }

    @tool
    def get_weather(event_id: str) -> dict[str, Any]:
        """Read ERA5 reanalysis wind at the event time; values are estimates, not measurements."""
        event = scoped_event(event_id)
        if event is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        try:
            if weather_lookup is None:
                from backend.ingestion.open_meteo import historical_wind
                lookup = historical_wind
            else:
                lookup = weather_lookup
            weather = lookup(event.latitude, event.longitude, event.detected_at_utc)
        except Exception as exc:
            return {"status": "UNAVAILABLE", "detail": f"Weather source error: {type(exc).__name__}."}
        evidence_id = "wx_" + hashlib.sha256(
            f"{event.event_id}:{_iso(weather.observed_at_utc)}".encode()
        ).hexdigest()[:24]
        if weather.wind_speed_m_s is None or weather.wind_direction_degrees is None:
            return {"status": "UNAVAILABLE", "source": weather.source}
        registry[evidence_id] = {"type": "WEATHER_ESTIMATE", "source": weather.source}
        result = {
            "status": "OK",
            "evidence_id": evidence_id,
            "source": weather.source,
            "source_version": weather.source_version,
            "observed_at_utc": _iso(weather.observed_at_utc),
            "wind_speed_m_s": weather.wind_speed_m_s,
            "wind_direction_degrees": weather.wind_direction_degrees,
            "interpretation": "Historical reanalysis estimate; not a direct local measurement.",
        }
        evidence.put_derived_record({
            "observation_id": evidence_id,
            "event_id": event.event_id,
            "event_time_utc": _iso(event.detected_at_utc),
            "observed_at_utc": _iso(weather.observed_at_utc),
            "source": weather.source,
            "evidence_type": "WEATHER_ESTIMATE",
            "latitude": event.latitude,
            "longitude": event.longitude,
            "record": result,
        })
        environment_packet[event_id] = {"weather": result}
        return result

    @tool
    def get_exposure(event_id: str) -> dict[str, Any]:
        """Estimate potential exposure from event wind and a sourced population grid."""
        event = scoped_event(event_id)
        if event is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        weather = environment_packet.get(event_id, {}).get("weather")
        if not weather or weather.get("status") != "OK":
            return {"status": "UNAVAILABLE", "detail": "Sourced event-time wind context is required before exposure can be estimated."}
        from backend.impact.corridor import downwind_corridor

        corridor = downwind_corridor(
            event.latitude,
            event.longitude,
            weather["wind_speed_m_s"],
            weather["wind_direction_degrees"],
            duration_hours=6,
            width_km=10,
        )
        if corridor.geometry is None:
            return {"status": "UNAVAILABLE", "detail": corridor.assumptions[0] if corridor.assumptions else "Impact corridor unavailable."}
        try:
            from backend.impact.worldpop import population_sum

            lookup = population_lookup or population_sum
            estimated = lookup(corridor.geometry, year=event.detected_at_utc.year, resolution="100m")
        except Exception as exc:
            return {"status": "UNAVAILABLE", "detail": f"Population source unavailable ({type(exc).__name__})."}
        evidence_id = "wp_" + hashlib.sha256(
            f"{event.event_id}:{event.detected_at_utc.year}:worldpop-global2-api-v2".encode()
        ).hexdigest()[:24]
        result = {
            "status": "OK",
            "evidence_id": evidence_id,
            **estimated,
            "corridor_geojson": corridor.geometry,
            "corridor_area_approx_km2": round(corridor.distance_km * 10, 3),
            "downwind_bearing_degrees": corridor.downwind_bearing_degrees,
            "wind_speed_m_s": weather["wind_speed_m_s"],
            "wind_direction_degrees": weather["wind_direction_degrees"],
            "method": "DIRECTIONAL_CORRIDOR",
            "limitations": list(estimated.get("limitations", [])) + list(corridor.assumptions),
        }
        registry[evidence_id] = {"type": "POPULATION_EXPOSURE_ESTIMATE", "source": estimated["source"]}
        evidence.put_derived_record({
            "observation_id": evidence_id,
            "event_id": event.event_id,
            "event_time_utc": _iso(event.detected_at_utc),
            "observed_at_utc": _iso(event.detected_at_utc),
            "source": estimated["source"],
            "evidence_type": "POPULATION_EXPOSURE_ESTIMATE",
            "latitude": event.latitude,
            "longitude": event.longitude,
            "record": result,
        })
        return result

    @tool
    def get_sensor_comparison(event_id: str) -> dict[str, Any]:
        """Compare independent sensor evidence attached to the same candidate event."""
        event = scoped_event(event_id)
        if event is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        records = evidence.list_for_event(event_id)
        satellite_rows = [row for row in records if row.get("evidence_type") not in {"WEATHER_ESTIMATE", "POPULATION_EXPOSURE_ESTIMATE"} and row.get("source")]
        sources = sorted({str(row.get("source")) for row in satellite_rows})
        if len(sources) < 2:
            return {
                "status": "INDEPENDENT_OBSERVATION_UNAVAILABLE",
                "sources": sources,
                "evidence_ids": [],
                "caveat": "No independent source observation is attached; absence is not a non-detection.",
            }
        from backend.common.models import FireObservation
        from backend.processing.comparison import compare_sensor_observations

        observations = []
        for row in satellite_rows:
            timestamp = _parse_time(row.get("observed_at_utc"))
            if timestamp is None or not row.get("observation_id"):
                continue
            try:
                observations.append(FireObservation(
                    fire_id=str(row["observation_id"]),
                    source=str(row["source"]),
                    observed_at_utc=timestamp,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    grid_id=str(row.get("grid_id") or event.grid_id),
                    confidence=None,
                    source_version=str(row.get("source_version") or "attached-evidence"),
                ))
            except (KeyError, TypeError, ValueError):
                continue
        primary_source = next((name for name in sources if name == event.sources[0]), sources[0])
        comparison_source = next(name for name in sources if name != primary_source)
        coverage_records = [row.get("record", {}) for row in records if row.get("evidence_type") == "SENSOR_COVERAGE"]
        result = compare_sensor_observations(observations, primary_source, comparison_source, coverage_records=coverage_records)
        result["evidence_ids"] = sorted({
            evidence_id
            for match in result.get("matches", [])
            for evidence_id in (match.get("primary_evidence_id"), match.get("comparison_evidence_id"))
            if evidence_id
        })
        comparison_id = "cmp_" + hashlib.sha256(event.event_id.encode()).hexdigest()[:24]
        evidence.put_derived_record({
            "observation_id": comparison_id,
            "event_id": event.event_id,
            "event_time_utc": _iso(event.detected_at_utc),
            "observed_at_utc": _iso(event.detected_at_utc),
            "source": "BURNBLIND_CROSS_SENSOR_COMPARISON",
            "evidence_type": "SENSOR_COMPARISON",
            "latitude": event.latitude,
            "longitude": event.longitude,
            "record": result,
        })
        return result

    environment_packet: dict[str, dict[str, Any]] = {}
    return [get_event, get_satellite_evidence, get_historical_context, get_weather, get_exposure, get_sensor_comparison]


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _plain(value: Any) -> Any:
    from decimal import Decimal

    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _dynamo_safe(value: Any) -> Any:
    from decimal import Decimal

    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _dynamo_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_dynamo_safe(item) for item in value]
    return value
