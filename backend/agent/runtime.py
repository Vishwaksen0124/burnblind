"""Strands investigation agent with a separately configurable model provider."""

from __future__ import annotations

import json
import os
from typing import Any

from backend.agent.evidence import DynamoEvidenceRepository, build_evidence_tools
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.report import InvestigationReport
from backend.api.repository import CandidateEventRepository
from backend.common.models import EvidenceReference


AGENT_VERSION = "burnblind-investigator-v2"
PROMPT_VERSION = "burnblind-investigation-v2"


def investigate_event(
    event_id: str,
    events: CandidateEventRepository,
    evidence: DynamoEvidenceRepository,
    *,
    model_id: str | None = None,
    region: str | None = None,
    agent_factory: Any | None = None,
    weather_lookup: Any | None = None,
    population_lookup: Any | None = None,
) -> dict[str, Any]:
    event = events.get(event_id)
    if event is None:
        raise ValueError("candidate event no longer exists")

    # Imports remain inside the runtime path so API/local data tooling does not
    # require the agent's model SDK.
    if agent_factory is None:
        from strands import Agent
        selected_region = region or os.environ.get("AWS_REGION", "us-east-2")
        provider = os.environ.get("INVESTIGATION_MODEL_PROVIDER", "bedrock").strip().lower()

        if provider == "bedrock":
            from strands.models import BedrockModel

            selected_model = model_id or os.environ.get("BEDROCK_MODEL_ID", "deepseek.v3.2")
            model = BedrockModel(
                model_id=selected_model,
                region_name=selected_region,
                temperature=0,
                max_tokens=900,
                streaming=False,
            )
        elif provider == "bedrock-mantle":
            from strands.models.openai import OpenAIModel

            selected_model = model_id or os.environ.get("BEDROCK_MODEL_ID", "deepseek.v3.2")
            model = OpenAIModel(
                model_id=selected_model,
                bedrock_mantle_config={"region": selected_region},
                params={"temperature": 0, "max_tokens": 900},
                stream=False,
            )
        elif provider == "sagemaker":
            from strands.models.sagemaker import SageMakerAIModel

            endpoint_name = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "").strip()
            if not endpoint_name:
                raise RuntimeError(
                    "SAGEMAKER_ENDPOINT_NAME is required when "
                    "INVESTIGATION_MODEL_PROVIDER=sagemaker"
                )
            model = SageMakerAIModel(
                endpoint_config={
                    "endpoint_name": endpoint_name,
                    "region_name": selected_region,
                },
                payload_config={
                    "temperature": 0,
                    "max_tokens": 900,
                    "stream": False,
                },
            )
            selected_model = f"sagemaker:{endpoint_name}"
        else:
            raise ValueError(
                "INVESTIGATION_MODEL_PROVIDER must be 'bedrock', "
                "'bedrock-mantle', or 'sagemaker'"
            )

        agent_factory = lambda tools: Agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None,
        )
    else:
        selected_model = model_id or "test-model"

    evidence_registry: dict[str, dict[str, str]] = {}
    tools = build_evidence_tools(
        events, evidence, evidence_registry, weather_lookup, population_lookup, target_event_id=event_id
    )
    # Evidence sources required for every review are read once by the service,
    # then passed as a bounded, event-scoped input packet. The model has no
    # tools to retry, fan out, or accidentally investigate another event.
    evidence_packet = {
        "event": _call_tool(tools[0], event_id=event_id),
        "satellite": _call_tool(tools[1], event_id=event_id),
        "historical_context": _call_tool(tools[2], event_id=event_id),
        "weather": _call_tool(tools[3], event_id=event_id),
        "exposure": _call_tool(tools[4], event_id=event_id),
        "sensor_comparison": _call_tool(tools[5], event_id=event_id),
    }
    evidence_packet["missing_evidence"] = _missing_evidence(evidence_packet)
    agent = agent_factory([])
    result = agent(
        "Produce the evidence report for this one candidate. Follow the system "
        "rules and the structured schema exactly. Evidence packet (JSON):\n"
        + json.dumps(evidence_packet, separators=(",", ":"), default=str),
        structured_output_model=InvestigationReport,
    )
    parsed: InvestigationReport = result.structured_output

    cited: list[dict[str, str]] = []
    for finding in parsed.evidence:
        metadata = evidence_registry.get(finding.evidence_id)
        if metadata is None:
            raise ValueError("agent cited evidence that was not returned by a tool")
        reference = EvidenceReference(
            evidence_id=finding.evidence_id,
            evidence_type=metadata["type"],
            source=metadata["source"],
            summary=finding.interpretation,
        )
        cited.append({
            "evidence_id": reference.evidence_id,
            "evidence_type": reference.evidence_type,
            "source": reference.source,
            "summary": reference.summary,
        })

    satellite_found = (
        evidence_packet["satellite"].get("status") == "OK"
        and bool(evidence_packet["satellite"].get("observations"))
    )
    if satellite_found and not any(item["evidence_type"] == "SATELLITE" for item in cited):
        raise ValueError("agent report omitted the available satellite evidence citation")
    for contradiction in parsed.contradictions:
        if len(set(contradiction.evidence_ids)) < 2 or any(evidence_id not in evidence_registry for evidence_id in contradiction.evidence_ids):
            raise ValueError("agent cited a contradiction record that was not supplied")
    classification = parsed.classification
    if not satellite_found:
        classification = "INSUFFICIENT_EVIDENCE"
    if satellite_found and classification == "INSUFFICIENT_EVIDENCE":
        classification = "REVIEW_REQUIRED"
    recommendations = list(parsed.recommendations)
    if classification in {"REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE"} and "HUMAN_VERIFICATION" not in recommendations:
        recommendations.insert(0, "HUMAN_VERIFICATION")
    comparison_status = evidence_packet["sensor_comparison"].get("status")
    if comparison_status != "DISAGREEMENT":
        recommendations = [item for item in recommendations if item != "REVIEW_SENSOR_DISAGREEMENT"]
    if evidence_packet["exposure"].get("status") != "OK":
        recommendations = [item for item in recommendations if item != "REVIEW_EXPOSURE"]
    if not recommendations:
        recommendations = ["HUMAN_VERIFICATION"]

    return {
        "classification": classification,
        "summary": parsed.summary,
        "evidence": cited,
        "contradictions": [
            {"evidence_ids": item.evidence_ids, "explanation": item.explanation}
            for item in parsed.contradictions
        ],
        "missing_evidence": evidence_packet["missing_evidence"],
        "uncertainties": parsed.uncertainties,
        "recommendations": recommendations,
    }


