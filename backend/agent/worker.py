"""SQS worker that investigates one candidate at a time."""

from __future__ import annotations

import json
import os

from backend.agent.evidence import DynamoEvidenceRepository
from backend.agent.runtime import investigate_event
from backend.agent.storage import DynamoInvestigationStore
from backend.api.dynamodb_repository import DynamoCandidateEventRepository


def lambda_handler(event, context):
    import boto3

    dynamodb = boto3.resource("dynamodb")
    events = DynamoCandidateEventRepository(os.environ["EVENT_TABLE"], dynamodb.Table(os.environ["EVENT_TABLE"]))
    evidence = DynamoEvidenceRepository(os.environ["EVIDENCE_TABLE"], dynamodb.Table(os.environ["EVIDENCE_TABLE"]))
    investigations = DynamoInvestigationStore(dynamodb.Table(os.environ["INVESTIGATION_TABLE"]))

    for record in event.get("Records", []):
        message = json.loads(record["body"])
        event_id = message["event_id"]
        existing = investigations.get(event_id)
        if existing and existing.get("status") == "COMPLETED":
            continue
        investigations.set_running(event_id)
        try:
            report = investigate_event(event_id, events, evidence)
            investigations.complete(event_id, report)
        except Exception as exc:
            investigations.fail(event_id, _error_code(exc))
            raise
    return {"batchItemFailures": []}


def _error_code(error: Exception) -> str:
    name = type(error).__name__
    return name if name.isidentifier() else "INVESTIGATION_FAILED"
