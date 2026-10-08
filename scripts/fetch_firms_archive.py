"""Fetch standard-processing FIRMS detections for the MVP fire seasons.

The FIRMS MAP_KEY is read only from the FIRMS_MAP_KEY environment variable.
It is never printed or written into the provenance manifest.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data/raw/firms"
MANIFEST_NAME = "manifest.json"
ALLOWED_SOURCES = ("MODIS_SP", "VIIRS_SNPP_SP", "VIIRS_NOAA20_SP")
AREA = "73,27,78,33"  # west,south,east,north; Punjab/Haryana screening envelope
API_TEMPLATE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/{source}/{area}/{days}/{start_date}"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _windows(year: int):
    current = date(year, 10, 1)
    end = date(year, 12, 1)
    while current < end:
        days = min(5, (end - current).days)
        yield current, days
        current += timedelta(days=days)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_existing(path: Path, manifest_entry: dict | None) -> bool:
    if not path.is_file() or not manifest_entry:
        return False
    if path.stat().st_size != manifest_entry.get("file_size_bytes"):
        return False
    expected = manifest_entry.get("sha256", "")
    return bool(_SHA256.fullmatch(expected)) and _sha256(path) == expected


def _fetch_csv(url: str, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temp:
                temporary_path = Path(temp.name)
                try:
                    request = Request(url, headers={"User-Agent": "BurnBlind/0.1 FIRMS ingestion"})
                    with urlopen(request, timeout=90) as response:
                        header = response.readline()
                        header_text = header.decode("utf-8-sig", errors="replace").strip().casefold()
                        if "latitude" not in header_text or "longitude" not in header_text:
                            raise ValueError("FIRMS returned an error or unknown CSV schema")
                        temp.write(header)
                        while chunk := response.read(1024 * 1024):
                            temp.write(chunk)
                    temp.flush()
                    os.fsync(temp.fileno())
                    os.replace(temporary_path, output)
                    return {
                        "file_name": output.name,
                        "file_size_bytes": output.stat().st_size,
                        "sha256": _sha256(output),
                        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                    }
                except Exception:
                    temporary_path.unlink(missing_ok=True)
                    raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    raise RuntimeError(f"FIRMS archive request failed after retries: {type(last_error).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--source", choices=ALLOWED_SOURCES, action="append", help="Repeat to select products; defaults to all standard products")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    if args.start_year < 2000 or args.end_year > 2025 or args.start_year > args.end_year:
        parser.error("year range must be ordered and within 2000–2025")
    map_key = os.environ.get("FIRMS_MAP_KEY", "").strip()
    if not map_key:
        parser.error("set FIRMS_MAP_KEY in the environment; the key is never stored in the project")

    sources = args.source or list(ALLOWED_SOURCES)
    manifest_path = args.output_dir / MANIFEST_NAME
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "dataset": "NASA FIRMS standard-processing active-fire detections",
            "source_url": "https://firms.modaps.eosdis.nasa.gov/active_fire/",
            "api_url_template": API_TEMPLATE,
            "geographic_bbox_wsen": AREA,
            "years": [args.start_year, args.end_year],
            "products": {},
        }

    for source in sources:
        product = manifest["products"].setdefault(source, {})
        for year in range(args.start_year, args.end_year + 1):
            for start, days in _windows(year):
                filename = f"{source}_{start.isoformat()}_{days}d.csv"
                output = args.output_dir / filename
                existing = product.get(filename)
                if _valid_existing(output, existing):
                    print(f"verified existing {filename}")
                    continue
                url = (
                    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/"
                    f"{source}/{AREA}/{days}/{start.isoformat()}"
                )
                try:
                    details = _fetch_csv(url, output)
                except RuntimeError as exc:
                    print(f"{filename}: {exc}", file=sys.stderr)
                    return 2
                details.update({"source": source, "period_start": start.isoformat(), "day_count": days})
                product[filename] = details
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
                print(f"verified {filename} ({details['file_size_bytes']} bytes)")
    manifest["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"provenance manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
