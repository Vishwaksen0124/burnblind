"""Load the small, explicitly historical replay sample into the Events table."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.common.serialization import candidate_event_to_dict, fire_observation_from_dict
from backend.processing.events import build_candidate_events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=ROOT / "data/sample/gk2a_historical_2025.jsonl")
    parser.add_argument("--table", default=os.environ.get("EVENT_TABLE"))
    args = parser.parse_args()
    if not args.table:
        parser.error("set EVENT_TABLE or pass --table")
    if not args.sample.is_file():
        parser.error(f"replay sample not found: {args.sample}; run the documented sample workflow first")

    records = []
    with args.sample.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            try:
                records.append(fire_observation_from_dict(json.loads(line)))
            except (json.JSONDecodeError, ValueError) as exc:
                parser.error(f"{args.sample}:{line_number}: invalid sample record: {exc}")
    events = build_candidate_events(records)

    import boto3

    table = boto3.resource("dynamodb").Table(args.table)
    with table.batch_writer(overwrite_by_pkeys=["event_id"]) as batch:
        for event in events:
            item = candidate_event_to_dict(event)
            item["latitude"] = Decimal(str(item["latitude"]))
            item["longitude"] = Decimal(str(item["longitude"]))
            batch.put_item(Item=item)
    print(f"seeded {len(events)} HISTORICAL_REPLAY candidate clusters into {args.table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
