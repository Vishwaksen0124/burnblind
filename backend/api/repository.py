"""Local candidate-event repository used by the replay API and tests."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Iterable, Protocol

from backend.common.models import CandidateEvent


@dataclass(frozen=True, slots=True)
class EventFilters:
    start: datetime | None = None
    end: datetime | None = None
    bbox: tuple[float, float, float, float] | None = None
    status: str | None = None
    priority: str | None = None


class InvalidCursor(ValueError):
    """Pagination token is malformed or belongs to another query."""


class CandidateEventRepository(Protocol):
    def get(self, event_id: str) -> CandidateEvent | None: ...

    def list(
        self,
        filters: EventFilters,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[CandidateEvent], str | None]: ...

    def all(self) -> list[CandidateEvent]: ...


class MemoryCandidateEventRepository:
    def __init__(self, events: Iterable[CandidateEvent]):
        self._events = {event.event_id: event for event in events}

    def get(self, event_id: str) -> CandidateEvent | None:
        return self._events.get(event_id)

    def list(
        self,
        filters: EventFilters,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[CandidateEvent], str | None]:
        query_fingerprint = fingerprint_filters(filters)
        offset = _decode_cursor(cursor, query_fingerprint) if cursor else 0
        events = [
            event
            for event in self._events.values()
            if _matches(event, filters)
        ]
        events.sort(key=lambda event: (event.detected_at_utc, event.event_id), reverse=True)
        page = events[offset : offset + limit]
        next_offset = offset + len(page)
        next_cursor = _encode_cursor(next_offset, query_fingerprint) if next_offset < len(events) else None
        return page, next_cursor

    def all(self) -> list[CandidateEvent]:
        return list(self._events.values())


def load_replay_repository(path: str) -> MemoryCandidateEventRepository:
    """Load canonical sample detections and cluster them for local replay."""
    import json
    from pathlib import Path

    from backend.common.serialization import fire_observation_from_dict
    from backend.processing.events import build_candidate_events

    records = []
    with Path(path).open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            try:
                records.append(fire_observation_from_dict(json.loads(line)))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number}: invalid replay record: {exc}") from exc
    return MemoryCandidateEventRepository(build_candidate_events(records))


def _matches(event: CandidateEvent, filters: EventFilters) -> bool:
    if filters.start is not None and event.detected_at_utc < filters.start:
        return False
    if filters.end is not None and event.detected_at_utc > filters.end:
        return False
    if filters.status and filters.status != "CANDIDATE":
        return False
    # Candidate clusters have no priority score until deterministic features
    # and exposure inputs are available.
    if filters.priority:
        return False
    if filters.bbox is not None:
        west, south, east, north = filters.bbox
        if not (west <= event.longitude <= east and south <= event.latitude <= north):
            return False
    return True


def fingerprint_filters(filters: EventFilters) -> str:
    serializable = {
        "start": filters.start.isoformat() if filters.start else None,
        "end": filters.end.isoformat() if filters.end else None,
        "bbox": filters.bbox,
        "status": filters.status,
        "priority": filters.priority,
    }
    return hashlib.sha256(json.dumps(serializable, sort_keys=True).encode()).hexdigest()[:16]


def encode_cursor(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")


def decode_cursor(cursor: str, fingerprint: str) -> dict:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        payload = json.loads(raw)
        if not isinstance(payload, dict) or payload.get("query") != fingerprint:
            raise ValueError
        return payload
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursor("cursor is invalid for this query") from exc


def _encode_cursor(offset: int, fingerprint: str) -> str:
    return encode_cursor({"offset": offset, "query": fingerprint})


def _decode_cursor(cursor: str, fingerprint: str) -> int:
    try:
        payload = decode_cursor(cursor, fingerprint)
        offset = payload["offset"]
        if not isinstance(offset, int) or offset < 0:
            raise ValueError
        return offset
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise InvalidCursor("cursor is invalid for this query") from exc
