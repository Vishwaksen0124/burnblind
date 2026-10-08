"""Temporal features with explicit missing-data and leakage handling."""

from datetime import datetime, timezone


def observation_gap_hours(
    most_recent_observation_utc: datetime | None,
    event_time_utc: datetime,
) -> float | None:
    """Return elapsed UTC hours, or None when the source observation is absent.

    Future observations are rejected to prevent time leakage in historical
    replay and evaluation.
    """
    if event_time_utc.tzinfo is None or event_time_utc.utcoffset() is None:
        raise ValueError("event_time_utc must be timezone-aware")
    if most_recent_observation_utc is None:
        return None
    if most_recent_observation_utc.tzinfo is None or most_recent_observation_utc.utcoffset() is None:
        raise ValueError("most_recent_observation_utc must be timezone-aware")

    observed = most_recent_observation_utc.astimezone(timezone.utc)
    event_time = event_time_utc.astimezone(timezone.utc)
    if observed > event_time:
        raise ValueError("most recent observation occurs after event time")
    return (event_time - observed).total_seconds() / 3600
