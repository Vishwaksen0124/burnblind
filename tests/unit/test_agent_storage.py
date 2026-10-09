from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from backend.agent.storage import DynamoInvestigationStore, SqsInvestigationLauncher


EVENT_ID = "evt_000000000000000000000001"


def _conditional_failure(operation):
    return ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "condition failed"}},
        operation,
    )


class InvestigationTable:
    def __init__(self, item=None, *, race_on_retry=False):
        self.item = deepcopy(item)
        self.race_on_retry = race_on_retry

    def put_item(self, *, Item, ConditionExpression):
        assert ConditionExpression == "attribute_not_exists(event_id)"
        if self.item is not None:
            raise _conditional_failure("PutItem")
        self.item = deepcopy(Item)

    def get_item(self, *, Key, ConsistentRead=False):
        assert Key == {"event_id": EVENT_ID}
        return {"Item": deepcopy(self.item)} if self.item is not None else {}

    def update_item(self, **request):
        assert request["ConditionExpression"] == "#status = :failed"
        if self.race_on_retry:
            self.item["status"] = "QUEUED"
            raise _conditional_failure("UpdateItem")
        if self.item.get("status") != "FAILED":
            raise _conditional_failure("UpdateItem")
        values = request["ExpressionAttributeValues"]
        self.item.update({
            "status": values[":queued"],
            "requested_at_utc": values[":requested"],
            "updated_at_utc": values[":requested"],
            "request_id": values[":request"],
        })
        if ":reasons" in values:
            self.item["trigger_reasons"] = values[":reasons"]
        if ":score" in values:
            self.item["score_snapshot"] = values[":score"]
        for key in ("error_code", "started_at_utc", "completed_at_utc", "report", "model_id", "agent_version", "prompt_version"):
            self.item.pop(key, None)


def _failed_item():
    return {
        "event_id": EVENT_ID,
        "status": "FAILED",
        "error_code": "MODEL_TIMEOUT",
        "started_at_utc": "2025-10-01T07:00:00Z",
        "completed_at_utc": "2025-10-01T07:02:00Z",
        "report": {"summary": "stale"},
        "model_id": "old-model",
        "agent_version": "old-agent",
        "prompt_version": "old-prompt",
    }


def _event():
    return SimpleNamespace(event_id=EVENT_ID)


def test_queue_creates_one_request_and_deduplicates_active_event():
    table = InvestigationTable()
    store = DynamoInvestigationStore(table)

    first, created = store.queue(_event(), "request-1")
    duplicate, duplicate_created = store.queue(_event(), "request-2")

    assert created is True
    assert first["status"] == "QUEUED"
    assert duplicate_created is False
    assert duplicate["request_id"] == "request-1"
    assert table.item["request_id"] == "request-1"


def test_failed_investigation_retry_resets_old_run_fields():
    table = InvestigationTable(_failed_item())
    store = DynamoInvestigationStore(table)

    retried, created = store.queue(_event(), "retry-request", ["ANALYST_OVERRIDE"])

    assert created is True
    assert retried["status"] == "QUEUED"
    assert retried["request_id"] == "retry-request"
    assert retried["trigger_reasons"] == ["ANALYST_OVERRIDE"]
    assert not {"error_code", "started_at_utc", "completed_at_utc", "report", "model_id"} & retried.keys()


def test_concurrent_failed_retries_return_the_winning_queued_request():
    table = InvestigationTable(_failed_item(), race_on_retry=True)
    store = DynamoInvestigationStore(table)

    result, created = store.queue(_event(), "losing-retry")

    assert created is False
    assert result["status"] == "QUEUED"


def test_duplicate_request_does_not_send_another_sqs_message():
    item = {"event_id": EVENT_ID, "status": "QUEUED"}
    store = Mock()
    store.queue.return_value = (item, False)
    queue = Mock()
    launcher = SqsInvestigationLauncher(store, "queue-url", queue)

    result, created = launcher.enqueue(_event(), "second-request")

    assert result is item
    assert created is False
    queue.send_message.assert_not_called()


def test_sqs_dispatch_failure_marks_request_failed_and_propagates():
    store = Mock()
    store.queue.return_value = ({"event_id": EVENT_ID, "status": "QUEUED"}, True)
    queue = Mock()
    queue.send_message.side_effect = RuntimeError("queue unavailable")
    launcher = SqsInvestigationLauncher(store, "queue-url", queue)

    with pytest.raises(RuntimeError, match="queue unavailable"):
        launcher.enqueue(_event(), "request-1")

    store.fail.assert_called_once_with(EVENT_ID, "QUEUE_SEND_FAILED")
