"""Create a small, deterministic real-data development sample."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def evenly_spaced_indices(size: int, limit: int) -> list[int]:
    if size < 1 or limit < 1:
        raise ValueError("size and limit must be positive")
    if limit >= size:
        return list(range(size))
    if limit == 1:
        return [0]
    return [round(index * (size - 1) / (limit - 1)) for index in range(limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized-dir", type=Path, default=ROOT / "data/processed/gk2a")
    parser.add_argument("--raw-manifest", type=Path, default=ROOT / "data/raw/gk2a/manifest.json")
    parser.add_argument("--per-region", type=int, default=125)
    parser.add_argument("--output", type=Path, default=ROOT / "data/sample/gk2a_historical_2025.jsonl")
    args = parser.parse_args()
    if args.per_region < 1:
        parser.error("--per-region must be positive")

    source_manifest = json.loads(args.raw_manifest.read_text(encoding="utf-8"))
    selected_records = []
    source_files = []
    for region in ("Haryana", "Punjab"):
        filename = f"GK2-AMI_FireHotspotsData_2025_10-11_{region}_India_v1.txt"
        normalized_path = args.normalized_dir / f"{Path(filename).stem}.jsonl"
        source_entry = next((item for item in source_manifest["files"] if item["file_name"] == filename), None)
        if source_entry is None or source_manifest.get("dataset_version") != "v1":
            parser.error(f"source manifest does not contain the expected pinned file {filename}")
        lines = normalized_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            parser.error(f"normalized file is empty: {normalized_path}")
        indices = evenly_spaced_indices(len(lines), min(args.per_region, len(lines)))
        selected_records.extend(lines[index] for index in indices)
        source_files.append({
            "file_name": filename,
            "checksum": source_entry["checksum"],
            "selected_records": len(indices),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(selected_records) + "\n", encoding="utf-8")
    manifest = {
        "dataset": "BurnBlind GK2A historical development sample",
        "sample_type": "real source records; development/debug only; not a statistical sample",
        "sample_method": "evenly spaced source-row indices per 2025 region file",
        "source_record_id": source_manifest["record_id"],
        "source_doi": source_manifest["doi"],
        "source_version": source_manifest["dataset_version"],
        "license": source_manifest["license"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "record_count": len(selected_records),
        "source_files": source_files,
        "data_file": args.output.name,
    }
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"created {len(selected_records)} real source records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
