from datetime import datetime, timezone
import sys
from types import ModuleType, SimpleNamespace

from backend.agent.report import EvidenceFinding, InvestigationReport
from backend.agent.runtime import investigate_event
from backend.api.repository import MemoryCandidateEventRepository
from backend.common.models import CandidateEvent


EVENT_ID = "evt_000000000000000000000001"


def _event(event_id=EVENT_ID):
    timestamp = datetime(2025, 10, 1, 7, 0, tzinfo=timezone.utc)
    return CandidateEvent(
        event_id=event_id,
        grid_id="grid-v1-test",
        detected_at_utc=timestamp,
        last_observed_at_utc=timestamp,
        latitude=30.9,
        longitude=75.85,
        detection_count=1,
        sources=("GK2A_AMI",),
        evidence_ids=("obs_1",),
        data_mode="HISTORICAL_REPLAY",
        processing_version="candidate-events-v1",
    )


class EvidenceRepository:
    def list_for_event(self, event_id, limit=100):
        return [{
            "observation_id": "obs_1",
            "event_id": event_id,
            "source": "GK2A_AMI",
            "observed_at_utc": "2025-10-01T07:00:00Z",
            "latitude": 30.9,
            "longitude": 75.85,
            "confidence_flag": "NOMINAL",
        }]


def test_investigation_is_scoped_and_cites_only_tool_returned_evidence(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    events = MemoryCandidateEventRepository([_event(), _event("evt_000000000000000000000002")])
    report = InvestigationReport(
        classification="REVIEW_REQUIRED",
        summary="A satellite source record is available for analyst review.",
        evidence=[EvidenceFinding(evidence_id="obs_1", interpretation="A nominal satellite record is attached.")],
        contradictions=[],
        missing_evidence=["Independent sensor confirmation is unavailable."],
        recommended_action="HUMAN_VERIFICATION",
    )

    def agent_factory(tools):
        by_name = {tool.__name__: tool for tool in tools}
        assert by_name["get_event"]("evt_000000000000000000000002")["status"] == "NOT_FOUND"
        evidence = by_name["get_satellite_evidence"](EVENT_ID)
        assert evidence["observations"][0]["evidence_id"] == "obs_1"
        return lambda *_args, **_kwargs: SimpleNamespace(structured_output=report)

    result = investigate_event(
        EVENT_ID, events, EvidenceRepository(), agent_factory=agent_factory
    )

    assert result["classification"] == "REVIEW_REQUIRED"
    assert result["evidence"][0]["evidence_id"] == "obs_1"
    assert result["evidence"][0]["source"] == "GK2A_AMI"
    assert result["confidence"] is None
    assert result["model_id"] == "test-model"


def test_report_rejects_evidence_ids_not_returned_by_tools(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    report = InvestigationReport(
        classification="REVIEW_REQUIRED",
        summary="A satellite source record is available for analyst review.",
        evidence=[EvidenceFinding(evidence_id="invented", interpretation="A record exists.")],
        contradictions=[], missing_evidence=[], recommended_action="HUMAN_VERIFICATION",
    )
    result = SimpleNamespace(structured_output=report)

    try:
        investigate_event(
            EVENT_ID,
            MemoryCandidateEventRepository([_event()]),
            EvidenceRepository(),
            agent_factory=lambda _tools: lambda *_args, **_kwargs: result,
        )
    except ValueError as exc:
        assert "not returned by a tool" in str(exc)
    else:
        raise AssertionError("unverified evidence reference was accepted")
