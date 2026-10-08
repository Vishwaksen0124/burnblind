from datetime import datetime, timedelta, timezone

from backend.common.models import FireObservation
from backend.processing.matching import match_cross_source_detections


def detection(fire_id, source, observed_at, grid_id="grid-v1-utm43n-5000m-1-1"):
    return FireObservation(
        fire_id=fire_id,
        source=source,
        observed_at_utc=observed_at,
        latitude=30.9,
        longitude=75.85,
        grid_id=grid_id,
        confidence=None,
        source_version="fixture-v1",
    )


def test_matcher_pairs_only_cross_source_detections_in_same_grid_and_time_window():
    timestamp = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    records = [
        detection("gk2a_1", "GK2A_AMI", timestamp),
        detection("firms_1", "NASA_FIRMS", timestamp + timedelta(hours=2)),
        detection("firms_2", "NASA_FIRMS", timestamp + timedelta(hours=4)),
        detection("firms_other_grid", "NASA_FIRMS", timestamp, "grid-v1-utm43n-2-1"),
    ]

    matches = match_cross_source_detections(records, max_time_delta_hours=3)

    assert len(matches) == 1
    assert matches[0].left_id == "gk2a_1"
    assert matches[0].right_id == "firms_1"
    assert matches[0].temporal_delta_hours == 2
    assert "same_grid" in matches[0].matching_rule


def test_matcher_does_not_infer_non_detection_as_sensor_failure():
    timestamp = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    matches = match_cross_source_detections([detection("gk2a_1", "GK2A_AMI", timestamp)])

    assert matches == []


def test_matcher_output_order_is_independent_of_input_order():
    timestamp = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    records = [
        detection("gk2a_2", "GK2A_AMI", timestamp + timedelta(minutes=30)),
        detection("firms_2", "NASA_FIRMS", timestamp + timedelta(minutes=45)),
        detection("gk2a_1", "GK2A_AMI", timestamp),
        detection("firms_1", "NASA_FIRMS", timestamp + timedelta(minutes=10)),
    ]

    first = match_cross_source_detections(records)
    second = match_cross_source_detections(reversed(records))

    assert first == second
