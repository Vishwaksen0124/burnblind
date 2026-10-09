from datetime import datetime, timezone
import json
import sys
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.agent.report import EvidenceContradiction, EvidenceFinding, InvestigationReport
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
    def __init__(self, records=None):
        self.derived = []
        self.records = records

    def list_for_event(self, event_id, limit=100):
        if self.records is not None:
            return self.records
        return [{
            "observation_id": "obs_1",
            "event_id": event_id,
            "source": "GK2A_AMI",
            "observed_at_utc": "2025-10-01T07:00:00Z",
            "latitude": 30.9,
            "longitude": 75.85,
            "confidence_flag": "NOMINAL",
        }]

    def put_derived_record(self, record):
        self.derived.append(record)


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
        uncertainties=["Independent sensor confirmation is unavailable."],
        recommendations=["HUMAN_VERIFICATION"],
    )

    def agent_factory(tools):
        assert tools == []

        def invoke(prompt, structured_output_model):
            assert structured_output_model is InvestigationReport
            assert EVENT_ID in prompt
            assert "obs_1" in prompt
            assert "No independent source observation or validated coverage record is available." in prompt
            return SimpleNamespace(structured_output=report)

        return invoke

    result = investigate_event(
        EVENT_ID, events, EvidenceRepository(), agent_factory=agent_factory
    )

    assert result["classification"] == "REVIEW_REQUIRED"
    assert result["evidence"][0]["evidence_id"] == "obs_1"
    assert result["evidence"][0]["source"] == "GK2A_AMI"
    assert "event_id" not in result
    assert "confidence" not in result
    assert "model_id" not in result


