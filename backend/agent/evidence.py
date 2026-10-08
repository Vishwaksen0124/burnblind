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
        return result.get("Items", [])


def build_evidence_tools(
    events: CandidateEventRepository,
    evidence: DynamoEvidenceRepository,
    registry: dict[str, dict[str, str]],
    weather_lookup: Callable[..., Any] | None = None,
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
    def get_weather_context(event_id: str) -> dict[str, Any]:
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
        return {
            "status": "OK",
            "evidence_id": evidence_id,
            "source": weather.source,
            "source_version": weather.source_version,
            "observed_at_utc": _iso(weather.observed_at_utc),
            "wind_speed_m_s": weather.wind_speed_m_s,
            "wind_direction_degrees": weather.wind_direction_degrees,
            "interpretation": "Historical reanalysis estimate; not a direct local measurement.",
        }

    @tool
    def get_exposure_context(event_id: str) -> dict[str, Any]:
        """Read an estimated population exposure value when one is available."""
        if scoped_event(event_id) is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        return {"status": "UNAVAILABLE", "detail": "No population estimate is attached to this event."}

    @tool
    def get_sensor_comparison(event_id: str) -> dict[str, Any]:
        """Compare independent sensor evidence attached to the same candidate event."""
        event = scoped_event(event_id)
        if event is None:
            return {"status": "NOT_FOUND", "event_id": event_id}
        records = evidence.list_for_event(event_id)
        sources = sorted({str(row.get("source", "UNKNOWN")) for row in records})
        if len(sources) > 1:
            return {
                "status": "MULTIPLE_SOURCES_CO_CLUSTERED",
                "sources": sources,
                "evidence_ids": [str(row["observation_id"]) for row in records if row.get("observation_id")],
                "caveat": "Co-clustering is not proof of independent confirmation.",
            }
        return {
            "status": "NO_INDEPENDENT_RECORD_ATTACHED",
            "sources": sources,
            "caveat": "No independent source record is attached to this event; that is not evidence of a sensor non-detection.",
        }

    return [get_event, get_satellite_evidence, get_historical_context, get_weather_context, get_exposure_context, get_sensor_comparison]


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
