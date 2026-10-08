"""Historical ERA5 wind context from the Open-Meteo archive API."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.common.models import WeatherObservation


ARCHIVE_ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
MODEL = "era5"


class WeatherSourceError(RuntimeError):
    """The weather provider could not return a valid response."""


def _get_json(url: str) -> Mapping[str, Any]:
    request = Request(url, headers={"User-Agent": "BurnBlind/0.1 environmental context"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise WeatherSourceError(f"Open-Meteo archive request failed: {type(exc).__name__}") from exc


def _optional_number(values: Any, index: int, name: str) -> float | None:
    try:
        value = values[index]
    except (TypeError, IndexError) as exc:
        raise WeatherSourceError(f"Open-Meteo response is missing {name} data") from exc
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise WeatherSourceError(f"Open-Meteo returned invalid {name}")
    return float(value)


def historical_wind(
    latitude: float,
    longitude: float,
    event_time_utc: datetime,
    json_getter: Callable[[str], Mapping[str, Any]] = _get_json,
) -> WeatherObservation:
    """Get wind for the event's UTC hour; ERA5 is contextual reanalysis."""
    for name, value, low, high in (
        ("latitude", latitude, -90, 90),
        ("longitude", longitude, -180, 180),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be between {low} and {high}")
    if event_time_utc.tzinfo is None or event_time_utc.utcoffset() is None:
        raise ValueError("event_time_utc must be timezone-aware")
    event_time = event_time_utc.astimezone(timezone.utc)
    query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": event_time.date().isoformat(),
            "end_date": event_time.date().isoformat(),
            "hourly": "wind_speed_10m,wind_direction_10m",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "models": MODEL,
        }
    )
    response = json_getter(f"{ARCHIVE_ENDPOINT}?{query}")
    hourly = response.get("hourly")
    if not isinstance(hourly, Mapping):
        raise WeatherSourceError("Open-Meteo response does not include hourly data")
    times = hourly.get("time")
    if not isinstance(times, list):
        raise WeatherSourceError("Open-Meteo response does not include hourly timestamps")
    target_hour = event_time.replace(minute=0, second=0, microsecond=0)
    target_text = target_hour.strftime("%Y-%m-%dT%H:%M")
    try:
        index = times.index(target_text)
    except ValueError:
        speed = direction = None
    else:
        speed = _optional_number(hourly.get("wind_speed_10m"), index, "wind_speed_10m")
        direction = _optional_number(hourly.get("wind_direction_10m"), index, "wind_direction_10m")

    return WeatherObservation(
        observed_at_utc=target_hour,
        latitude=latitude,
        longitude=longitude,
        wind_speed_m_s=speed,
        wind_direction_degrees=direction,
        source="OPEN_METEO_ERA5_REANALYSIS",
        source_version="open-meteo-archive:era5",
    )