def test_report_rejects_evidence_ids_not_returned_by_tools(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    report = InvestigationReport(
        classification="REVIEW_REQUIRED",
        summary="A satellite source record is available for analyst review.",
        evidence=[EvidenceFinding(evidence_id="invented", interpretation="A record exists.")],
        contradictions=[], missing_evidence=[], uncertainties=[], recommendations=["HUMAN_VERIFICATION"],
    )
    result = SimpleNamespace(structured_output=report)

    try:
        investigate_event(
            EVENT_ID,
            MemoryCandidateEventRepository([_event()]),
            EvidenceRepository(),
            agent_factory=lambda tools: lambda *_args, **_kwargs: result,
        )
    except ValueError as exc:
        assert "not returned by a tool" in str(exc)
    else:
        raise AssertionError("unverified evidence reference was accepted")


@pytest.mark.parametrize(
    "override",
    [
        {"classification": "CONFIRMED"},
        {"recommendations": ["EVACUATE"]},
        {"recommendations": []},
    ],
)
def test_structured_report_schema_rejects_unsupported_output(override):
    values = {
        "classification": "REVIEW_REQUIRED",
        "summary": "A supplied candidate record needs evidence-based human review.",
        "evidence": [],
        "contradictions": [],
        "missing_evidence": [],
        "uncertainties": [],
        "recommendations": ["HUMAN_VERIFICATION"],
    }
    values.update(override)

    with pytest.raises(ValidationError):
        InvestigationReport(**values)


def test_absent_satellite_evidence_forces_insufficient_evidence(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    report = InvestigationReport(
        classification="REVIEW_REQUIRED",
        summary="Context alone cannot establish whether a current event is present.",
        evidence=[], contradictions=[], missing_evidence=[], uncertainties=[],
        recommendations=["HUMAN_VERIFICATION"],
    )
    result = investigate_event(
        EVENT_ID,
        MemoryCandidateEventRepository([_event()]),
        EvidenceRepository(records=[]),
        agent_factory=lambda tools: lambda *_args, **_kwargs: SimpleNamespace(structured_output=report),
    )

    assert result["classification"] == "INSUFFICIENT_EVIDENCE"
    assert "No satellite observation record was available for this event." in result["missing_evidence"]
    assert "HUMAN_VERIFICATION" in result["recommendations"]


def test_weather_and_population_are_preassembled_as_agent_input(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    from backend.common.models import WeatherObservation

    evidence = EvidenceRepository()
    report = InvestigationReport(
        classification="REVIEW_REQUIRED",
        summary="One supplied satellite observation remains uncertain and needs human review.",
        evidence=[EvidenceFinding(evidence_id="obs_1", interpretation="A nominal satellite record is attached.")],
        contradictions=[], missing_evidence=[], uncertainties=["No independent detection is attached."],
        recommendations=["HUMAN_VERIFICATION"],
    )
    captured = {}

    def agent_factory(tools):
        assert tools == []

        def invoke(prompt, structured_output_model):
            captured["packet"] = json.loads(prompt.split("Evidence packet (JSON):\n", 1)[1])
            return SimpleNamespace(structured_output=report)

        return invoke

    result = investigate_event(
        EVENT_ID,
        MemoryCandidateEventRepository([_event()]),
        evidence,
        agent_factory=agent_factory,
        weather_lookup=lambda lat, lon, when: WeatherObservation(
            when.replace(minute=0, second=0, microsecond=0), lat, lon, 3.0, 270.0,
            "OPEN_METEO_ERA5_REANALYSIS", "fixture-era5-v1",
        ),
        population_lookup=lambda geometry, year, resolution: {
            "population_estimate": 1234,
            "population_year": year,
            "resolution": resolution,
            "source": "WorldPop fixture",
            "source_version": "fixture-v1",
            "limitations": ["Test fixture only."],
        },
    )

    packet = captured["packet"]
    assert packet["weather"]["wind_speed_m_s"] == 3.0
    assert packet["exposure"]["population_estimate"] == 1234
    assert packet["exposure"]["method"] == "DIRECTIONAL_CORRIDOR"
    assert "event_id" not in result
    assert len(evidence.derived) == 2


def test_sensor_agreement_is_not_reported_as_missing_or_disagreement(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    records = [
        {
            "observation_id": "obs_1", "event_id": EVENT_ID, "evidence_type": "SATELLITE_DETECTION",
            "source": "GK2A_AMI", "observed_at_utc": "2025-10-01T07:00:00Z",
            "latitude": 30.9, "longitude": 75.85,
        },
        {
            "observation_id": "viirs_1", "event_id": EVENT_ID, "evidence_type": "SATELLITE_DETECTION",
            "source": "VIIRS", "observed_at_utc": "2025-10-01T07:05:00Z",
            "latitude": 30.9, "longitude": 75.85,
        },
    ]
    report = InvestigationReport(
        classification="REVIEW_REQUIRED", summary="Two supplied satellite records match within the comparison window.",
        evidence=[EvidenceFinding(evidence_id="obs_1", interpretation="A GK2A observation is attached.")],
        contradictions=[], missing_evidence=[], uncertainties=[],
        recommendations=["HUMAN_VERIFICATION", "REVIEW_SENSOR_DISAGREEMENT"],
    )
    captured = {}

    def agent_factory(tools):
        assert tools == []

        def invoke(prompt, structured_output_model):
            captured["packet"] = json.loads(prompt.split("Evidence packet (JSON):\n", 1)[1])
            return SimpleNamespace(structured_output=report)

        return invoke

    result = investigate_event(
        EVENT_ID, MemoryCandidateEventRepository([_event()]), EvidenceRepository(records), agent_factory=agent_factory,
    )

    assert captured["packet"]["sensor_comparison"]["status"] == "AGREEMENT"
    assert "No independent source observation or validated coverage record is available." not in result["missing_evidence"]
    assert "A usable cross-sensor comparison is unavailable." not in result["missing_evidence"]
    assert "REVIEW_SENSOR_DISAGREEMENT" not in result["recommendations"]


def test_quality_valid_negative_coverage_is_cited_as_disagreement(monkeypatch):
    strands = ModuleType("strands")
    strands.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "strands", strands)
    records = [
        {
            "observation_id": "obs_1", "event_id": EVENT_ID, "evidence_type": "SATELLITE_DETECTION",
            "source": "GK2A_AMI", "observed_at_utc": "2025-10-01T07:00:00Z",
            "latitude": 30.9, "longitude": 75.85,
        },
        {
            "observation_id": "coverage_row", "event_id": EVENT_ID, "evidence_type": "SENSOR_COVERAGE",
            "source": "VIIRS", "observed_at_utc": "2025-10-01T07:05:00Z",
            "latitude": 30.9, "longitude": 75.85,
            "record": {
                "evidence_id": "coverage_1", "source": "VIIRS", "observed_at_utc": "2025-10-01T07:05:00Z",
                "latitude": 30.9, "longitude": 75.85, "coverage_radius_km": 1.5,
                "quality_valid": True, "detection_present": False,
            },
        },
    ]
    report = InvestigationReport(
        classification="REVIEW_REQUIRED", summary="A GK2A observation conflicts with explicit VIIRS coverage evidence.",
        evidence=[EvidenceFinding(evidence_id="obs_1", interpretation="GK2A reports a supplied thermal observation.")],
        contradictions=[EvidenceContradiction(
            evidence_ids=["obs_1", "coverage_1"],
            explanation="GK2A reports an observation while valid VIIRS coverage reports no matching detection.",
        )], missing_evidence=[], uncertainties=[],
        recommendations=["HUMAN_VERIFICATION", "REVIEW_SENSOR_DISAGREEMENT"],
    )
    captured = {}

    def agent_factory(tools):
        assert tools == []

        def invoke(prompt, structured_output_model):
            captured["packet"] = json.loads(prompt.split("Evidence packet (JSON):\n", 1)[1])
            return SimpleNamespace(structured_output=report)

        return invoke

    result = investigate_event(
        EVENT_ID, MemoryCandidateEventRepository([_event()]), EvidenceRepository(records), agent_factory=agent_factory,
    )

    assert captured["packet"]["satellite"]["observations"][0]["evidence_id"] == "obs_1"
    assert captured["packet"]["sensor_comparison"]["status"] == "DISAGREEMENT"
    assert result["contradictions"][0]["evidence_ids"] == ["obs_1", "coverage_1"]
    assert result["recommendations"] == ["HUMAN_VERIFICATION", "REVIEW_SENSOR_DISAGREEMENT"]
