"""Attach matched NASA FIRMS observations to replay events in DynamoDB."""

from __future__ import annotations

from datetime import timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path

import boto3
from pyproj import Geod

from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.common.serialization import fire_observation_from_dict, fire_observation_to_dict


GEOD = Geod(ellps="WGS84")
MAX_MINUTES = 30
MAX_DISTANCE_KM = 5


def main() -> int:
    event_table_name = os.environ["EVENT_TABLE"]
    evidence_table_name = os.environ["EVIDENCE_TABLE"]
    region = os.environ.get("AWS_REGION", "us-east-2")
    root = Path(__file__).resolve().parents[1]
    observations = []
    for path in sorted((root / "data/processed/firms").glob("*.jsonl")):
        with path.open(encoding="utf-8") as source:
            observations.extend(fire_observation_from_dict(json.loads(line)) for line in source)

    dynamodb = boto3.resource("dynamodb", region_name=region)
    events = DynamoCandidateEventRepository(event_table_name, dynamodb.Table(event_table_name))
    evidence_table = dynamodb.Table(evidence_table_name)
    matched_events = 0
    attached = 0
    for event in events.all():
        matches = [observation for observation in observations if _matches(event, observation)]
        if not matches:
            continue
        matched_events += 1
        with evidence_table.batch_writer() as batch:
            for observation in matches:
                evidence_id = "firms_" + hashlib.sha256(
                    f"{event.event_id}:{observation.fire_id}".encode()
                ).hexdigest()[:32]
                record = fire_observation_to_dict(observation)
                record.update({"evidence_id": evidence_id, "source": observation.satellite or observation.source})
                batch.put_item(Item=_dynamo_safe({
                    "observation_id": evidence_id,
                    "event_id": event.event_id,
                    "event_time_utc": event.detected_at_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "observed_at_utc": observation.observed_at_utc.isoformat().replace("+00:00", "Z"),
                    "source": observation.satellite or observation.source,
                    "evidence_type": "SENSOR_OBSERVATION",
                    "latitude": observation.latitude,
                    "longitude": observation.longitude,
                    "record": record,
                }))
                coverage_id = evidence_id + "_coverage"
                batch.put_item(Item=_dynamo_safe({
                    "observation_id": coverage_id,
                    "event_id": event.event_id,
                    "event_time_utc": event.detected_at_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "observed_at_utc": observation.observed_at_utc.isoformat().replace("+00:00", "Z"),
                    "source": observation.satellite or observation.source,
                    "evidence_type": "SENSOR_COVERAGE",
                    "latitude": observation.latitude,
                    "longitude": observation.longitude,
                    "record": {
                        "evidence_id": coverage_id,
                        "source": observation.satellite or observation.source,
                        "quality_valid": True,
                        "detection_present": True,
                        "coverage_radius_km": MAX_DISTANCE_KM,
                        "observed_at_utc": observation.observed_at_utc.isoformat().replace("+00:00", "Z"),
                    },
                }))
                attached += 1
    print(json.dumps({"events_with_matches": matched_events, "observations_attached": attached}))
    return 0


def _matches(event, observation) -> bool:
    delta_minutes = abs((event.detected_at_utc - observation.observed_at_utc).total_seconds()) / 60
    _, _, distance_m = GEOD.inv(event.longitude, event.latitude, observation.longitude, observation.latitude)
    return delta_minutes <= MAX_MINUTES and distance_m / 1000 <= MAX_DISTANCE_KM


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