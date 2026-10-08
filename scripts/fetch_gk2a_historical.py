"""Download the pinned GK2A historical dataset and verify every file checksum."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
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

RECORD_ID = "20084790"
RECORD_URL = f"https://zenodo.org/api/records/{RECORD_ID}"
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "gk2a"
FILENAME = re.compile(r"^GK2-AMI_FireHotspotsData_(2019|202[0-5])_10-11_(Punjab|Haryana)_India_v1\.txt$")


def _read_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "BurnBlind/0.1 dataset-acquisition"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def _download_verified(file_record: dict, destination: Path) -> dict:
    name = file_record["key"]
    expected_size = int(file_record["size"])
    checksum = file_record.get("checksum", "")
    algorithm, separator, expected_digest = checksum.partition(":")
    if not separator or algorithm not in {"md5", "sha256"}:
        raise ValueError(f"Unsupported or missing checksum for {name}: {checksum!r}")

    def valid_existing_file() -> bool:
        if not destination.is_file() or destination.stat().st_size != expected_size:
            return False
        existing_digest = hashlib.new(algorithm)
        with destination.open("rb") as existing:
            for chunk in iter(lambda: existing.read(1024 * 1024), b""):
                existing_digest.update(chunk)
        return existing_digest.hexdigest().lower() == expected_digest.lower()

    if valid_existing_file():
        digest_value = hashlib.new(algorithm)
        with destination.open("rb") as existing:
            for chunk in iter(lambda: existing.read(1024 * 1024), b""):
                digest_value.update(chunk)
        return {
            "file_name": name,
            "file_size_bytes": expected_size,
            "checksum": f"{algorithm}:{digest_value.hexdigest()}",
            "source_url": file_record.get("links", {}).get("self", ""),
            "downloaded_at_utc": datetime.fromtimestamp(destination.stat().st_mtime, timezone.utc).isoformat(),
        }

    links = file_record.get("links", {})
    # Zenodo's current record API exposes the content endpoint as `self`.
    # Older responses used a separate `content` link.
    content_url = links.get("content") or links.get("self")
    if not content_url:
        raise ValueError(f"Zenodo API did not provide a content URL for {name}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(content_url, headers={"User-Agent": "BurnBlind/0.1 dataset-acquisition"})
    last_error: Exception | None = None
    for attempt in range(3):
        digest = hashlib.new(algorithm)
        byte_count = 0
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
            temporary_path = Path(temp.name)
            try:
                with urlopen(request, timeout=90) as response:
                    while chunk := response.read(1024 * 1024):
                        temp.write(chunk)
                        digest.update(chunk)
                        byte_count += len(chunk)
                if byte_count != expected_size:
                    raise ValueError(f"Size mismatch for {name}: expected {expected_size}, received {byte_count}")
                actual_digest = digest.hexdigest()
                if actual_digest.lower() != expected_digest.lower():
                    raise ValueError(f"Checksum mismatch for {name}: expected {expected_digest}, received {actual_digest}")
                os.replace(temporary_path, destination)
                last_error = None
                break
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                temporary_path.unlink(missing_ok=True)
                last_error = exc
                if attempt < 2:
                    time.sleep(attempt + 1)
    if last_error is not None:
        raise last_error

    return {
        "file_name": name,
        "file_size_bytes": byte_count,
        "checksum": f"{algorithm}:{digest.hexdigest()}",
        "source_url": content_url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, action="append", help="Limit to one or more years (2019–2025); defaults to all years")
    parser.add_argument("--output", type=Path, default=DATA_DIR, help="Directory for downloaded source files")
    args = parser.parse_args()
    requested_years = set(args.year or range(2019, 2026))
    if not requested_years or any(year < 2019 or year > 2025 for year in requested_years):
        parser.error("--year must be between 2019 and 2025")

    try:
        record = _read_json(RECORD_URL)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"Unable to read pinned Zenodo record {RECORD_ID}: {exc}", file=sys.stderr)
        return 2

    metadata = record.get("metadata", {})
    version = metadata.get("version")
    if version != "v1":
        print(f"Expected Zenodo dataset version v1, received {version!r}; refusing an unreviewed version", file=sys.stderr)
        return 2
    license_id = (metadata.get("license") or {}).get("id")
    if license_id != "cc-by-4.0":
        print(f"Expected CC BY 4.0 license metadata, received {license_id!r}", file=sys.stderr)
        return 2

    selected = [
        item for item in record.get("files", [])
        if FILENAME.fullmatch(item.get("key", ""))
        and int(FILENAME.fullmatch(item["key"]).group(1)) in requested_years
    ]
    expected_count = len(requested_years) * 2
    if len(selected) != expected_count:
        print(f"Expected {expected_count} Punjab/Haryana files; Zenodo returned {len(selected)}", file=sys.stderr)
        return 2

    manifest = {
        "dataset": "gk2a_historical_fire_hotspots",
        "record_id": RECORD_ID,
        "doi": "10.5281/zenodo.20084790",
        "source_url": f"https://zenodo.org/records/{RECORD_ID}",
        "dataset_version": version,
        "license": "CC BY 4.0",
        "coverage": "Punjab and Haryana, India; October–November; selected years",
        "files": [],
    }
    try:
        for item in sorted(selected, key=lambda entry: entry["key"]):
            record_entry = _download_verified(item, args.output / item["key"])
            manifest["files"].append(record_entry)
            print(f"verified {record_entry['file_name']} ({record_entry['file_size_bytes']} bytes)")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        print(f"Dataset acquisition stopped: {exc}", file=sys.stderr)
        return 2

    manifest["downloaded_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"provenance manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
