"""Build reproducible grid/season/hour summaries from normalized GK2A data."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.common.serialization import fire_observation_from_dict
from backend.ingestion.historical_context import summarize_detections
from backend.ingestion.gk2a_historical import SOURCE_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data/processed/gk2a")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/gk2a/manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/gk2a/historical_context.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("dataset_version") != "v1" or manifest.get("record_id") != "20084790":
        parser.error("manifest must identify the pinned Zenodo 20084790 v1 release")

    files = sorted(args.input_dir.glob("GK2-AMI_FireHotspotsData_*.jsonl"))
    if len(files) != 14:
        parser.error(f"expected 14 normalized source files, found {len(files)}")

    def records():
        for path in files:
            with path.open(encoding="utf-8") as source:
                for line_number, line in enumerate(source, start=1):
                    try:
                        record = fire_observation_from_dict(json.loads(line))
                    except (json.JSONDecodeError, ValueError) as exc:
                        raise ValueError(f"{path}:{line_number}: invalid normalized record: {exc}") from exc
                    if record.source_version != SOURCE_VERSION:
                        raise ValueError(f"{path}:{line_number}: unexpected source version {record.source_version}")
                    yield record

    summary = summarize_detections(records())
    summary["dataset"] = "GK2-AMI hourly fire/hot-smoke detection dataset"
    summary["record_id"] = manifest["record_id"]
    summary["doi"] = manifest["doi"]
    summary["dataset_version"] = manifest["dataset_version"]
    summary["license"] = manifest.get("license", "CC BY 4.0")
    summary["generated_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as temp:
        temporary_path = Path(temp.name)
        try:
            json.dump(summary, temp, indent=2, sort_keys=True, allow_nan=False)
            temp.write("\n")
            temp.flush()
            temporary_path.replace(args.output)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    print(f"summarized {summary['total_detections']} source detections -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
