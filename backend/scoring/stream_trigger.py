"""Automatically queue investigations when versioned scores qualify an event."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

from backend.agent.storage import DynamoInvestigationStore, SqsInvestigationLauncher
from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.scoring.engine import ScoreFeatures, investigation_trigger, load_score_config, score_event


_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "scoring.v1.json"


def evaluate_score_features(payload: dict[str, Any], config_path: str | Path = _CONFIG_PATH) -> dict[str, Any]:
    """Return the deterministic score and trigger decision for persisted features."""
    allowed = set(ScoreFeatures.__dataclass_fields__)
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ValueError("score_features contains unsupported fields")
    features = ScoreFeatures(**payload)
    config = load_score_config(config_path)
    result = score_event(features, config)
    trigger = investigation_trigger(result, config, features.exposure_score)
    return {
        "should_investigate": trigger.should_investigate,
        "reasons": list(trigger.reasons),
        "score_version": result.score_version,
        "feature_version": result.feature_version,
        "blindness_score": result.blindness_score,
        "fire_likelihood_score": result.fire_likelihood_score,
        "uncertainty": result.uncertainty,
        "priority_score": result.priority_score,
        "evidence_completeness": result.evidence_completeness,
    }


def lambda_handler(event, context):
    import boto3
    from boto3.dynamodb.types import TypeDeserializer

    dynamodb = boto3.resource("dynamodb")
    events_table = dynamodb.Table(_required_env("EVENT_TABLE"))
    investigations_table = dynamodb.Table(_required_env("INVESTIGATION_TABLE"))
    queue_url = _required_env("INVESTIGATION_QUEUE_URL")
    event_repository = DynamoCandidateEventRepository(_required_env("EVENT_TABLE"), events_table)
    store = DynamoInvestigationStore(investigations_table)
    launcher = SqsInvestigationLauncher(store, queue_url, boto3.client("sqs"))
    deserializer = TypeDeserializer()
    failures = []

    for record in event.get("Records", []):
        try:
            _handle_record(record, deserializer, events_table, event_repository, launcher)
        except Exception as exc:
            print(json.dumps({"level": "ERROR", "event_id": record.get("eventID"), "error": type(exc).__name__}))
            failures.append({"itemIdentifier": record["eventID"]})
    return {"batchItemFailures": failures}


def _handle_record(record, deserializer, events_table, event_repository, launcher) -> None:
    image = record.get("dynamodb", {}).get("NewImage")
    if not image:
        return
    item = {name: deserializer.deserialize(value) for name, value in image.items()}
    raw_features = item.get("score_features")
    if not isinstance(raw_features, dict):
        return
    features = _plain_numbers(raw_features)
    if not any(
        key != "sensor_disagreement" and value is not None
        for key, value in features.items()
    ):
        return
    fingerprint = hashlib.sha256(
        json.dumps(features, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if item.get("trigger_evaluation_hash") == fingerprint:
        return

    decision = evaluate_score_features(features)
    if decision["should_investigate"]:
        candidate = event_repository.get(item["event_id"])
        if candidate is None:
            raise ValueError("scored candidate event no longer exists")
        request_id = "score-" + hashlib.sha256(
            f"{candidate.event_id}:{fingerprint}".encode()
        ).hexdigest()[:32]
        launcher.enqueue(
            candidate,
            request_id,
            trigger_reasons=decision["reasons"],
            score_snapshot=decision,
        )

    _persist_evaluation(events_table, item["event_id"], fingerprint, decision)


def _persist_evaluation(table, event_id: str, fingerprint: str, decision: dict[str, Any]) -> None:
    values = {
        "trigger_evaluation_hash": fingerprint,
        "trigger_evaluation_version": decision["score_version"],
        "investigation_qualifies": decision["should_investigate"],
        "investigation_status": "QUEUED" if decision["should_investigate"] else "NOT_REQUIRED",
        "investigation_trigger_reasons": decision["reasons"],
        "score_version": decision["score_version"],
        "feature_version": decision["feature_version"],
        "evidence_completeness": Decimal(str(decision["evidence_completeness"])),
    }
    for key in ("blindness_score", "fire_likelihood_score", "uncertainty", "priority_score"):
        if decision[key] is not None:
            values[key] = Decimal(str(decision[key]))
    assignments = []
    names = {}
    expression_values = {}
    for index, (key, value) in enumerate(values.items()):
        name, placeholder = f"#n{index}", f":v{index}"
        names[name] = key
        expression_values[placeholder] = value
        assignments.append(f"{name} = {placeholder}")
    table.update_item(
        Key={"event_id": event_id},
        UpdateExpression="SET " + ", ".join(assignments),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=expression_values,
    )


def _plain_numbers(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _plain_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_numbers(item) for item in value]
    return value


def _required_env(name: str) -> str:
    import os

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value
