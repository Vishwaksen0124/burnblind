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

from backend.common.serialization import candidate_event_to_dict, fire_observation_from_dict, fire_observation_to_dict
from backend.processing.events import build_candidate_events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=ROOT / "data/sample/gk2a_historical_2025.jsonl")
    parser.add_argument("--table", default=os.environ.get("EVENT_TABLE"))
    parser.add_argument("--evidence-table", default=os.environ.get("EVIDENCE_TABLE"))
    args = parser.parse_args()
    if not args.table:
        parser.error("set EVENT_TABLE or pass --table")
    if not args.evidence_table:
        parser.error("set EVIDENCE_TABLE or pass --evidence-table")
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

    dynamodb = boto3.resource("dynamodb")
    event_table = dynamodb.Table(args.table)
    evidence_table = dynamodb.Table(args.evidence_table)
    event_by_observation = {
        evidence_id: event.event_id
        for event in events
        for evidence_id in event.evidence_ids
    }
    with event_table.batch_writer(overwrite_by_pkeys=["event_id"]) as batch:
        for event in events:
            batch.put_item(Item=_to_dynamo(candidate_event_to_dict(event)))
    with evidence_table.batch_writer(overwrite_by_pkeys=["observation_id"]) as batch:
        for record in records:
            batch.put_item(Item=_to_dynamo({
                "observation_id": record.fire_id,
                "event_id": event_by_observation[record.fire_id],
                **fire_observation_to_dict(record),
            }))
    print(
        f"seeded {len(events)} HISTORICAL_REPLAY candidate clusters and "
        f"{len(records)} source observations"
    )
    return 0


def _to_dynamo(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_dynamo(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_to_dynamo(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
