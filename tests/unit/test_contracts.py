from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.common.models import (
    Classification,
    ContractError,
    Event,
    EventStatus,
    FireObservation,
    Investigation,
    InvestigationStatus,
    Observation,
    PopulationEstimate,
    WeatherObservation,
)
from backend.common.serialization import fire_observation_from_dict, fire_observation_to_dict
from backend.ingestion.historical_context import query_historical_context, summarize_detections


NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def observation():
    # Synthetic contract fixture; this is not satellite evidence.
    return Observation(
        observation_id="sample_obs_001",
        source="SAMPLE",
        timestamp_utc=NOW,
        latitude=30.9,
        longitude=75.85,
        grid_id="sample_grid_001",
        thermal_anomaly=None,
        quality=None,
        source_version="synthetic-v1",
    )


def test_observation_normalizes_timestamp_to_utc(observation):
    assert observation.timestamp_utc.tzinfo == timezone.utc


def test_observation_rejects_naive_timestamp(observation):
    with pytest.raises(ContractError, match="timezone-aware"):
        replace(observation, timestamp_utc=datetime(2026, 10, 8, 12))


def test_observation_rejects_invalid_coordinates(observation):
    with pytest.raises(ContractError, match="latitude"):
        replace(observation, latitude=91)


def test_event_rejects_non_normalized_score():
    with pytest.raises(ContractError, match="blindness_score"):
        Event(
            event_id="evt_sample_001",
            grid_id="grid_sample_001",
            detected_at_utc=NOW,
            latitude=30.9,
            longitude=75.85,
            observation_gap_hours=None,
            blindness_score=1.1,
            fire_likelihood=0.5,
            uncertainty=0.5,
            exposure_estimate=None,
            priority_score=0.5,
            status=EventStatus.CANDIDATE,
            investigation_status=InvestigationStatus.NOT_REQUIRED,
            feature_version="features-v1",
            scoring_version="scores-v1",
        )


def test_event_accepts_missing_optional_measurements():
    event = Event(
        event_id="evt_sample_001",
        grid_id="grid_sample_001",
        detected_at_utc=NOW,
        latitude=30.9,
        longitude=75.85,
        observation_gap_hours=None,
        blindness_score=0.5,
        fire_likelihood=0.5,
        uncertainty=0.7,
        exposure_estimate=None,
        priority_score=0.5,
        status=EventStatus.CANDIDATE,
        investigation_status=InvestigationStatus.NOT_REQUIRED,
        feature_version="features-v1",
        scoring_version="scores-v1",
    )
    assert event.observation_gap_hours is None
    assert event.exposure_estimate is None


def test_investigation_time_order_is_part_of_contract():
    with pytest.raises(ContractError, match="cannot precede"):
        Investigation(
            investigation_id="inv_sample_001",
            event_id="evt_sample_001",
            agent_version="agent-v1",
            prompt_version="prompt-v1",
            started_at_utc=NOW,
            completed_at_utc=NOW - timedelta(minutes=1),
            classification=Classification.REVIEW_REQUIRED,
            confidence=0.5,
        )


def test_weather_and_population_contracts_validate_units_and_ranges():
    weather = WeatherObservation(
        observed_at_utc=NOW,
        latitude=30.9,
        longitude=75.85,
        wind_speed_m_s=2.5,
        wind_direction_degrees=359.0,
        source="OPEN_METEO",
        source_version="era5-v1",
    )
    population = PopulationEstimate(
        grid_id="grid_sample_001",
        population=1000,
        estimate_year=2021,
        source="WORLDPOP",
        source_version="india-2021",
    )
    assert weather.wind_direction_degrees == 359.0
    assert population.population == 1000
    with pytest.raises(ContractError, match="wind_direction_degrees"):
        replace(weather, wind_direction_degrees=360)
    with pytest.raises(ContractError, match="population"):
        replace(population, population=-1)


def test_fire_observation_json_round_trip_preserves_evidence():
    record = FireObservation(
        fire_id="sample_fire_001",
        source="GK2A_AMI",
        observed_at_utc=NOW,
        latitude=30.9,
        longitude=75.85,
        grid_id="grid_sample_001",
        confidence=None,
        source_version="zenodo:20084790:v1",
        brightness_temperature_difference_ref=7.3,
        brightness_temperature_038_micron_k=304.3,
        brightness_temperature_112_micron_k=293.6,
        confidence_flag=1,
    )
    assert fire_observation_from_dict(fire_observation_to_dict(record)) == record


def test_historical_context_counts_detections_by_ist_dimensions():
    record = FireObservation(
        fire_id="sample_fire_001",
        source="GK2A_AMI",
        observed_at_utc=datetime(2025, 10, 1, 7, 30, tzinfo=timezone.utc),
        latitude=30.9,
        longitude=75.85,
        grid_id="grid_sample_001",
        confidence=None,
        source_version="zenodo:20084790:v1",
    )

    summary = summarize_detections([record])

    assert summary["total_detections"] == 1
    assert summary["by_year"] == {"2025": 1}
    assert summary["by_month_ist"] == {"10": 1}
    assert summary["by_hour_ist"] == {"13": 1}
    assert summary["by_grid_month_ist"]["grid_sample_001"] == {"10": 1}
    assert summary["by_grid_year_month"]["grid_sample_001"] == {"2025": {"10": 1}}
    assert summary["by_grid_hour_ist"]["grid_sample_001"] == {"2025-10-01T13:00:00+05:30": 1}
    assert query_historical_context(summary, "grid_sample_001", NOW)[
        "historical_detections_in_same_month_prior_years"
    ] == 1


def test_historical_query_excludes_detections_after_cutoff():
    from backend.common.models import FireObservation

    earlier = FireObservation(
        fire_id="sample_fire_early",
        source="GK2A_AMI",
        observed_at_utc=datetime(2025, 10, 1, 7, 30, tzinfo=timezone.utc),
        latitude=30.9,
        longitude=75.85,
        grid_id="grid_sample_001",
        confidence=None,
        source_version="zenodo:20084790:v1",
    )
    later = replace(
        earlier,
        fire_id="sample_fire_late",
        observed_at_utc=datetime(2025, 10, 2, 7, 30, tzinfo=timezone.utc),
    )
    summary = summarize_detections([earlier, later])

    result = query_historical_context(
        summary,
        "grid_sample_001",
        datetime(2025, 10, 1, 8, 0, tzinfo=timezone.utc),
    )

    assert result["historical_detections_through_as_of_hour"] == 1
    assert result["historical_detections_in_same_month_prior_years"] == 0
