"""Process reviewer-requested environmental enrichment jobs from SQS."""

from __future__ import annotations

from typing import Any, Mapping
import os
import json
from datetime import datetime, timezone

from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.agent.evidence import DynamoEvidenceRepository
from backend.features.environmental import EnvironmentalAnalysisService


def lambda_handler(event: Mapping[str, Any], context: Any) -> dict[str, Any]:
    """Process queued event-scoped enrichment; never invokes the model."""
    events = DynamoCandidateEventRepository(os.environ["EVENT_TABLE"])
    evidence = DynamoEvidenceRepository(os.environ["EVIDENCE_TABLE"])
    service = EnvironmentalAnalysisService(events, evidence)
    failures = []
    for record in event.get("Records", []):
        event_id = None
        try:
            payload = json.loads(record.get("body", "{}"))
            event_id = str(payload["event_id"])
            result = service.analyze(event_id)
            print(json.dumps({
                "level": "INFO", "component": "environmental-analysis", "event_id": event_id,
                "status": result.get("environmental_analysis", {}).get("status", result.get("status")),
                "exposure_status": result.get("exposure", {}).get("status"),
                "comparison_status": result.get("sensor_comparison", {}).get("status"),
                "blind_spot_status": result.get("blind_spot", {}).get("status"),
            }, separators=(",", ":")))
            if result.get("status") == "NOT_FOUND":
                failures.append({"itemIdentifier": record.get("messageId")})
        except Exception as exc:
            print(json.dumps({
                "level": "ERROR", "component": "environmental-analysis",
                "event_id": event_id, "error": type(exc).__name__,
            }, separators=(",", ":")))
            if event_id:
                try:
                    events.put_feature_context(event_id, {"environmental_analysis": {
                        "status": "FAILED",
                        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "detail": f"Environmental worker failed ({type(exc).__name__}).",
                    }})
                except Exception:
                    pass
            failures.append({"itemIdentifier": record.get("messageId")})
    return {"batchItemFailures": failures}
