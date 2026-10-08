from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from backend.ingestion.open_meteo import WeatherSourceError, historical_wind


def test_historical_wind_requests_era5_in_utc_and_returns_hourly_values():
    captured = {}

    def fake_get(url):
        captured["url"] = url
        return {
            "hourly": {
                "time": ["2025-10-01T07:00"],
                "wind_speed_10m": [3.2],
                "wind_direction_10m": [240],
            }
        }

    weather = historical_wind(
        30.9,
        75.85,
        datetime(2025, 10, 1, 7, 42, tzinfo=timezone.utc),
        json_getter=fake_get,
    )
    params = parse_qs(urlparse(captured["url"]).query)

    assert params["models"] == ["era5"]
    assert params["timezone"] == ["UTC"]
    assert weather.observed_at_utc.isoformat() == "2025-10-01T07:00:00+00:00"
    assert weather.wind_speed_m_s == 3.2
    assert weather.wind_direction_degrees == 240
    assert weather.source == "OPEN_METEO_ERA5_REANALYSIS"


def test_historical_wind_keeps_unavailable_values_missing():
    weather = historical_wind(
        30.9,
        75.85,
        datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc),
        json_getter=lambda _: {
            "hourly": {
                "time": ["2025-10-01T07:00"],
                "wind_speed_10m": [None],
                "wind_direction_10m": [None],
            }
        },
    )

    assert weather.wind_speed_m_s is None
    assert weather.wind_direction_degrees is None


def test_historical_wind_rejects_bad_response_values():
    with pytest.raises(WeatherSourceError, match="invalid wind_speed_10m"):
        historical_wind(
            30.9,
            75.85,
            datetime(2025, 10, 1, 7, tzinfo=timezone.utc),
            json_getter=lambda _: {
                "hourly": {
                    "time": ["2025-10-01T07:00"],
                    "wind_speed_10m": [float("nan")],
                    "wind_direction_10m": [10],
                }
            },
        )
