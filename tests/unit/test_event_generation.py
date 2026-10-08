from datetime import datetime, timedelta, timezone

from backend.common.models import FireObservation
from backend.processing.events import build_candidate_events


def observation(fire_id, source, time, grid="grid-v1-utm43n-5000m-1-1", latitude=30.9, longitude=75.85):
    return FireObservation(
        fire_id=fire_id,
        source=source,
        observed_at_utc=time,
        latitude=latitude,
        longitude=longitude,
        grid_id=grid,
        confidence=None,
        source_version="fixture-v1",
    )


def test_event_generation_groups_same_grid_and_time_but_keeps_distant_records_separate():
    start = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    records = [
        observation("obs_1", "GK2A_AMI", start),
        observation("obs_2", "NASA_FIRMS", start + timedelta(hours=2), latitude=30.91),
        observation("obs_3", "GK2A_AMI", start + timedelta(hours=4)),
        observation("obs_4", "NASA_FIRMS", start, grid="grid-v1-utm43n-2-1"),
    ]

    events = build_candidate_events(records, max_time_delta_hours=3)

    assert len(events) == 3
    merged = next(event for event in events if event.detection_count == 2)
    assert set(merged.sources) == {"GK2A_AMI", "NASA_FIRMS"}
    assert merged.data_mode == "HISTORICAL_REPLAY"
    assert merged.event_id.startswith("evt_")
    assert merged.latitude == 30.905


def test_event_ids_and_order_are_deterministic():
    start = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    records = [
        observation("obs_1", "GK2A_AMI", start),
        observation("obs_2", "NASA_FIRMS", start + timedelta(minutes=20)),
    ]

    first = build_candidate_events(records)
    second = build_candidate_events(reversed(records))

    assert first == second


def test_event_generation_prevents_single_link_time_chain_growth():
    start = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    records = [
        observation(f"obs_{index}", "GK2A_AMI", start + timedelta(hours=hour))
        for index, hour in enumerate((0, 2, 4), start=1)
    ]

    events = build_candidate_events(records, max_time_delta_hours=3)

    assert [event.detection_count for event in events] == [2, 1]