def _call_tool(tool: Any, **kwargs: Any) -> dict[str, Any]:
    """Call one deterministic evidence adapter and normalize unexpected errors."""
    try:
        result = tool(**kwargs)
    except Exception as exc:
        return {"status": "UNAVAILABLE", "detail": f"Evidence adapter error: {type(exc).__name__}."}
    return result if isinstance(result, dict) else {"status": "UNAVAILABLE", "detail": "Evidence adapter returned an invalid payload."}


def _missing_evidence(packet: dict[str, Any]) -> list[str]:
    """Derive explicit evidence gaps from adapter status, never from model inference."""
    gaps = []
    if packet["satellite"].get("status") != "OK":
        gaps.append("No satellite observation record was available for this event.")
    if packet["historical_context"].get("status") != "OK":
        gaps.append("Sourced historical-context records are unavailable.")
    if packet["weather"].get("status") != "OK":
        gaps.append("Sourced weather estimates are unavailable.")
    if packet["exposure"].get("status") != "OK":
        gaps.append("A sourced population-exposure estimate is unavailable.")
    comparison_status = packet["sensor_comparison"].get("status")
    if comparison_status == "INDEPENDENT_OBSERVATION_UNAVAILABLE":
        gaps.append("No independent source observation or validated coverage record is available.")
    elif comparison_status == "INCONCLUSIVE":
        gaps.append("Independent source observations are present, but the supplied records do not establish a spatial-temporal match or validated disagreement.")
    elif comparison_status not in {"AGREEMENT", "DISAGREEMENT"}:
        gaps.append("A usable cross-sensor comparison is unavailable.")
    gaps.append("No ground-based verification record is attached to this event.")
    return gaps
