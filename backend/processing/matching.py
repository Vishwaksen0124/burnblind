"""Deterministic cross-source detection matching on the canonical grid."""

from dataclasses import dataclass
from datetime import timedelta
import math
from typing import Iterable

from backend.common.models import FireObservation


@dataclass(frozen=True, slots=True)
class DetectionMatch:
    grid_id: str
    left_id: str
    left_source: str
    left_time_utc: str
    right_id: str
    right_source: str
    right_time_utc: str
    temporal_delta_hours: float
    matching_rule: str


def match_cross_source_detections(
    records: Iterable[FireObservation],
    max_time_delta_hours: float = 3.0,
) -> list[DetectionMatch]:
    """Return all cross-source pairs sharing a grid and time window.

    A match means two products reported detections in the same 5 km cell
    within the selected temporal window. A missing pair is not evidence that a
    sensor failed to observe or missed a fire.
    """
    if isinstance(max_time_delta_hours, bool) or not isinstance(max_time_delta_hours, (int, float)):
        raise ValueError("max_time_delta_hours must be numeric")
    if not math.isfinite(max_time_delta_hours) or max_time_delta_hours < 0:
        raise ValueError("max_time_delta_hours must be finite and non-negative")
    window = timedelta(hours=max_time_delta_hours)

    grouped: dict[str, dict[str, list[FireObservation]]] = {}
    for record in records:
        grouped.setdefault(record.grid_id, {}).setdefault(record.source, []).append(record)

    matches: list[DetectionMatch] = []
    for grid_id in sorted(grouped):
        sources = grouped[grid_id]
        source_names = sorted(sources)
        for left_index, left_source in enumerate(source_names):
            left_records = sorted(sources[left_source], key=lambda item: (item.observed_at_utc, item.fire_id))
            for right_source in source_names[left_index + 1 :]:
                right_records = sorted(sources[right_source], key=lambda item: (item.observed_at_utc, item.fire_id))
                first_possible = 0
                for left in left_records:
                    while (
                        first_possible < len(right_records)
                        and right_records[first_possible].observed_at_utc < left.observed_at_utc - window
                    ):
                        first_possible += 1
                    candidate_index = first_possible
                    while candidate_index < len(right_records):
                        right = right_records[candidate_index]
                        delta = abs(right.observed_at_utc - left.observed_at_utc)
                        if right.observed_at_utc > left.observed_at_utc + window:
                            break
                        if delta <= window:
                            matches.append(
                                DetectionMatch(
                                    grid_id=grid_id,
                                    left_id=left.fire_id,
                                    left_source=left.source,
                                    left_time_utc=left.observed_at_utc.isoformat().replace("+00:00", "Z"),
                                    right_id=right.fire_id,
                                    right_source=right.source,
                                    right_time_utc=right.observed_at_utc.isoformat().replace("+00:00", "Z"),
                                    temporal_delta_hours=delta.total_seconds() / 3600,
                                    matching_rule=f"same_grid_within_{max_time_delta_hours:g}_hours",
                                )
                            )
                        candidate_index += 1

    return sorted(
        matches,
        key=lambda item: (
            item.grid_id,
            item.left_time_utc,
            item.left_source,
            item.left_id,
            item.right_time_utc,
            item.right_source,
            item.right_id,
        ),
    )
