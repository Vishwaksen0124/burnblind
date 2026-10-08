"""Normalize every source file recorded in the verified Zenodo manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.normalize_gk2a import normalize_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/gk2a/manifest.json")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/gk2a")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/gk2a")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("record_id") != "20084790" or manifest.get("dataset_version") != "v1":
        parser.error("manifest must identify the pinned Zenodo 20084790 v1 release")
    files = manifest.get("files", [])
    if len(files) != 14:
        parser.error(f"expected all 14 Punjab/Haryana year files, found {len(files)}")

    total = 0
    for item in sorted(files, key=lambda entry: entry["file_name"]):
        source = args.raw_dir / item["file_name"]
        destination = args.output_dir / f"{source.stem}.jsonl"
        count = normalize_file(source, destination)
        total += count
        print(f"normalized {source.name}: {count} records")
    print(f"normalized {total} records across {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
