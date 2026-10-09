"""NASA FIRMS standard-processing area API client and row normalizer."""

from __future__ import annotations

from datetime import date, timedelta
from datetime import datetime
from dataclasses import asdict, replace
import hashlib
import json
import re
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.common.models import FireObservation
from backend.ingestion.errors import IngestionRecordError
from backend.ingestion.firms import iter_firms_csv
from backend.processing.spatial import GridSpec


ENDPOINT = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
ALLOWED_SOURCES = frozenset({"VIIRS_SNPP_SP", "VIIRS_NOAA20_SP", "VIIRS_NOAA21_SP", "MODIS_SP"})
_MAP_KEY = re.compile(r"^[A-Fa-f0-9]{32}$")
_BBOX_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$")


class FirmsApiError(RuntimeError):
    """Sanitized FIRMS API failure; messages never contain request URLs or MAP_KEY."""


def fetch_standard_processing(
    map_key: str,
    start_date: date,
    end_date: date,
    *,
    source: str = "VIIRS_SNPP_SP",
    bbox: str = "73.75,28.5,78,33",
    grid: GridSpec | None = None,
    opener: Callable[..., Any] = urlopen,
    timeout_seconds: float = 20,
    maximum_response_bytes: int = 5_000_000,
) -> list[FireObservation]:
    """Fetch a bounded, date-addressable CSV window and normalize every row."""
    if not isinstance(map_key, str) or not _MAP_KEY.fullmatch(map_key):
        raise ValueError("FIRMS MAP_KEY is missing or malformed")
    if source not in ALLOWED_SOURCES:
        raise ValueError("source must be a supported standard-processing FIRMS product")
    if not isinstance(start_date, date) or isinstance(start_date, datetime) or not isinstance(end_date, date) or isinstance(end_date, datetime) or start_date > end_date:
        raise ValueError("date range is invalid")
    day_count = (end_date - start_date).days + 1
    if day_count > 5:
        raise ValueError("FIRMS area requests are limited to five days")
    if not _BBOX_PATTERN.fullmatch(bbox):
        raise ValueError("bbox must contain west,south,east,north numeric coordinates")
    west, south, east, north = (float(part) for part in bbox.split(","))
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise ValueError("bbox coordinates are outside valid ranges")
    if timeout_seconds <= 0 or maximum_response_bytes <= 0:
        raise ValueError("response limits must be positive")

    records: list[FireObservation] = []
    current = start_date
    grid_spec = grid or GridSpec()
    while current <= end_date:
        remaining = min(5, (end_date - current).days + 1)
        # The key is required by NASA's API path contract; never log this URL.
        url = "/".join((ENDPOINT, quote(map_key, safe=""), source, quote(bbox, safe=","), str(remaining), current.isoformat()))
        request = Request(url, headers={"Accept": "text/csv", "User-Agent": "BurnBlind/0.1"})
        try:
            with opener(request, timeout=timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise FirmsApiError(f"NASA FIRMS API returned HTTP {status}")
                content = response.read(maximum_response_bytes + 1)
        except FirmsApiError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise FirmsApiError(f"NASA FIRMS request failed ({type(exc).__name__})") from None
        if len(content) > maximum_response_bytes:
            raise FirmsApiError("NASA FIRMS response exceeded the configured size limit")
        text = content.decode("utf-8-sig")
        records.extend(_parse_csv(text, current, remaining, grid_spec))
        current += timedelta(days=remaining)
    return records


def _parse_csv(text: str, requested_date: date, day_count: int, grid: GridSpec) -> Iterable[FireObservation]:
    import tempfile

    # Reuse the canonical file normalizer without duplicating its CSV contract.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".csv", newline="") as temp:
        temp.write(text)
        temp.flush()
        normalized = list(iter_firms_csv(temp.name, grid.cell_id))
    finish = requested_date + timedelta(days=day_count)
    for row in normalized:
        if not requested_date <= row.observed_at_utc.date() < finish:
            raise IngestionRecordError("FIRMS row falls outside the requested date range")
        identity = asdict(row)
        identity.pop("fire_id", None)
        stable_id = "firms_" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"), default=lambda value: value.isoformat() if isinstance(value, (date, datetime)) else str(value)).encode()).hexdigest()[:32]
        yield replace(row, fire_id=stable_id)
