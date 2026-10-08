"""Normalize locally acquired, checksum-verified FIRMS CSV files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ingestion.firms import iter_firms_csv
from backend.ingestion.normalization import write_fire_observations
from backend.processing.spatial import GridSpec


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/firms/manifest.json")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/firms")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/firms")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = [
        entry
        for product in manifest.get("products", {}).values()
        for entry in product.values()
        if isinstance(entry, dict) and "file_name" in entry
    ]
    if not entries:
        parser.error("manifest contains no downloaded FIRMS CSV files")

    grid = GridSpec()
    total = 0
    for entry in sorted(entries, key=lambda item: item["file_name"]):
        source = args.raw_dir / entry["file_name"]
        if not source.is_file() or sha256(source) != entry.get("sha256"):
            parser.error(f"missing file or SHA-256 mismatch: {source}")
        output = args.output_dir / f"{source.stem}.jsonl"
        count = write_fire_observations(iter_firms_csv(source, grid.cell_id), output)
        total += count
        print(f"normalized {source.name}: {count} records")
    print(f"normalized {total} FIRMS records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
