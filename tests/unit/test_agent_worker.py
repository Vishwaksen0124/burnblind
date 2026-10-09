import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from backend.agent import worker


EVENT_ID = "evt_000000000000000000000001"


class InvestigationStore:
    def __init__(self, _table):
        self.record = None
        self.state = None

    def get(self, event_id):
        assert event_id == EVENT_ID
        return self.record

    def set_running(self, event_id):
        self.state = (event_id, "RUNNING")

    def fail(self, event_id, error_code):
        self.state = (event_id, "FAILED", error_code)

    def complete(self, event_id, report, model_id, agent_version, prompt_version):
        self.state = (event_id, "COMPLETED", report, model_id, agent_version, prompt_version)


def _configure_worker(monkeypatch, store):
    class FakeDynamo:
        def Table(self, table_name):
            return table_name

    boto3 = ModuleType("boto3")
    boto3.resource = lambda service: FakeDynamo()
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setattr(worker, "DynamoCandidateEventRepository", lambda *args: object())
    monkeypatch.setattr(worker, "DynamoEvidenceRepository", lambda *args: object())
    monkeypatch.setattr(worker, "DynamoInvestigationStore", lambda _table: store)
    monkeypatch.setenv("EVENT_TABLE", "events")
    monkeypatch.setenv("EVIDENCE_TABLE", "evidence")
    monkeypatch.setenv("INVESTIGATION_TABLE", "investigations")
    monkeypatch.setenv("INVESTIGATION_MODEL_PROVIDER", "bedrock-mantle")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "deepseek.v3.2")


def _sqs_event():
    return {"Records": [{"body": json.dumps({"event_id": EVENT_ID, "request_id": "request-1"})}]}


def test_worker_persists_failure_and_raises_for_sqs_retry(monkeypatch):
    store = InvestigationStore("investigations")
    _configure_worker(monkeypatch, store)
    monkeypatch.setattr(worker, "investigate_event", lambda *_: (_ for _ in ()).throw(RuntimeError("model unavailable")))

    with pytest.raises(RuntimeError, match="model unavailable"):
        worker.lambda_handler(_sqs_event(), SimpleNamespace())

    assert store.state == (EVENT_ID, "FAILED", "RuntimeError")


def test_worker_skips_completed_duplicate_without_invoking_agent(monkeypatch):
    store = InvestigationStore("investigations")
    store.record = {"event_id": EVENT_ID, "status": "COMPLETED"}
    _configure_worker(monkeypatch, store)
    monkeypatch.setattr(worker, "investigate_event", lambda *_: pytest.fail("completed duplicate was re-run"))

    result = worker.lambda_handler(_sqs_event(), SimpleNamespace())

    assert result == {"batchItemFailures": []}
    assert store.state is None
