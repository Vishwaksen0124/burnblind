"""Queue environmental enrichment for newly persisted candidate events."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.features.environmental import EnvironmentalAnalysisLauncher


def insert_event_ids(event: Mapping[str, Any]) -> list[str]:
    return [
        event_id
        for record in event.get("Records", [])
        if record.get("eventName") == "INSERT"
        for event_id in [((record.get("dynamodb", {}).get("NewImage") or {}).get("event_id", {}).get("S"))]
        if event_id
    ]


def lambda_handler(event: Mapping[str, Any], context: Any) -> dict[str, Any]:
    import boto3

    table_name = os.environ["EVENT_TABLE"]
    queue_url = os.environ["ENVIRONMENTAL_ANALYSIS_QUEUE_URL"]
    dynamodb = boto3.resource("dynamodb")
    repository = DynamoCandidateEventRepository(table_name, dynamodb.Table(table_name))
    launcher = EnvironmentalAnalysisLauncher(repository, queue_url, boto3.client("sqs"))
    failures = []
    for record in event.get("Records", []):
        if record.get("eventName") != "INSERT":
            continue
        image = record.get("dynamodb", {}).get("NewImage") or {}
        event_id = image.get("event_id", {}).get("S")
        if not event_id:
            continue
        try:
            launcher.enqueue(event_id, f"stream-{event_id}")
        except Exception as exc:
            print(json.dumps({
                "level": "ERROR",
                "component": "environmental-trigger",
                "event_id": event_id,
                "error": type(exc).__name__,
            }, separators=(",", ":")))
            failures.append({"itemIdentifier": record.get("eventID", event_id)})
    return {"batchItemFailures": failures}