from backend.features.environmental import _has_blindness_score, _valid_scoring_coverage
from backend.features.environmental import EnvironmentalAnalysisService
from datetime import datetime, timezone
from types import SimpleNamespace


def test_positive_sensor_detection_cannot_be_used_as_coverage_or_zero_blindness():
    row = {
        "evidence_type": "SENSOR_COVERAGE",
        "source": "VIIRS_NOAA20",
        "record": {
            "quality_valid": True,
            "detection_present": True,
            "evidence_id": "observation-derived-fake-coverage",
            "source": "VIIRS_NOAA20",
            "coverage_radius_km": 5,
        },
    }

    assert not _valid_scoring_coverage(row)
    assert not _has_blindness_score(row["record"])


def test_coverage_measurement_without_computed_score_does_not_report_zero():
    row = {
        "evidence_type": "SENSOR_COVERAGE",
        "source": "VIIRS_NOAA20",
        "record": {
            "quality_valid": True,
            "detection_present": False,
            "evidence_id": "coverage-source-1",
            "source": "VIIRS_NOAA20",
            "observation_gap_hours": 0,
        },
    }

    assert _valid_scoring_coverage(row)
    assert not _has_blindness_score(row["record"])


def test_only_versioned_normalized_score_with_evidence_lineage_is_reported():
    record = {
        "blindness_score": 0.0,
        "score_version": "score-v1",
        "score_evidence_ids": ["coverage-source-1"],
    }

    assert _has_blindness_score(record)
    assert not _has_blindness_score({**record, "blindness_score": 1.01})
    assert not _has_blindness_score({**record, "score_evidence_ids": []})


def test_available_score_features_persist_when_weather_and_exposure_are_unavailable():
    event = SimpleNamespace(
        event_id="evt_0123456789abcdef01234567",
        grid_id="grid-v1-utm43n-132-672",
        detected_at_utc=datetime(2025, 10, 1, 10, tzinfo=timezone.utc),
        last_observed_at_utc=datetime(2025, 10, 1, 10, tzinfo=timezone.utc),
        latitude=30.5,
        longitude=76.5,
    )
    initial_rows = [{
        "observation_id": "gk2a-observation-1",
        "event_id": event.event_id,
        "evidence_type": "SATELLITE_OBSERVATION",
        "source": "GK2A_AMI",
        "observed_at_utc": "2025-10-01T10:00:00Z",
        "brightness_temperature_difference_ref": 15,
    }]

    class Events:
        updates = []

        def get(self, event_id):
            return event if event_id == event.event_id else None

        def put_feature_context(self, event_id, features):
            self.updates.append(features)

    class Evidence:
        def __init__(self):
            self.rows = list(initial_rows)

        def list_for_event(self, event_id):
            return list(self.rows)

        def put_derived_record(self, record):
            self.rows.append(record)

    events = Events()
    service = EnvironmentalAnalysisService(events, Evidence())
    service._weather = lambda _: {"status": "UNAVAILABLE"}
    service._comparison = lambda _: {"status": "INDEPENDENT_OBSERVATION_UNAVAILABLE", "evidence_ids": []}

    result = service.analyze(event.event_id)

    assert result["environmental_analysis"]["status"] == "PARTIAL"
    assert result["environmental_analysis"]["historical_context"]["status"] == "OK"
    score_update = next(update for update in events.updates if "score_features" in update)
    assert score_update["score_features"]["thermal_signal"] == 0.5
    assert score_update["score_features"]["historical_activity"] is not None
    assert score_update["score_feature_evidence_ids"]["historical_activity"]
    assert "exposure_score" not in score_update["score_features"]
