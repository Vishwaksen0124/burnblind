"""Deterministic counts over historical source detections.

Counts describe records in the GK2A-derived dataset. They are not unique fires
or ground-truth labels.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Iterable
from zoneinfo import ZoneInfo

from backend.common.models import FireObservation


IST = ZoneInfo("Asia/Kolkata")


def summarize_detections(records: Iterable[FireObservation]) -> dict:
    total = 0
    by_grid: Counter[str] = Counter()
    by_year: Counter[int] = Counter()
    by_month: Counter[int] = Counter()
    by_local_hour: Counter[int] = Counter()
    by_grid_month: dict[str, Counter[int]] = defaultdict(Counter)
    by_grid_year: dict[str, Counter[int]] = defaultdict(Counter)
    by_grid_year_month: dict[str, dict[int, Counter[int]]] = defaultdict(lambda: defaultdict(Counter))
    by_grid_hour: dict[str, Counter[str]] = defaultdict(Counter)

    for record in records:
        total += 1
        local_time = record.observed_at_utc.astimezone(IST)
        by_grid[record.grid_id] += 1
        by_year[local_time.year] += 1
        by_month[local_time.month] += 1
        by_local_hour[local_time.hour] += 1
        by_grid_month[record.grid_id][local_time.month] += 1
        by_grid_year[record.grid_id][local_time.year] += 1
        by_grid_year_month[record.grid_id][local_time.year][local_time.month] += 1
        hour_bucket = local_time.replace(minute=0, second=0, microsecond=0).isoformat()
        by_grid_hour[record.grid_id][hour_bucket] += 1

    return {
        "record_type": "source_detection_counts",
        "count_semantics": "GK2A dataset detection records; not unique fires or ground truth",
        "timezone_for_temporal_groups": "Asia/Kolkata",
        "total_detections": total,
        "by_grid": dict(sorted(by_grid.items())),
        "by_year": {str(key): by_year[key] for key in sorted(by_year)},
        "by_month_ist": {str(key): by_month[key] for key in sorted(by_month)},
        "by_hour_ist": {str(key): by_local_hour[key] for key in sorted(by_local_hour)},
        "by_grid_month_ist": {
            grid: {str(month): count for month, count in sorted(counts.items())}
            for grid, counts in sorted(by_grid_month.items())
        },
        "by_grid_year": {
            grid: {str(year): count for year, count in sorted(counts.items())}
            for grid, counts in sorted(by_grid_year.items())
        },
        "by_grid_year_month": {
            grid: {
                str(year): {str(month): count for month, count in sorted(months.items())}
                for year, months in sorted(years.items())
            }
            for grid, years in sorted(by_grid_year_month.items())
        },
        "by_grid_hour_ist": {
            grid: dict(sorted(counts.items())) for grid, counts in sorted(by_grid_hour.items())
        },
    }


def query_historical_context(
    summary: dict,
    grid_id: str,
    as_of_utc: datetime,
) -> dict:
    """Return historical detections without including records after `as_of`.

    Month-to-month context uses only complete earlier years. A time-bucket
    count provides same-grid observations available up to the requested time.
    """
    if as_of_utc.tzinfo is None or as_of_utc.utcoffset() is None:
        raise ValueError("as_of_utc must be timezone-aware")
    as_of_local = as_of_utc.astimezone(IST)
    year_month = summary.get("by_grid_year_month", {}).get(grid_id, {})
    prior_year_month_count = sum(
        int(months.get(str(as_of_local.month), 0))
        for year, months in year_month.items()
        if int(year) < as_of_local.year
    )
    prior_complete_year_count = sum(
        int(count)
        for year, count in summary.get("by_grid_year", {}).get(grid_id, {}).items()
        if int(year) < as_of_local.year
    )
    cutoff_hour = as_of_local.replace(minute=0, second=0, microsecond=0).isoformat()
    through_time_count = sum(
        int(count)
        for bucket, count in summary.get("by_grid_hour_ist", {}).get(grid_id, {}).items()
        if datetime.fromisoformat(bucket) <= datetime.fromisoformat(cutoff_hour)
    )
    return {
        "grid_id": grid_id,
        "as_of_utc": as_of_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "historical_detections_through_as_of_hour": through_time_count,
        "historical_detections_in_same_month_prior_years": prior_year_month_count,
        "historical_detections_in_complete_prior_years": prior_complete_year_count,
        "source": "GK2A dataset detection counts; not unique fires or ground truth",
        "source_version": "zenodo:20084790:v1",
    }
