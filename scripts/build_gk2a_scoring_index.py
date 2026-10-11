"""Build the compact, temporal-safe GK2A index bundled with Lambda workers.

Run after normalizing all 14 pinned source files with `scripts/normalize_gk2a_release.py`.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.common.serialization import fire_observation_from_dict
from backend.ingestion.historical_context import summarize_detections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data/processed/gk2a")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/gk2a/manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/reference/gk2a_scoring_index_v1.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("dataset_version") != "v1" or manifest.get("record_id") != "20084790":
        parser.error("manifest must identify pinned Zenodo record 20084790 v1")
    files = sorted(args.input_dir.glob("GK2-AMI_FireHotspotsData_*.jsonl"))
    if len(files) != 14:
        parser.error(f"expected 14 normalized source files, found {len(files)}")

    def records():
        for path in files:
            with path.open(encoding="utf-8") as source:
                for line_number, line in enumerate(source, 1):
                    try:
                        row = fire_observation_from_dict(json.loads(line))
                    except (json.JSONDecodeError, ValueError) as exc:
                        raise ValueError(f"{path}:{line_number}: invalid source record: {exc}") from exc
                    if row.source_version != "zenodo:20084790:v1":
                        raise ValueError(f"{path}:{line_number}: source release mismatch")
                    yield row

    summary = summarize_detections(records())
    years = sorted(int(year) for year in summary["by_year"])
    payload = {
        "record_type": "gk2a_same_grid_month_index",
        "record_id": manifest["record_id"],
        "doi": manifest["doi"],
        "dataset_version": manifest["dataset_version"],
        "license": manifest.get("license", "CC BY 4.0"),
        "source_version": "zenodo:20084790:v1",
        "months": [10, 11],
        "complete_years": years,
        "count_semantics": "GK2A source detection records; not unique fires or ground truth",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "by_grid_year_month": summary["by_grid_year_month"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as target:
        temporary_path = Path(target.name)
        try:
            json.dump(payload, target, separators=(",", ":"), sort_keys=True, allow_nan=False)
            target.write("\n")
            target.flush()
            temporary_path.replace(args.output)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    print(json.dumps({
        "output": str(args.output),
        "grids": len(payload["by_grid_year_month"]),
        "source_detections": summary["total_detections"],
        "years": years,
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
