import pytest

from backend.scoring.stream_trigger import evaluate_score_features


def test_empty_score_features_do_not_qualify_on_missingness_alone():
    decision = evaluate_score_features({})

    assert not decision["should_investigate"]
    assert decision["reasons"] == []
    assert decision["uncertainty"] == 1


def test_high_uncertainty_qualifies_only_with_supported_likelihood_input():
    decision = evaluate_score_features({"thermal_signal": 0.8})

    assert decision["should_investigate"]
    assert decision["reasons"] == ["HIGH_UNCERTAINTY"]
    assert decision["fire_likelihood_score"] == pytest.approx(0.8)


def test_high_priority_and_exposure_reasons_are_recorded():
    decision = evaluate_score_features({
        "observation_gap_risk": 1,
        "sensor_coverage_gap": 1,
        "data_quality_risk": 1,
        "timing_risk": 1,
        "thermal_signal": 1,
        "historical_activity": 1,
        "independent_detection_support": 1,
        "exposure_score": 1,
        "urgency_score": 1,
    })

    assert decision["should_investigate"]
    assert "HIGH_PRIORITY" in decision["reasons"]
    assert "HIGH_EXPOSURE" in decision["reasons"]


def test_unknown_score_feature_is_rejected():
    with pytest.raises(ValueError, match="unsupported fields"):
        evaluate_score_features({"unverified_feature": 0.9})
