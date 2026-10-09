"""DynamoDB implementation of the candidate-event repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.api.repository import (
    EventFilters,
    InvalidCursor,
    decode_cursor,
    encode_cursor,
    fingerprint_filters,
)
from backend.common.models import CandidateEvent


class DynamoCandidateEventRepository:
    """Queries the `data-mode-detected-at` GSI for replay/current events."""

    def __init__(self, table_name: str, table: Any | None = None):
        if table is None:
            import boto3

            table = boto3.resource("dynamodb").Table(table_name)
        self._table = table

    def get(self, event_id: str) -> CandidateEvent | None:
        result = self._table.get_item(Key={"event_id": event_id}, ConsistentRead=True)
        item = result.get("Item")
        return _to_event(item) if item else None

    def get_scoring_context(self, event_id: str) -> dict[str, Any] | None:
        item = self._table.get_item(Key={"event_id": event_id}, ConsistentRead=True).get("Item")
        if not item or not item.get("score_version"):
            return None
        keys = (
            "blindness_score", "fire_likelihood_score", "uncertainty",
            "priority_score", "score_version", "feature_version",
            "evidence_completeness", "investigation_qualifies",
            "investigation_trigger_reasons", "investigation_status",
        )
        return {
            key: _plain_number(item[key])
            for key in keys
            if key in item
        }

    def get_feature_context(self, event_id: str) -> dict[str, Any] | None:
        """Return allowlisted, source-backed feature records attached to an event."""
        item = self._table.get_item(Key={"event_id": event_id}, ConsistentRead=True).get("Item")
        if not item:
            return None
        allowed = ("blind_spot", "sensor_comparison", "exposure", "replay_timeline")
        return {key: item[key] for key in allowed if key in item}

    def list(
        self,
        filters: EventFilters,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[CandidateEvent], str | None]:
        if filters.status and filters.status != "CANDIDATE":
            return [], None
        if filters.priority:
            return [], None
        fingerprint = fingerprint_filters(filters)
        start_key = None
        if cursor:
            payload = decode_cursor(cursor, fingerprint)
            start_key = payload.get("last_key")
            if not isinstance(start_key, dict):
                raise InvalidCursor("cursor is missing a DynamoDB continuation key")

        expression_names = {"#mode": "data_mode"}
        expression_values = {":mode": "HISTORICAL_REPLAY"}
        key_condition = "#mode = :mode"
        if filters.start is not None or filters.end is not None:
            expression_names["#time"] = "detected_at_utc"
            if filters.start is not None and filters.end is not None:
                key_condition += " AND #time BETWEEN :start AND :end"
                expression_values[":start"] = _timestamp(filters.start)
                expression_values[":end"] = _timestamp(filters.end)
            elif filters.start is not None:
                key_condition += " AND #time >= :start"
                expression_values[":start"] = _timestamp(filters.start)
            else:
                key_condition += " AND #time <= :end"
                expression_values[":end"] = _timestamp(filters.end)

        selected: list[CandidateEvent] = []
        next_key = start_key
        continuation = None
        while len(selected) < limit:
            arguments = {
                "IndexName": "data-mode-detected-at",
                "KeyConditionExpression": key_condition,
                "ExpressionAttributeNames": expression_names,
                "ExpressionAttributeValues": expression_values,
                "ScanIndexForward": False,
                "Limit": max(100, limit - len(selected)),
            }
            if next_key:
                arguments["ExclusiveStartKey"] = next_key
            page = self._table.query(**arguments)
            for item in page.get("Items", []):
                event = _to_event(item)
                if _in_bbox(event, filters.bbox):
                    selected.append(event)
                    if len(selected) == limit:
                        continuation = _key_from_item(item)
                        break
            else:
                next_key = page.get("LastEvaluatedKey")
                if not next_key:
                    break
                continue
            break

        next_cursor = (
            encode_cursor({"query": fingerprint, "last_key": continuation})
            if continuation is not None
            else None
        )
        return selected, next_cursor

    def all(self) -> list[CandidateEvent]:
        events: list[CandidateEvent] = []
        cursor = None
        filters = EventFilters()
        while True:
            page, cursor = self.list(filters, 100, cursor)
            events.extend(page)
            if cursor is None:
                return events


def _timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _key_from_item(item: dict) -> dict:
    return {
        "event_id": item["event_id"],
        "data_mode": item["data_mode"],
        "detected_at_utc": item["detected_at_utc"],
    }


def _in_bbox(event: CandidateEvent, bbox: tuple[float, float, float, float] | None) -> bool:
    if bbox is None:
        return True
    west, south, east, north = bbox
    return west <= event.longitude <= east and south <= event.latitude <= north


def _to_event(item: dict) -> CandidateEvent:
    return CandidateEvent(
        event_id=item["event_id"],
        grid_id=item["grid_id"],
        detected_at_utc=datetime.fromisoformat(item["detected_at_utc"].replace("Z", "+00:00")),
        last_observed_at_utc=datetime.fromisoformat(item["last_observed_at_utc"].replace("Z", "+00:00")),
        latitude=float(item["latitude"]),
        longitude=float(item["longitude"]),
        detection_count=int(item["detection_count"]),
        sources=tuple(item["sources"]),
        evidence_ids=tuple(item["evidence_ids"]),
        data_mode=item["data_mode"],
        processing_version=item["processing_version"],
    )


def _plain_number(value):
    if isinstance(value, (int, float, bool)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return value
