"""Normalize NASA FIRMS standard-processing VIIRS or MODIS CSV records."""

from __future__ import annotations

import csv
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Callable, Iterator

from backend.common.models import FireObservation
from backend.ingestion.errors import IngestionRecordError


_REQUIRED_COLUMNS = {
    "latitude", "longitude", "acq_date", "acq_time", "satellite",
    "instrument", "confidence", "version",
}


def _optional_float(row: dict[str, str], *names: str) -> float | None:
    for name in names:
        value = row.get(name, "").strip()
        if value:
            try:
                return float(value)
            except ValueError as exc:
                raise ValueError(f"invalid numeric field {name}={value!r}") from exc
    return None


def iter_firms_csv(
    path: str | Path,
    cell_id: Callable[[float, float], str],
) -> Iterator[FireObservation]:
    """Yield validated FIRMS records; acquisition dates and times are UTC."""
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise IngestionRecordError(f"{source_path}: missing CSV header")
        fieldnames = {name.strip().casefold() for name in reader.fieldnames if name}
        missing = _REQUIRED_COLUMNS - fieldnames
        if missing:
            raise IngestionRecordError(f"{source_path}: missing FIRMS columns: {', '.join(sorted(missing))}")
        if not ({"bright_ti4", "brightness"} & fieldnames):
            raise IngestionRecordError(f"{source_path}: expected VIIRS bright_ti4 or MODIS brightness column")

        for row_number, original_row in enumerate(reader, start=2):
            row = {(key or "").strip().casefold(): (value or "").strip() for key, value in original_row.items()}
            try:
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])
                acquisition_date = date.fromisoformat(row["acq_date"])
                acquisition_time = row["acq_time"].zfill(4)
                if len(acquisition_time) != 4 or not acquisition_time.isdigit():
                    raise ValueError("acq_time must be an integer in HHMM format")
                hour, minute = int(acquisition_time[:2]), int(acquisition_time[2:])
                observed_at = datetime.combine(acquisition_date, time(hour, minute), tzinfo=timezone.utc)
                version = row["version"]
                instrument = row["instrument"]
                satellite = row["satellite"]
                raw_confidence = row["confidence"]
                if not all((version, instrument, satellite)):
                    raise ValueError("version, instrument, and satellite are required")

                if row.get("bright_ti4", ""):
                    primary_name, primary = "bright_ti4", float(row["bright_ti4"])
                    secondary_name = "bright_ti5" if row.get("bright_ti5", "") else None
                    secondary = _optional_float(row, "bright_ti5")
                else:
                    primary_name, primary = "brightness", float(row["brightness"])
                    secondary_name = "bright_t31" if row.get("bright_t31", "") else None
                    secondary = _optional_float(row, "bright_t31")

                grid = cell_id(latitude, longitude)
                yield FireObservation(
                    fire_id=f"{source_path.stem}:{row_number}",
                    source="NASA_FIRMS",
                    observed_at_utc=observed_at,
                    latitude=latitude,
                    longitude=longitude,
                    grid_id=grid,
                    confidence=None,
                    source_version=f"firms:{version}",
                    source_confidence=raw_confidence or None,
                    brightness_temperature_channel_1_k=primary,
                    brightness_temperature_channel_2_k=secondary,
                    channel_1_name=primary_name,
                    channel_2_name=secondary_name,
                    frp_mw=_optional_float(row, "frp"),
                    scan_size_km=_optional_float(row, "scan"),
                    track_size_km=_optional_float(row, "track"),
                    satellite=satellite,
                    instrument=instrument,
                    daynight=row.get("daynight") or None,
                )
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                raise IngestionRecordError(f"{source_path}:{row_number}: invalid FIRMS record: {exc}") from exc
