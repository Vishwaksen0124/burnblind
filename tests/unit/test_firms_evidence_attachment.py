from dataclasses import replace
from datetime import datetime, timedelta, timezone

from backend.common.models import CandidateEvent, FireObservation
from scripts.attach_firms_evidence import (
    _matches,
    _sensor_source,
    build_observation_evidence,
    build_sensor_comparison_evidence,
)


def _event():
    observed_at = datetime(2025, 11, 30, 11, 0, tzinfo=timezone.utc)
    return CandidateEvent(
        event_id="evt_0123456789abcdef01234567",
        grid_id="grid-v1-utm43n-5000m-1-1",
        detected_at_utc=observed_at,
        last_observed_at_utc=observed_at,
        latitude=30.65,
        longitude=75.71,
        detection_count=1,
        sources=("GK2A_AMI",),
        evidence_ids=("gk2a-1",),
        data_mode="HISTORICAL_REPLAY",
        processing_version="fixture-v1",
    )


def _observation(*, minutes=10, latitude=30.65, longitude=75.71):
    return FireObservation(
        fire_id="firms-source-1",
        source="NASA_FIRMS",
        observed_at_utc=datetime(2025, 11, 30, 11, 0, tzinfo=timezone.utc) + timedelta(minutes=minutes),
        latitude=latitude,
        longitude=longitude,
        grid_id="grid-v1-utm43n-5000m-1-1",
        confidence=None,
        source_version="firms:fixture-v1",
        satellite="N20",
        instrument="VIIRS",
    )


def test_attachment_persists_only_actual_sensor_observation():
    item = build_observation_evidence(_event(), _observation())

    assert item["evidence_type"] == "SENSOR_OBSERVATION"
    assert item["source"] == "VIIRS_NOAA20"
    assert item["record"]["provider"] == "NASA_FIRMS"
    assert item["record"]["evidence_id"] == item["observation_id"]
    assert "coverage_radius_km" not in item["record"]


def test_firms_satellite_codes_map_to_stable_sensor_names():
    assert _sensor_source(_observation()) == "VIIRS_NOAA20"
    snpp = replace(_observation(), satellite="N")
    assert _sensor_source(snpp) == "VIIRS_SNPP"


def test_sensor_comparison_requires_actual_independent_match():
    event = _event()
    primary = {
        "observation_id": "gk2a-1",
        "event_id": event.event_id,
        "observed_at_utc": event.detected_at_utc.isoformat().replace("+00:00", "Z"),
        "source": "GK2A_AMI",
        "evidence_type": "SENSOR_OBSERVATION",
        "latitude": event.latitude,
        "longitude": event.longitude,
    }

    result = build_sensor_comparison_evidence(event, [primary, build_observation_evidence(event, _observation())])

    assert result["evidence_type"] == "SENSOR_COMPARISON"
    assert result["record"]["status"] == "AGREEMENT"
    assert len(result["record"]["evidence_ids"]) == 2


def test_unmatched_observation_cannot_create_disagreement_or_comparison_record():
    event = _event()
    far_later = _observation(minutes=90, latitude=31.0, longitude=76.0)
    primary = {
        "observation_id": "gk2a-1",
        "event_id": event.event_id,
        "observed_at_utc": event.detected_at_utc.isoformat().replace("+00:00", "Z"),
        "source": "GK2A_AMI",
        "evidence_type": "SENSOR_OBSERVATION",
        "latitude": event.latitude,
        "longitude": event.longitude,
    }
    independent = build_observation_evidence(event, far_later)
    assert not _matches(event, far_later)
    result = build_sensor_comparison_evidence(event, [primary, independent])
    assert result["record"]["status"] == "INCONCLUSIVE"


def test_absent_independent_observation_does_not_create_comparison_record():
    event = _event()
    primary = {
        "observation_id": "gk2a-1",
        "event_id": event.event_id,
        "observed_at_utc": event.detected_at_utc.isoformat().replace("+00:00", "Z"),
        "source": "GK2A_AMI",
        "evidence_type": "SENSOR_OBSERVATION",
        "latitude": event.latitude,
        "longitude": event.longitude,
    }

    assert build_sensor_comparison_evidence(event, [primary]) is None
