"""Idempotent detection clustering into reviewable candidate events."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
import hashlib
import math
from typing import Iterable

from backend.common.models import CandidateEvent, FireObservation


PROCESSING_VERSION = "candidate-events-v1"


def build_candidate_events(
    records: Iterable[FireObservation],
    max_time_delta_hours: float = 3.0,
    data_mode: str = "HISTORICAL_REPLAY",
) -> list[CandidateEvent]:
    """Cluster detections sharing a metric cell within a bounded time span.

    The result is a candidate observation cluster, not a confirmed fire. The
    temporal bound is measured from each cluster's first record to prevent
    single-link chains from growing without limit.
    """
    if isinstance(max_time_delta_hours, bool) or not isinstance(max_time_delta_hours, (int, float)):
        raise ValueError("max_time_delta_hours must be numeric")
    if not math.isfinite(max_time_delta_hours) or max_time_delta_hours < 0:
        raise ValueError("max_time_delta_hours must be finite and non-negative")
    delta_limit = timedelta(hours=max_time_delta_hours)
    grouped: dict[str, list[FireObservation]] = defaultdict(list)
    for record in records:
        grouped[record.grid_id].append(record)

    events: list[CandidateEvent] = []
    for grid_id, grid_records in sorted(grouped.items()):
        ordered = sorted(grid_records, key=lambda item: (item.observed_at_utc, item.source, item.fire_id))
        cluster: list[FireObservation] = []
        cluster_start = None
        for record in ordered:
            if cluster and record.observed_at_utc - cluster_start > delta_limit:
                events.append(_make_candidate(grid_id, cluster, data_mode))
                cluster = []
                cluster_start = None
            if not cluster:
                cluster_start = record.observed_at_utc
            cluster.append(record)
        if cluster:
            events.append(_make_candidate(grid_id, cluster, data_mode))

    return sorted(events, key=lambda item: (item.detected_at_utc, item.grid_id, item.event_id))


def _make_candidate(grid_id: str, records: list[FireObservation], data_mode: str) -> CandidateEvent:
    evidence_ids = tuple(sorted(record.fire_id for record in records))
    digest = hashlib.sha256()
    digest.update(PROCESSING_VERSION.encode())
    digest.update(grid_id.encode())
    for evidence_id in evidence_ids:
        digest.update(b"\0")
        digest.update(evidence_id.encode())
    return CandidateEvent(
        event_id=f"evt_{digest.hexdigest()[:24]}",
        grid_id=grid_id,
        detected_at_utc=records[0].observed_at_utc,
        last_observed_at_utc=records[-1].observed_at_utc,
        latitude=sum(record.latitude for record in records) / len(records),
        longitude=sum(record.longitude for record in records) / len(records),
        detection_count=len(records),
        sources=tuple(sorted({record.source for record in records})),
        evidence_ids=evidence_ids,
        data_mode=data_mode,
        processing_version=PROCESSING_VERSION,
    )
