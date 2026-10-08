"""Normalize the published Zenodo GK2A hotspot text files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Callable, Iterator
from zoneinfo import ZoneInfo

from backend.common.models import FireObservation
from backend.ingestion.errors import IngestionRecordError as DatasetRecordError


SOURCE_VERSION = "zenodo:20084790:v1"
SOURCE_TIMEZONE = ZoneInfo("Asia/Kolkata")
_FORMAT = re.compile(r"^\s*FORMAT\s*:", re.IGNORECASE)
_SOURCE_FILE = re.compile(
    r"^GK2-AMI_FireHotspotsData_(2019|202[0-5])_10-11_(Punjab|Haryana)_India_v1\.txt$"
)
_FORMAT_FIELD = re.compile(r"(\d+)\s*=\s*(.*?)(?=\s+\d+\s*=|$)")
_EXPECTED_FIELDS = (
    "year",
    "month",
    "date",
    "hour",
    "minutes",
    "longitude (deg.)",
    "latitude (deg.)",
    "brightness temperature difference ref.",
    "brightness temperature [0.38 micron]",
    "brightness temperature [11.2 micron]",
    "confidence_flag",
)
_STUDY_BOUNDS = (73.0, 27.0, 78.0, 33.0)  # west, south, east, north


def _validate_source_metadata(path: Path, metadata: dict[str, str]) -> tuple[int, str]:
    match = _SOURCE_FILE.fullmatch(path.name)
    if not match:
        raise DatasetRecordError(f"{path}: filename is not a supported pinned GK2A release file")
    expected_year, expected_region = int(match.group(1)), match.group(2)
    if metadata.get("FILE_NAME") != path.name:
        raise DatasetRecordError(f"{path}: embedded FILE_NAME does not match the source filename")
    if metadata.get("YEAR") != str(expected_year):
        raise DatasetRecordError(f"{path}: embedded YEAR does not match the source filename")
    if expected_region.casefold() not in metadata.get("REGION", "").casefold():
        raise DatasetRecordError(f"{path}: embedded REGION does not match the source filename")
    months = metadata.get("MONTHS", "").casefold()
    if "october" not in months or "november" not in months:
        raise DatasetRecordError(f"{path}: expected October and November coverage metadata")
    if metadata.get("SATELLITE") != "GEOKOMPSAT-2A":
        raise DatasetRecordError(f"{path}: unexpected satellite metadata")
    if "advanced meteorological imager" not in metadata.get("SENSOR", "").casefold():
        raise DatasetRecordError(f"{path}: unexpected sensor metadata")
    return expected_year, expected_region


def iter_gk2a_hotspots(
    path: str | Path,
    cell_id: Callable[[float, float], str],
) -> Iterator[FireObservation]:
    """Yield canonical detections from one publisher-format `.txt` file.

    The source encodes time in India Standard Time. We preserve its measured
    brightness temperatures and confidence flag as source fields; confidence
    is deliberately not converted into a normalized score.
    """
    source_path = Path(path)
    saw_format = False
    metadata: dict[str, str] = {}
    expected_year = None
    with source_path.open("r", encoding="utf-8-sig") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if _FORMAT.match(line):
                if saw_format:
                    raise DatasetRecordError(f"{source_path}:{line_number}: duplicate FORMAT declaration")
                body = line.split(":", 1)[1]
                # Parse positions separately so descriptions containing numbers
                # (e.g. 0.38 and 11.2 micron) are not mistaken for field indices.
                indexed_fields = [
                    (int(index), label.strip().casefold())
                    for index, label in _FORMAT_FIELD.findall(body)
                ]
                if [label for _, label in sorted(indexed_fields)] != list(_EXPECTED_FIELDS) or [
                    index for index, _ in sorted(indexed_fields)
                ] != list(range(1, 12)):
                    raise DatasetRecordError(
                        f"{source_path}:{line_number}: unsupported publisher FORMAT declaration"
                    )
                expected_year, _ = _validate_source_metadata(source_path, metadata)
                saw_format = True
                continue
            if not saw_format:
                key, separator, value = line.partition("=")
                if separator:
                    metadata[key.strip()] = value.strip()
                continue  # publisher metadata before the tabular format line

            fields = line.split()
            if len(fields) != 11:
                raise DatasetRecordError(
                    f"{source_path}:{line_number}: expected 11 fields after FORMAT, got {len(fields)}"
                )
            try:
                year, month, day, hour, minute = map(int, fields[:5])
                longitude, latitude = map(float, fields[5:7])
                if year != expected_year or month not in (10, 11):
                    raise ValueError("record date does not match declared release coverage")
                west, south, east, north = _STUDY_BOUNDS
                if not west <= longitude <= east or not south <= latitude <= north:
                    raise ValueError("coordinates fall outside the Punjab/Haryana study envelope")
                brightness_difference = float(fields[7])
                brightness_038 = float(fields[8])
                brightness_112 = float(fields[9])
                confidence_flag = int(fields[10])
                observed_at = datetime(
                    year, month, day, hour, minute, tzinfo=SOURCE_TIMEZONE
                )
            except (ValueError, OverflowError) as exc:
                raise DatasetRecordError(f"{source_path}:{line_number}: invalid record: {exc}") from exc

            try:
                grid_id = cell_id(latitude, longitude)
                yield FireObservation(
                    fire_id=f"{source_path.stem}:{line_number}",
                    source="GK2A_AMI",
                    observed_at_utc=observed_at,
                    latitude=latitude,
                    longitude=longitude,
                    grid_id=grid_id,
                    confidence=None,
                    source_version=SOURCE_VERSION,
                    brightness_temperature_difference_ref=brightness_difference,
                    brightness_temperature_038_micron_k=brightness_038,
                    brightness_temperature_112_micron_k=brightness_112,
                    confidence_flag=confidence_flag,
                )
            except (TypeError, ValueError) as exc:
                raise DatasetRecordError(f"{source_path}:{line_number}: invalid normalized record: {exc}") from exc

    if not saw_format:
        raise DatasetRecordError(f"{source_path}: missing publisher FORMAT declaration")
