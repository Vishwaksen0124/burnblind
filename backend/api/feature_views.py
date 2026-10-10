"""Small, read-only API projections for action ranking and map overlays."""

from __future__ import annotations

from typing import Any

from backend.common.serialization import candidate_event_to_dict


LAYER_FIELDS = {
    "blind-spots": "blind_spot",
    "sensor-disagreement": "sensor_comparison",
    "exposure": "exposure",
}


def action_center(repository: Any, limit: int, cursor: str | None) -> dict[str, Any]:
    events, next_cursor = repository.list(_empty_filters(), limit, cursor)
    score_reader = getattr(repository, "get_scoring_context", None)
    batch_score_reader = getattr(repository, "get_scoring_contexts", None)
    assessments = batch_score_reader([event.event_id for event in events]) if batch_score_reader else {}
    entries = []
    for event in events:
        assessment = assessments.get(event.event_id) if batch_score_reader else score_reader(event.event_id) if score_reader else None
        reasons = list((assessment or {}).get("investigation_trigger_reasons", []))
        if reasons:
            bucket = "REQUIRES_REVIEW"
        elif (assessment or {}).get("priority_score") is not None:
            bucket = "LOW_PRIORITY"
        else:
            bucket = "MORE_EVIDENCE_NEEDED"
        entries.append({
            "event": _event_payload(event, assessment),
            "bucket": bucket,
            "trigger_reasons": reasons,
        })
    order = {"REQUIRES_REVIEW": 0, "MORE_EVIDENCE_NEEDED": 1, "LOW_PRIORITY": 2}
    entries.sort(key=lambda item: (order[item["bucket"]], -(item["event"].get("priority_score") or item["event"].get("provisional_priority_score") or 0), item["event"]["detected_at_utc"]))
    return {
        "items": entries,
        "counts": {bucket: sum(item["bucket"] == bucket for item in entries) for bucket in order},
        "next_cursor": next_cursor,
        "data_mode": "HISTORICAL_REPLAY",
    }


def map_layer(repository: Any, layer: str, limit: int, evidence_reader: Any | None = None) -> dict[str, Any]:
    if layer not in LAYER_FIELDS:
        raise ValueError("layer must be blind-spots, sensor-disagreement, or exposure")
    events, _ = repository.list(_empty_filters(), limit, None)
    context_reader = getattr(repository, "get_feature_context", None)
    batch_context_reader = getattr(repository, "get_feature_contexts", None)
    feature_contexts = batch_context_reader([event.event_id for event in events]) if batch_context_reader else None
    field = LAYER_FIELDS[layer]
    items = []
    for event in events:
        context = (
            feature_contexts.get(event.event_id) if feature_contexts is not None
            else context_reader(event.event_id) if context_reader else None
        )
        value = (context or {}).get(field)
        # Event projections can contain stale UNAVAILABLE placeholders while
        # source-derived evidence is stored independently in the evidence table.
        # Prefer the projection only when it contains a usable feature.
        if layer == "sensor-disagreement":
            usable = isinstance(value, dict) and value.get("status") in {
                "AGREEMENT", "DISAGREEMENT", "INCONCLUSIVE",
            }
            if evidence_reader and not usable:
                value = evidence_reader.get_latest_derived(event.event_id, "SENSOR_COMPARISON")
        elif layer == "exposure":
            usable = isinstance(value, dict) and value.get("status") in {"OK", "ESTIMATED"}
            if evidence_reader and not usable:
                value = evidence_reader.get_latest_derived(event.event_id, "POPULATION_EXPOSURE_ESTIMATE")
        if not value and layer == "sensor-disagreement":
            value = (context or {}).get("sensor_comparison")
        elif not value and layer == "exposure":
            value = (context or {}).get("exposure")
        if not isinstance(value, dict):
            continue
        if layer == "blind-spots" and value.get("score") is None:
            continue
        if layer == "blind-spots" and value.get("status") != "AVAILABLE":
            continue
        if layer == "sensor-disagreement" and value.get("status") not in {"AGREEMENT", "DISAGREEMENT", "INCONCLUSIVE"}:
            continue
        if layer == "exposure" and value.get("status") not in {"OK", "ESTIMATED"}:
            continue
        if layer == "exposure" and value.get("status") == "OK":
            value = {**value, "status": "ESTIMATED"}
        items.append({
            "event_id": event.event_id,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "detected_at_utc": event.detected_at_utc.isoformat().replace("+00:00", "Z"),
            "value": value,
        })
    reason = {
        "blind-spots": "No event-scoped observation coverage and quality measurements are attached to this replay.",
        "sensor-disagreement": "No explicit, spatially and temporally matched sensor comparison is attached to this replay.",
        "exposure": "No sourced population estimate and impact corridor are attached to this replay.",
    }[layer]
    status = "AVAILABLE" if items else "UNAVAILABLE"
    return {"layer": layer, "status": status, "reason": None if items else reason, "items": items, "data_mode": "HISTORICAL_REPLAY"}


def _empty_filters():
    from backend.api.repository import EventFilters

    return EventFilters()


def _event_payload(event, assessment):
    payload = candidate_event_to_dict(event)
    payload.update({
        "blindness_score": (assessment or {}).get("blindness_score"),
        "fire_likelihood": (assessment or {}).get("fire_likelihood_score"),
        "uncertainty": (assessment or {}).get("uncertainty"),
        "priority_score": (assessment or {}).get("priority_score"),
        "provisional_priority_score": (assessment or {}).get("provisional_priority_score"),
        "priority_status": (assessment or {}).get("priority_status", "UNAVAILABLE"),
        "score_version": (assessment or {}).get("score_version"),
        "score_status": "HEURISTIC_SCORES_AVAILABLE" if assessment else "AWAITING_REQUIRED_FEATURES",
    })
    return payload
