from datetime import datetime, timezone
from types import SimpleNamespace

from backend.ingestion.historical_context import build_event_historical_evidence


def test_same_grid_month_history_uses_only_complete_prior_years():
    event = SimpleNamespace(
        event_id="evt_0123456789abcdef01234567",
        grid_id="grid-v1-utm43n-130-677",
        detected_at_utc=datetime(2025, 10, 1, 10, tzinfo=timezone.utc),
        latitude=30.5,
        longitude=76.5,
    )
    index = {
        "record_id": "20084790",
        "dataset_version": "v1",
        "months": [10, 11],
        "complete_years": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "by_grid_year_month": {
            event.grid_id: {
                "2019": {"10": 2},
                "2020": {"10": 3},
                "2024": {"10": 4},
                "2025": {"10": 100},
            }
        },
    }

    result = build_event_historical_evidence(event, index)

    assert result["record"]["detection_count"] == 9
    assert result["record"]["years_covered"] == 6
    assert result["record"]["coverage_years"] == [2019, 2020, 2021, 2022, 2023, 2024]
    assert result["record"]["source_version"] == "zenodo:20084790:v1"
    assert result["evidence_type"] == "HISTORICAL_CONTEXT"


def test_history_is_unavailable_outside_the_source_months():
    event = SimpleNamespace(
        event_id="evt_0123456789abcdef01234567",
        grid_id="grid-v1-utm43n-130-677",
        detected_at_utc=datetime(2025, 9, 1, 10, tzinfo=timezone.utc),
        latitude=30.5,
        longitude=76.5,
    )
    index = {
        "record_id": "20084790",
        "dataset_version": "v1",
        "months": [10, 11],
        "complete_years": [2019, 2020, 2021, 2022, 2023, 2024],
        "by_grid_year_month": {},
    }

    assert build_event_historical_evidence(event, index) is None
