"""Persistence for human review outcomes, separate from agent reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


REVIEW_OUTCOMES = frozenset({
    "CONFIRMED",
    "FALSE_POSITIVE",
    "NEEDS_VERIFICATION",
    "INSUFFICIENT_EVIDENCE",
})


class DynamoReviewOutcomeStore:
    """Append-only event review history keyed by event and review timestamp."""

    def __init__(self, table: Any):
        self._table = table

    def list_for_event(self, event_id: str, limit: int = 20) -> list[dict[str, Any]]:
        response = self._table.query(
            KeyConditionExpression="event_id = :event_id",
            ExpressionAttributeValues={":event_id": event_id},
            ScanIndexForward=False,
            Limit=max(1, min(limit, 100)),
        )
        return response.get("Items", [])

    def record(self, event_id: str, outcome: str, notes: str, request_id: str, reviewer_id: str) -> dict[str, Any]:
        if outcome not in REVIEW_OUTCOMES:
            raise ValueError("unsupported review outcome")
        reviewed_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        item = {
            "event_id": event_id,
            "reviewed_at_utc": reviewed_at,
            "outcome": outcome,
            "notes": notes,
            "request_id": request_id,
            "reviewer_id": reviewer_id,
        }
        self._table.put_item(Item=item, ConditionExpression="attribute_not_exists(event_id) AND attribute_not_exists(reviewed_at_utc)")
        return item
