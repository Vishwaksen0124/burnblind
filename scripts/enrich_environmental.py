"""Bounded source-based event enrichment; never calls the investigation agent.

Examples:
  python scripts/enrich_environmental.py --event-id evt_... --region ap-south-1
  python scripts/enrich_environmental.py --limit 5 --region ap-south-1
    python scripts/enrich_environmental.py --all --region ap-south-1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from backend.agent.evidence import DynamoEvidenceRepository
from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.features.environmental import EnvironmentalAnalysisService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True, help="AWS region containing the replay tables")
    parser.add_argument("--event-id", help="Enrich exactly one event")
    parser.add_argument("--all", action="store_true", help="Process every event in the table")
    parser.add_argument("--limit", type=int, default=1, help="Maximum events to process (default: 1; max: 100)")
    parser.add_argument("--pause-seconds", type=float, default=1.0, help="Delay between events for provider rate control")
    args = parser.parse_args()
    if args.event_id and args.all:
        parser.error("choose --event-id or --all, not both")
    if not args.event_id and not args.all and not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    if args.pause_seconds < 0:
        parser.error("--pause-seconds cannot be negative")

    event_table = os.environ.get("EVENT_TABLE")
    evidence_table = os.environ.get("EVIDENCE_TABLE")
    if not event_table or not evidence_table:
        parser.error("Set EVENT_TABLE and EVIDENCE_TABLE to the target replay tables")

    import boto3

    dynamodb = boto3.resource("dynamodb", region_name=args.region)
    events = DynamoCandidateEventRepository(event_table, dynamodb.Table(event_table))
    evidence = DynamoEvidenceRepository(evidence_table, dynamodb.Table(evidence_table))
    selected = [events.get(args.event_id)] if args.event_id else events.all()
    if not args.all and not args.event_id:
        selected = selected[:args.limit]
    selected = [event for event in selected if event is not None]
    if not selected:
        print(json.dumps({"processed": 0, "reason": "No matching events."}))
        return 0

    service = EnvironmentalAnalysisService(events, evidence)
    counts = {"COMPLETE": 0, "PARTIAL": 0, "NOT_FOUND": 0, "ERROR": 0}
    for index, event in enumerate(selected):
        try:
            result = service.analyze(event.event_id)
            status = result.get("environmental_analysis", {}).get("status", result.get("status", "ERROR"))
            counts[status if status in counts else "ERROR"] += 1
            exposure = result.get("exposure", {})
            print(json.dumps({
                "event_id": event.event_id,
                "status": status,
                "weather": result.get("environmental_analysis", {}).get("weather", {}).get("status"),
                "exposure": exposure.get("status"),
                "population_estimate": exposure.get("population_estimate"),
                "sensor_comparison": result.get("sensor_comparison", {}).get("status"),
                "blind_spot": result.get("blind_spot", {}).get("status"),
            }, separators=(",", ":")))
        except Exception as exc:
            counts["ERROR"] += 1
            print(json.dumps({"event_id": event.event_id, "status": "ERROR", "error": type(exc).__name__}), file=sys.stderr)
        if index + 1 < len(selected) and args.pause_seconds:
            time.sleep(args.pause_seconds)
    print(json.dumps({"processed": len(selected), "counts": counts}, separators=(",", ":")))
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
