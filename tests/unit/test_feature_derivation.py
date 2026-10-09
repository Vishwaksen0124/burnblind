from datetime import datetime, timezone

import pytest

from backend.processing.feature_derivation import derive_score_features


EVENT_TIME = datetime(2025, 10, 1, 10, tzinfo=timezone.utc)
NORMALIZATION = {
    "max_observation_gap_hours": 24,
    "thermal_signal_max_delta_k": 15,
    "historical_hits_per_year_max": 10,
    "exposure_population_max": 100000,
}


def test_missing_inputs_remain_unavailable_instead_of_becoming_zeros():
    derived = derive_score_features({}, event_time_utc=EVENT_TIME, normalization=NORMALIZATION, version="feature-v2")

    assert derived.features.thermal_signal is None
    assert derived.features.independent_detection_support is None
    assert derived.features.exposure_score is None
    assert derived.available_feature_count == 0
    assert derived.features.sensor_disagreement is False


def test_measured_features_are_normalized_and_keep_evidence_lineage():
    packet = {
        "coverage": {
            "observation_gap_hours": 6,
            "expected_sensor_count": 2,
            "available_sensor_count": 1,
            "valid_observation_fraction": 0.75,
            "evidence_ids": ["coverage-1"],
        },
        "observations": [{
            "evidence_id": "gk2-1", "source": "GK2A_AMI", "observed_at_utc": "2025-10-01T09:55:00Z",
            "brightness_temperature_difference_ref": 7.5,
        }],
        "history": {
            "detection_count": 10, "years_covered": 5,
            "latest_observation_at_utc": "2024-11-01T10:00:00Z", "evidence_ids": ["history-1"],
        },
        "sensor_comparison": {"status": "DISAGREEMENT", "evidence_ids": ["gk2-1", "viirs-pass-1"]},
        "exposure": {"population_estimate": 50000, "evidence_ids": ["worldpop-1"]},
    }

    derived = derive_score_features(packet, event_time_utc=EVENT_TIME, normalization=NORMALIZATION, version="feature-v2")

    assert derived.features.observation_gap_risk == 0.25
    assert derived.features.sensor_coverage_gap == 0.5
    assert derived.features.data_quality_risk == 0.25
    assert derived.features.thermal_signal == 0.5
    assert derived.features.historical_activity == 0.2
    assert derived.features.sensor_disagreement is True
    assert derived.features.independent_detection_support == 0
    assert derived.features.exposure_score == 0.5
    assert derived.evidence_ids_by_feature["sensor_coverage_gap"] == ("coverage-1",)
    assert "viirs-pass-1" in derived.evidence_ids_by_feature["independent_detection_support"]


def test_future_satellite_record_is_rejected_to_prevent_leakage():
    packet = {"observations": [{
        "evidence_id": "future", "source": "GK2A_AMI", "observed_at_utc": "2025-10-01T10:01:00Z",
        "brightness_temperature_difference_ref": 8,
    }]}

    with pytest.raises(ValueError, match="after the event time"):
        derive_score_features(packet, event_time_utc=EVENT_TIME, normalization=NORMALIZATION, version="feature-v2")


def test_feature_inputs_without_evidence_ids_are_rejected():
    packet = {"exposure": {"population_estimate": 12000}}

    with pytest.raises(ValueError, match="require evidence_ids"):
        derive_score_features(packet, event_time_utc=EVENT_TIME, normalization=NORMALIZATION, version="feature-v2")
