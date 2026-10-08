"""Build deterministic historical candidate-event clusters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.common.serialization import candidate_event_to_dict, fire_observation_from_dict
from backend.ingestion.gk2a_historical import SOURCE_VERSION
from backend.processing.events import build_candidate_events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data/processed/gk2a")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/gk2a/candidate_events.jsonl")
    parser.add_argument("--max-time-delta-hours", type=float, default=3.0)
    args = parser.parse_args()
    files = sorted(args.input_dir.glob("GK2-AMI_FireHotspotsData_*.jsonl"))
    if len(files) != 14:
        parser.error(f"expected 14 normalized GK2A files, found {len(files)}")

    records = []
    for path in files:
        with path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                try:
                    record = fire_observation_from_dict(json.loads(line))
                except (json.JSONDecodeError, ValueError) as exc:
                    parser.error(f"{path}:{line_number}: invalid record: {exc}")
                if record.source_version != SOURCE_VERSION:
                    parser.error(f"{path}:{line_number}: unexpected source version {record.source_version}")
                records.append(record)

    events = build_candidate_events(records, args.max_time_delta_hours)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as temp:
        temporary_path = Path(temp.name)
        try:
            for event in events:
                temp.write(json.dumps(candidate_event_to_dict(event), separators=(",", ":")) + "\n")
            temp.flush()
            temporary_path.replace(args.output)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    print(f"built {len(events)} historical candidate clusters from {len(records)} detections -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
