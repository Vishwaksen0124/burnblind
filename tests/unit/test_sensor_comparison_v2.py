from datetime import datetime, timedelta, timezone

from backend.common.models import FireObservation
from backend.processing.comparison import compare_sensor_observations


TIME = datetime(2025, 10, 1, 10, tzinfo=timezone.utc)


def observation(evidence_id, source, time=TIME, latitude=30.9, longitude=75.8):
    return FireObservation(
        fire_id=evidence_id,
        source=source,
        observed_at_utc=time,
        latitude=latitude,
        longitude=longitude,
        grid_id="grid-v1-cell",
        confidence=None,
        source_version="fixture-v1",
    )


def test_matching_independent_records_report_agreement_with_deltas():
    result = compare_sensor_observations(
        [observation("gk2-1", "GK2A"), observation("viirs-1", "VIIRS", TIME + timedelta(minutes=8), 30.91, 75.81)],
        "GK2A", "VIIRS",
    )

    assert result["status"] == "AGREEMENT"
    assert result["matches"][0]["primary_evidence_id"] == "gk2-1"
    assert result["matches"][0]["temporal_delta_minutes"] == 8
    assert result["matches"][0]["spatial_delta_km"] > 0


def test_only_explicit_quality_valid_negative_coverage_can_disagree():
    primary = observation("gk2-1", "GK2A")
    coverage = {
        "evidence_id": "viirs-pass-1", "source": "VIIRS", "observed_at_utc": "2025-10-01T10:10:00Z",
        "latitude": 30.9, "longitude": 75.8, "coverage_radius_km": 1.5,
        "quality_valid": True, "detection_present": False,
    }

    result = compare_sensor_observations([primary], "GK2A", "VIIRS", coverage_records=[coverage])

    assert result["status"] == "DISAGREEMENT"
    assert result["matches"][0]["comparison_evidence_id"] == "viirs-pass-1"
    assert "explicitly reports no detection" in result["reason"]


def test_absent_or_low_quality_comparison_is_not_disagreement():
    primary = observation("gk2-1", "GK2A")
    low_quality = {
        "evidence_id": "viirs-pass-1", "source": "VIIRS", "observed_at_utc": "2025-10-01T10:10:00Z",
        "latitude": 30.9, "longitude": 75.8, "coverage_radius_km": 1,
        "quality_valid": False, "detection_present": False,
    }

    result = compare_sensor_observations([primary], "GK2A", "VIIRS", coverage_records=[low_quality])

    assert result["status"] == "INDEPENDENT_OBSERVATION_UNAVAILABLE"


def test_nonmatching_observations_are_inconclusive_not_negative():
    result = compare_sensor_observations(
        [observation("gk2-1", "GK2A"), observation("viirs-1", "VIIRS", TIME + timedelta(hours=2), 31.4, 76.3)],
        "GK2A", "VIIRS",
    )

    assert result["status"] == "INCONCLUSIVE"
