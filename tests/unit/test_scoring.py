from pathlib import Path

import pytest

from backend.scoring.engine import ScoreFeatures, investigation_trigger, load_score_config, score_event


CONFIG = Path(__file__).resolve().parents[2] / "config" / "scoring.v1.json"


@pytest.fixture
def config():
    return load_score_config(CONFIG)


def test_score_is_deterministic_and_fully_supported_features_rank_to_one(config):
    features = ScoreFeatures(
        observation_gap_risk=1,
        sensor_coverage_gap=1,
        data_quality_risk=1,
        timing_risk=1,
        thermal_signal=1,
        historical_activity=1,
        independent_detection_support=1,
        exposure_score=1,
        urgency_score=1,
    )

    first = score_event(features, config)
    second = score_event(features, config)

    assert first == second
    assert first.blindness_score == 1
    assert first.fire_likelihood_score == 1
    assert first.priority_score == 1
    assert first.uncertainty == 0
    assert first.score_version == "score-v1"


def test_priority_is_unavailable_when_exposure_or_urgency_is_missing(config):
    features = ScoreFeatures(
        observation_gap_risk=0.8,
        thermal_signal=0.7,
        independent_detection_support=0.9,
    )

    result = score_event(features, config)

    assert result.blindness_score == 0.8
    assert result.fire_likelihood_score == pytest.approx(0.8)
    assert result.priority_score is None


def test_sensor_disagreement_increases_uncertainty_without_boosting_fire_score(config):
    base = ScoreFeatures(thermal_signal=0.6, sensor_disagreement=False)
    conflict = ScoreFeatures(thermal_signal=0.6, sensor_disagreement=True)

    base_result = score_event(base, config)
    conflict_result = score_event(conflict, config)

    assert conflict_result.fire_likelihood_score == base_result.fire_likelihood_score
    assert conflict_result.uncertainty > base_result.uncertainty


def test_investigation_trigger_records_each_applicable_policy_reason(config):
    result = score_event(
        ScoreFeatures(
            observation_gap_risk=1,
            sensor_coverage_gap=1,
            data_quality_risk=1,
            timing_risk=1,
            thermal_signal=1,
            historical_activity=1,
            independent_detection_support=1,
            exposure_score=1,
            urgency_score=1,
        ),
        config,
    )

    trigger = investigation_trigger(result, config, exposure_score=1)

    assert trigger.should_investigate
    assert "HIGH_PRIORITY" in trigger.reasons
    assert "HIGH_EXPOSURE" in trigger.reasons


def test_feature_inputs_reject_non_normalized_values():
    with pytest.raises(ValueError, match="normalized"):
        ScoreFeatures(thermal_signal=1.1)
