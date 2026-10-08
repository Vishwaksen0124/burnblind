from datetime import datetime, timedelta, timezone

import pytest

from backend.processing.temporal import observation_gap_hours


def test_observation_gap_uses_utc_elapsed_hours():
    event_time = datetime(2025, 10, 1, 12, 0, tzinfo=timezone.utc)
    observed = event_time - timedelta(hours=3, minutes=30)

    assert observation_gap_hours(observed, event_time) == 3.5


def test_observation_gap_returns_missing_when_source_observation_is_absent():
    assert observation_gap_hours(None, datetime(2025, 10, 1, tzinfo=timezone.utc)) is None


def test_observation_gap_rejects_future_observations():
    event_time = datetime(2025, 10, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="after event time"):
        observation_gap_hours(event_time + timedelta(minutes=1), event_time)


def test_observation_gap_requires_timezone_aware_inputs():
    with pytest.raises(ValueError, match="timezone-aware"):
        observation_gap_hours(None, datetime(2025, 10, 1))
