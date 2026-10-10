from backend.features.environmental import _has_blindness_score, _valid_scoring_coverage


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
