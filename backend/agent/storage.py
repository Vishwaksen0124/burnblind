"""Idempotent investigation persistence and SQS dispatch."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import base64
from typing import Any

from backend.common.models import CandidateEvent


class DynamoInvestigationStore:
    def __init__(self, table: Any):
        self._table = table

    def get(self, event_id: str) -> dict[str, Any] | None:
        return self._table.get_item(Key={"event_id": event_id}, ConsistentRead=True).get("Item")

    def list(self, limit: int = 100, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        """List persisted investigations for the review page (table is event-keyed)."""
        from boto3.dynamodb.conditions import Attr

        args: dict[str, Any] = {
            "Limit": max(1, min(limit, 100)),
            "FilterExpression": Attr("status").is_in(["QUEUED", "RUNNING", "COMPLETED", "FAILED"]),
        }
        if cursor:
            args["ExclusiveStartKey"] = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        page = self._table.scan(**args)
        items = page.get("Items", [])
        items.sort(key=lambda item: item.get("updated_at_utc", item.get("completed_at_utc", item.get("requested_at_utc", ""))), reverse=True)
        next_key = page.get("LastEvaluatedKey")
        next_cursor = base64.urlsafe_b64encode(json.dumps(next_key, separators=(",", ":")).encode()).decode() if next_key else None
        return items, next_cursor

    def queue(
        self,
        event: CandidateEvent,
        request_id: str,
        trigger_reasons: list[str] | tuple[str, ...] = (),
        score_snapshot: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        item = {
            "event_id": event.event_id,
            "investigation_id": f"inv_{event.event_id.removeprefix('evt_')}",
            "status": "QUEUED",
            "requested_at_utc": now,
            "updated_at_utc": now,
            "request_id": request_id,
        }
        if trigger_reasons:
            item["trigger_reasons"] = list(trigger_reasons)
        if score_snapshot is not None:
            item["score_snapshot"] = _dynamo_safe(score_snapshot)
        from botocore.exceptions import ClientError

        try:
            self._table.put_item(Item=item, ConditionExpression="attribute_not_exists(event_id)")
            return item, True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
                raise
            existing = self.get(event.event_id)
            if not existing or existing.get("status") != "FAILED":
                return existing or item, False
            names = {"#status": "status"}
            values = {":queued": "QUEUED", ":failed": "FAILED", ":requested": now, ":request": request_id}
            assignments = ["#status = :queued", "requested_at_utc = :requested", "updated_at_utc = :requested", "request_id = :request"]
            if trigger_reasons:
                values[":reasons"] = list(trigger_reasons)
                assignments.append("trigger_reasons = :reasons")
            if score_snapshot is not None:
                values[":score"] = _dynamo_safe(score_snapshot)
                assignments.append("score_snapshot = :score")
            self._table.update_item(
                Key={"event_id": event.event_id},
                UpdateExpression="SET " + ", ".join(assignments) + " REMOVE error_code, started_at_utc, completed_at_utc, report, model_id, agent_version, prompt_version",
                ConditionExpression="#status = :failed",
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
            )
            return self.get(event.event_id) or item, True

    def set_running(self, event_id: str) -> None:
        now = _now()
        self._table.update_item(
            Key={"event_id": event_id},
            UpdateExpression="SET #status = :running, started_at_utc = :now, updated_at_utc = :now",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":running": "RUNNING", ":now": now},
        )

    def complete(self, event_id: str, report: dict[str, Any], model_id: str, agent_version: str, prompt_version: str) -> None:
        now = _now()
        self._table.update_item(
            Key={"event_id": event_id},
            UpdateExpression="SET #status = :status, completed_at_utc = :now, updated_at_utc = :now, report = :report, model_id = :model, agent_version = :agent, prompt_version = :prompt REMOVE error_code",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "COMPLETED", ":now": now, ":report": report,
                ":model": model_id,
                ":agent": agent_version,
                ":prompt": prompt_version,
            },
        )

    def fail(self, event_id: str, error_code: str) -> None:
        now = _now()
        self._table.update_item(
            Key={"event_id": event_id},
            UpdateExpression="SET #status = :failed, error_code = :error, updated_at_utc = :now",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":failed": "FAILED", ":error": error_code, ":now": now},
        )


class SqsInvestigationLauncher:
    def __init__(self, store: DynamoInvestigationStore, queue_url: str, client: Any):
        self._store = store
        self._queue_url = queue_url
        self._client = client

    def enqueue(
        self,
        event: CandidateEvent,
        request_id: str,
        trigger_reasons: list[str] | tuple[str, ...] = (),
        score_snapshot: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        item, created = self._store.queue(event, request_id, trigger_reasons, score_snapshot)
        if not created:
            return item, False
        try:
            self._client.send_message(
                QueueUrl=self._queue_url,
                MessageBody=json.dumps({"event_id": event.event_id, "request_id": request_id}),
                MessageGroupId=event.event_id,
                MessageDeduplicationId=hashlib.sha256(f"{event.event_id}:{request_id}".encode()).hexdigest(),
            )
        except Exception:
            self._store.fail(event.event_id, "QUEUE_SEND_FAILED")
            raise
        return item, True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dynamo_safe(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _dynamo_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_dynamo_safe(item) for item in value]
    return value
