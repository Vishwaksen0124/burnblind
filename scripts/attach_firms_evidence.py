"""Attach matched NASA FIRMS observations to replay events in DynamoDB."""

from __future__ import annotations

import argparse
from datetime import timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path

import boto3
from pyproj import Geod

from backend.agent.evidence import DynamoEvidenceRepository
from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.common.serialization import fire_observation_from_dict, fire_observation_to_dict
from backend.processing.evidence_comparison import compare_attached_evidence


GEOD = Geod(ellps="WGS84")
MAX_MINUTES = 30
MAX_DISTANCE_KM = 5
_VIIRS_SATELLITES = {
    "N": "VIIRS_SNPP",
    "SNPP": "VIIRS_SNPP",
    "SUOMI-NPP": "VIIRS_SNPP",
    "N20": "VIIRS_NOAA20",
    "NOAA20": "VIIRS_NOAA20",
    "J1": "VIIRS_NOAA20",
    "1": "VIIRS_NOAA20",
    "N21": "VIIRS_NOAA21",
    "NOAA21": "VIIRS_NOAA21",
    "J2": "VIIRS_NOAA21",
    "2": "VIIRS_NOAA21",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--input-dir", type=Path, default=root / "data/processed/firms")
    parser.add_argument("--event-id", help="Limit attachment to one candidate event")
    parser.add_argument("--dry-run", action="store_true", help="Count strict matches without writing evidence")
    args = parser.parse_args()
    event_table_name = os.environ["EVENT_TABLE"]
    evidence_table_name = os.environ["EVIDENCE_TABLE"]
    region = os.environ.get("AWS_REGION", "us-east-2")
    observations = []
    for path in sorted(args.input_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8") as source:
            observations.extend(fire_observation_from_dict(json.loads(line)) for line in source)
    if not observations:
        parser.error(f"no normalized FIRMS JSONL records found in {args.input_dir}")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    events = DynamoCandidateEventRepository(event_table_name, dynamodb.Table(event_table_name))
    evidence_table = dynamodb.Table(evidence_table_name)
    evidence_repository = DynamoEvidenceRepository(evidence_table_name, evidence_table)
    matched_events = 0
    attached = 0
    selected_events = [events.get(args.event_id)] if args.event_id else events.all()
    if args.event_id and selected_events[0] is None:
        parser.error(f"candidate event not found: {args.event_id}")
    for event in selected_events:
        matches = [observation for observation in observations if _matches(event, observation)]
        if not matches:
            continue
        matched_events += 1
        if args.dry_run:
            attached += len(matches)
            continue
        attached_rows = []
        with evidence_table.batch_writer() as batch:
            for observation in matches:
                item = build_observation_evidence(event, observation)
                batch.put_item(Item=item)
                attached_rows.append(item)
                attached += 1
        comparison_rows = evidence_repository.list_for_event(event.event_id) + attached_rows
        comparison_record = build_sensor_comparison_evidence(event, comparison_rows)
        if comparison_record:
            evidence_repository.put_derived_record(comparison_record)
            events.put_feature_context(event.event_id, {
                "sensor_comparison": comparison_record["record"],
            })
    print(json.dumps({"events_with_matches": matched_events, "observations_matched": attached, "dry_run": args.dry_run}))
    return 0


def _matches(event, observation) -> bool:
    delta_minutes = abs((event.detected_at_utc - observation.observed_at_utc).total_seconds()) / 60
    _, _, distance_m = GEOD.inv(event.longitude, event.latitude, observation.longitude, observation.latitude)
    return delta_minutes <= MAX_MINUTES and distance_m / 1000 <= MAX_DISTANCE_KM


def build_observation_evidence(event, observation) -> dict:
    """Return only the actual observation; a detection does not establish coverage."""
    sensor = _sensor_source(observation)
    evidence_id = "firms_" + hashlib.sha256(
        f"{event.event_id}:{observation.fire_id}".encode()
    ).hexdigest()[:32]
    record = fire_observation_to_dict(observation)
    record.update({"evidence_id": evidence_id, "provider": "NASA_FIRMS", "source": sensor})
    return _dynamo_safe({
        "observation_id": evidence_id,
        "event_id": event.event_id,
        "event_time_utc": event.detected_at_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observed_at_utc": observation.observed_at_utc.isoformat().replace("+00:00", "Z"),
        "source": sensor,
        "evidence_type": "SENSOR_OBSERVATION",
        "latitude": observation.latitude,
        "longitude": observation.longitude,
        "record": record,
    })


def _sensor_source(observation) -> str:
    """Give attached evidence a stable sensor name, not FIRMS' compact code."""
    instrument = (observation.instrument or "").strip().upper()
    satellite = (observation.satellite or "").strip().upper()
    if instrument == "VIIRS":
        return _VIIRS_SATELLITES.get(satellite, f"VIIRS_{satellite}" if satellite else "VIIRS_UNKNOWN")
    if instrument == "MODIS":
        if satellite in {"TERRA", "T"}:
            return "MODIS_TERRA"
        if satellite in {"AQUA", "A"}:
            return "MODIS_AQUA"
        return f"MODIS_{satellite}" if satellite else "MODIS_UNKNOWN"
    return f"NASA_FIRMS_{instrument}_{satellite}".rstrip("_")


def build_sensor_comparison_evidence(event, rows: list[dict]) -> dict | None:
    """Persist a comparison only when actual matched observations support one."""
    result = compare_attached_evidence(event, rows)
    if result.get("status") == "INDEPENDENT_OBSERVATION_UNAVAILABLE":
        return None
    comparison_id = "cmp_" + hashlib.sha256(event.event_id.encode()).hexdigest()[:24]
    event_time = event.detected_at_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return _dynamo_safe({
        "observation_id": comparison_id,
        "event_id": event.event_id,
        "event_time_utc": event_time,
        "observed_at_utc": event_time,
        "source": "BURNBLIND_CROSS_SENSOR_COMPARISON",
        "evidence_type": "SENSOR_COMPARISON",
        "latitude": event.latitude,
        "longitude": event.longitude,
        "record": result,
    })


def _dynamo_safe(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _dynamo_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_dynamo_safe(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
