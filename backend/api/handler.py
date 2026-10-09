"""AWS Lambda-compatible API Gateway HTTP API handler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import re
from typing import Any, Mapping
import uuid

from backend.api.repository import CandidateEventRepository, EventFilters, InvalidCursor
from backend.api.review_store import REVIEW_OUTCOMES
from backend.api.feature_views import action_center, map_layer
from backend.common.serialization import candidate_event_to_dict


_EVENT_ID = re.compile(r"^evt_[A-Fa-f0-9]{24}$")
_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}
_STATUSES = {
    "NEW", "CANDIDATE", "PRIORITIZED", "INVESTIGATION_QUEUED",
    "INVESTIGATING", "REVIEW_REQUIRED", "CONFIRMED", "DISMISSED",
}


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status_code: int
    body: Mapping[str, Any]
    headers: Mapping[str, str]

    def gateway_response(self) -> dict[str, Any]:
        return {
            "statusCode": self.status_code,
            "headers": dict(self.headers),
            "body": "" if self.status_code == 204 else json.dumps(self.body, separators=(",", ":"), allow_nan=False),
            "isBase64Encoded": False,
        }


def _parse_timestamp(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        west, south, east, north = (float(part.strip()) for part in value.split(","))
    except (ValueError, TypeError) as exc:
        raise ValueError("bbox must be west,south,east,north") from exc
    if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= 90 and -90 <= north <= 90):
        raise ValueError("bbox coordinates are outside valid ranges")
    if west > east or south > north:
        raise ValueError("bbox west/south must not exceed east/north")
    return west, south, east, north


def _parse_filters(query: Mapping[str, str]) -> tuple[EventFilters, int, str | None]:
    try:
        limit = int(query.get("limit", "20"))
    except ValueError as exc:
        raise ValueError("limit must be an integer") from exc
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    status = query.get("status")
    if status is not None and status not in _STATUSES:
        raise ValueError("status is not a supported event status")
    priority = query.get("priority")
    if priority is not None and priority.upper() not in _PRIORITIES:
        raise ValueError("priority must be LOW, MEDIUM, or HIGH")
    start = _parse_timestamp(query["start"], "start") if query.get("start") else None
    end = _parse_timestamp(query["end"], "end") if query.get("end") else None
    if start is not None and end is not None and start > end:
        raise ValueError("start must not be after end")
    filters = EventFilters(
        start=start,
        end=end,
        bbox=_parse_bbox(query.get("bbox")),
        status=status,
        priority=priority.upper() if priority else None,
    )
    return filters, limit, query.get("cursor")


def _event_payload(event, assessment: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = candidate_event_to_dict(event)
    payload.update(
        {
            "status": "CANDIDATE",
            "blindness_score": None,
            "fire_likelihood": None,
            "uncertainty": None,
            "priority_score": None,
                "provisional_priority_score": None,
                "priority_status": "UNAVAILABLE",
            "investigation_status": "NOT_AVAILABLE",
            "score_status": "AWAITING_REQUIRED_FEATURES",
        }
    )
    if assessment:
        payload.update(
            {
                "blindness_score": assessment.get("blindness_score"),
                "fire_likelihood": assessment.get("fire_likelihood_score"),
                "uncertainty": assessment.get("uncertainty"),
                "priority_score": assessment.get("priority_score"),
                "provisional_priority_score": assessment.get("provisional_priority_score"),
                "priority_status": assessment.get("priority_status", "UNAVAILABLE"),
                "score_status": "HEURISTIC_SCORES_AVAILABLE",
                "score_version": assessment.get("score_version"),
                "feature_version": assessment.get("feature_version"),
                "investigation_status": assessment.get("investigation_status", "NOT_REQUIRED"),
                "investigation_trigger_reasons": assessment.get("investigation_trigger_reasons", []),
            }
        )
    return payload


def _error(status: int, code: str, message: str) -> tuple[int, dict[str, Any]]:
    return status, {"error": {"code": code, "message": message}}


def _investigation_payload(event_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
    """Keep event identity and execution metadata outside the evidence report.

    The fallback reads legacy fields out of previously stored report objects so
    old completions follow the same API contract as new ones.
    """
    report = dict(record.get("report") or {})
    metadata = {}
    for field in ("event_id", "model_id", "agent_version", "prompt_version", "started_at_utc", "completed_at_utc", "confidence"):
        legacy_value = report.pop(field, None)
        metadata[field] = record.get(field) or legacy_value
    return {
        "event_id": event_id,
        "status": record.get("status", "UNKNOWN"),
        "investigation": report or None,
        "requested_at_utc": record.get("requested_at_utc"),
        "started_at_utc": metadata["started_at_utc"],
        "completed_at_utc": metadata["completed_at_utc"],
        "updated_at_utc": record.get("updated_at_utc") or metadata["completed_at_utc"] or record.get("requested_at_utc"),
        "model_id": metadata["model_id"],
        "agent_version": metadata["agent_version"],
        "prompt_version": metadata["prompt_version"],
        "error_code": record.get("error_code"),
        "trigger_reasons": record.get("trigger_reasons", []),
    }


def _public_latest_review(review_history: Any, event_id: str) -> dict[str, Any] | None:
    """Expose decision state in queue summaries without reviewer notes or identity."""
    reviews = review_history(event_id, limit=1) or []
    if not reviews:
        return None
    latest = reviews[0]
    return {key: latest[key] for key in ("outcome", "reviewed_at_utc") if key in latest}


def _review_allows_investigation(review_store: Any, event_id: str) -> bool:
    if review_store is None:
        return False
    reviews = review_store.list_for_event(event_id, limit=1)
    return bool(reviews and reviews[0].get("outcome") in {"CONFIRMED", "NEEDS_VERIFICATION"})


def handle_request(
    method: str,
    path: str,
    query: Mapping[str, str] | None,
    repository: CandidateEventRepository,
    request_id: str | None = None,
    body: str | None = None,
    origin: str | None = None,
    investigation_store: Any | None = None,
    investigation_launcher: Any | None = None,
    review_store: Any | None = None,
    evidence_reader: Any | None = None,
    reviewer_id: str | None = None,
    environmental_launcher: Any | None = None,
) -> ApiResponse:
    query = query or {}
    correlation_id = request_id or str(uuid.uuid4())
    route = path.rstrip("/") or "/"
    if route.startswith("/api/"):
        route = route[4:]
    configured_origins = [
        value.strip()
        for value in os.environ.get(
            "CORS_ALLOW_ORIGINS",
            os.environ.get("CORS_ALLOW_ORIGIN", "http://localhost:5173"),
        ).split(",")
        if value.strip()
    ]
    allowed_origins = set(configured_origins)
    default_origin = configured_origins[0] if configured_origins else "http://localhost:5173"
    allow_origin = origin if origin in allowed_origins else default_origin
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Correlation-Id",
        "X-Correlation-Id": correlation_id,
    }

    if method == "OPTIONS":
        return ApiResponse(204, {}, headers)
    if body is not None and len(body.encode("utf-8")) > 4096:
        status, response = _error(413, "REQUEST_TOO_LARGE", "Request body exceeds the 4 KB limit.")
    elif method == "GET" and route == "/health":
        status, response = 200, {"status": "ok", "data_mode": "HISTORICAL_REPLAY"}
    elif method == "GET" and route == "/summary":
        events = repository.all()
        newest = max((event.detected_at_utc for event in events), default=None)
        status, response = 200, {
            "active_events": 0,
            "candidate_events": len(events),
            "scored_events": 0,
            "high_priority": 0,
            "investigating": 0,
            "data_mode": "HISTORICAL_REPLAY",
            "last_updated": newest.isoformat().replace("+00:00", "Z") if newest else None,
        }
    elif method == "GET" and route == "/action-center":
        try:
            limit = int(query.get("limit", "50"))
            if not 1 <= limit <= 100:
                raise ValueError
            response = action_center(repository, limit, query.get("cursor"))
            status = 200
        except (TypeError, ValueError, InvalidCursor):
            status, response = _error(400, "INVALID_QUERY", "limit must be from 1 to 100 and cursor must be valid.")
    elif method == "GET" and route == "/map-layers":
        try:
            limit = int(query.get("limit", "100"))
            if not 1 <= limit <= 100:
                raise ValueError
            response = map_layer(repository, query.get("layer", ""), limit, evidence_reader)
            status = 200
        except ValueError as exc:
            status, response = _error(400, "INVALID_QUERY", str(exc) or "limit must be from 1 to 100.")
    elif method == "GET" and route == "/events":
        try:
            filters, limit, cursor = _parse_filters(query)
            events, next_cursor = repository.list(filters, limit, cursor)
            status, response = 200, {
                "items": [_event_payload(event) for event in events],
                "next_cursor": next_cursor,
                "data_mode": "HISTORICAL_REPLAY",
            }
        except InvalidCursor as exc:
            status, response = _error(400, "INVALID_CURSOR", str(exc))
        except ValueError as exc:
            status, response = _error(400, "INVALID_QUERY", str(exc))
    elif method == "GET" and route == "/replay":
        try:
            replay_at = _parse_timestamp(query.get("at", ""), "at")
            limit = int(query.get("limit", "50"))
            if not 1 <= limit <= 100:
                raise ValueError
            filters = EventFilters(end=replay_at)
            events, next_cursor = repository.list(filters, limit, query.get("cursor"))
            status, response = 200, {
                "at_utc": replay_at.isoformat().replace("+00:00", "Z"),
                "data_mode": "HISTORICAL_REPLAY",
                "items": [_event_payload(event) for event in events],
                "next_cursor": next_cursor,
            }
        except (TypeError, ValueError, InvalidCursor) as exc:
            message = str(exc) if isinstance(exc, InvalidCursor) else "at must be ISO-8601 and limit must be from 1 to 100."
            status, response = _error(400, "INVALID_QUERY", message)
    elif method == "GET" and route == "/investigations":
        if investigation_store is None:
            status, response = _error(503, "INVESTIGATION_STORE_UNAVAILABLE", "Investigation records are not configured.")
        else:
            try:
                limit = int(query.get("limit", "50"))
                if not 1 <= limit <= 100:
                    raise ValueError
                records, next_cursor = investigation_store.list(limit, query.get("cursor"))
                review_history = getattr(review_store, "list_for_event", None)
                status, response = 200, {
                    "items": [
                        {
                            **_investigation_payload(str(item.get("event_id", "")), item),
                            "latest_review": _public_latest_review(review_history, str(item["event_id"]))
                            if review_history and item.get("event_id") else None,
                        }
                        for item in records
                    ],
                    "next_cursor": next_cursor,
                }
            except (TypeError, ValueError):
                status, response = _error(400, "INVALID_QUERY", "limit must be an integer from 1 to 100.")
    elif route.startswith("/events/"):
        parts = route.split("/")
        if len(parts) not in (3, 4) or not _EVENT_ID.fullmatch(parts[2]):
            status, response = _error(400, "INVALID_EVENT_ID", "Event ID is malformed.")
        else:
            event = repository.get(parts[2])
            if event is None:
                status, response = _error(404, "EVENT_NOT_FOUND", "Event does not exist.")
            elif len(parts) == 3 and method == "GET":
                get_assessment = getattr(repository, "get_scoring_context", None)
                assessment = get_assessment(event.event_id) if get_assessment else None
                status, response = 200, _event_payload(event, assessment)
            elif len(parts) == 4 and parts[3] == "investigation" and method == "GET":
                record = investigation_store.get(event.event_id) if investigation_store else None
                if record:
                    status, response = 200, _investigation_payload(event.event_id, record)
                else:
                    status, response = 200, {
                        "event_id": event.event_id,
                        "status": "NOT_REQUESTED",
                        "investigation": None,
                        "reason": "No investigation has been requested for this historical candidate.",
                    }
            elif len(parts) == 4 and parts[3] == "investigate" and method == "POST":
                if not reviewer_id:
                    status, response = _error(401, "REVIEWER_AUTH_REQUIRED", "Sign in with an authorized reviewer account to request an investigation.")
                elif not _review_allows_investigation(review_store, event.event_id):
                    status, response = _error(409, "REVIEW_REQUIRED", "A reviewer must confirm or request verification before investigation.")
                elif investigation_launcher is None:
                    status, response = _error(
                        409,
                        "INVESTIGATION_NOT_READY",
                        "Investigation queue is not configured for this API instance.",
                    )
                else:
                    try:
                        record, created = investigation_launcher.enqueue(event, correlation_id)
                        status, response = 202, {
                            "event_id": event.event_id,
                            "status": record.get("status", "QUEUED"),
                            "already_requested": not created,
                        }
                    except Exception:
                        status, response = _error(503, "INVESTIGATION_QUEUE_UNAVAILABLE", "The investigation request could not be queued. Try again later.")
            elif len(parts) == 4 and parts[3] == "review" and method == "GET":
                if review_store is None:
                    status, response = _error(503, "REVIEW_STORE_UNAVAILABLE", "Human review storage is not configured.")
                else:
                    reviews = review_store.list_for_event(event.event_id)
                    if not reviewer_id:
                        reviews = [
                            {key: item[key] for key in ("outcome", "reviewed_at_utc") if key in item}
                            for item in reviews
                        ]
                    status, response = 200, {"event_id": event.event_id, "items": reviews}
            elif len(parts) == 4 and parts[3] == "review" and method == "POST":
                if not reviewer_id:
                    status, response = _error(401, "REVIEWER_AUTH_REQUIRED", "Sign in with an authorized reviewer account to record an outcome.")
                elif review_store is None:
                    status, response = _error(503, "REVIEW_STORE_UNAVAILABLE", "Human review storage is not configured.")
                else:
                    try:
                        payload = json.loads(body or "")
                    except json.JSONDecodeError:
                        payload = None
                    if not isinstance(payload, dict) or set(payload) - {"outcome", "notes"}:
                        status, response = _error(400, "INVALID_REVIEW", "Provide an outcome and optional notes.")
                    elif payload.get("outcome") not in REVIEW_OUTCOMES:
                        status, response = _error(400, "INVALID_REVIEW", "outcome is not a supported human review outcome.")
                    elif not isinstance(payload.get("notes", ""), str) or len(payload.get("notes", "")) > 1000:
                        status, response = _error(400, "INVALID_REVIEW", "notes must be text of at most 1000 characters.")
                    else:
                        saved = review_store.record(event.event_id, payload["outcome"], payload.get("notes", "").strip(), correlation_id, reviewer_id)
                        status, response = 201, {"event_id": event.event_id, "review": saved}
            elif len(parts) == 4 and parts[3] in {"sensor-comparison", "exposure"} and method == "GET":
                context_reader = getattr(repository, "get_feature_context", None)
                context = context_reader(event.event_id) if context_reader else None
                key = "SENSOR_COMPARISON" if parts[3] == "sensor-comparison" else "POPULATION_EXPOSURE_ESTIMATE"
                value = evidence_reader.get_latest_derived(event.event_id, key) if evidence_reader else None
                if value is None:
                    context_key = "sensor_comparison" if parts[3] == "sensor-comparison" else "exposure"
                    value = (context or {}).get(context_key)
                available = bool(value) and value.get("status") in {
                    "AGREEMENT", "DISAGREEMENT", "INCONCLUSIVE", "OK", "ESTIMATED",
                }
                status, response = 200, {
                    "event_id": event.event_id,
                    "status": "AVAILABLE" if available else "UNAVAILABLE",
                    "result": value,
                    "reason": None if available else (value or {}).get("detail") or f"No sourced {key.replace('_', ' ')} record is attached to this event.",
                }
            elif len(parts) == 4 and parts[3] == "environmental-analysis" and method == "GET":
                context_reader = getattr(repository, "get_feature_context", None)
                context = context_reader(event.event_id) if context_reader else None
                value = (context or {}).get("environmental_analysis")
                status, response = 200, {"event_id": event.event_id, "status": (value or {}).get("status", "NOT_RUN"), "result": context}
            elif len(parts) == 4 and parts[3] == "environmental-analysis" and method == "POST":
                if not reviewer_id:
                    status, response = _error(401, "REVIEWER_AUTH_REQUIRED", "Sign in with an authorized reviewer account to request environmental analysis.")
                elif environmental_launcher is None:
                    status, response = _error(503, "ENVIRONMENTAL_ANALYSIS_UNAVAILABLE", "Environmental analysis is not configured for this API instance.")
                else:
                    try:
                        result = environmental_launcher.enqueue(event.event_id, correlation_id)
                        status, response = 202, result
                    except Exception:
                        status, response = _error(503, "ENVIRONMENTAL_ANALYSIS_QUEUE_UNAVAILABLE", "Environmental analysis could not be queued. Try again later.")
            else:
                status, response = _error(405, "METHOD_NOT_ALLOWED", "Method is not allowed for this resource.")
    else:
        status, response = _error(404, "ROUTE_NOT_FOUND", "Route does not exist.")

    response["correlation_id"] = correlation_id
    if status == 204:
        response = {}
    return ApiResponse(status, response, headers)


def lambda_handler(event: Mapping[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point backed by the configured DynamoDB event table."""
    repository = _dynamo_repository_from_environment()
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    method = http.get("method") or event.get("httpMethod", "GET")
    path = event.get("rawPath") or event.get("path", "/")
    stage = request_context.get("stage")
    if stage and stage != "$default":
        stage_prefix = f"/{stage}"
        if path == stage_prefix:
            path = "/"
        elif path.startswith(f"{stage_prefix}/"):
            path = path[len(stage_prefix):]
    query = event.get("queryStringParameters") or {}
    request_id = request_context.get("requestId")
    headers = event.get("headers") or {}
    origin = headers.get("origin") or headers.get("Origin")
    investigation_store, investigation_launcher = _investigation_services_from_environment()
    review_store = _review_store_from_environment()
    evidence_reader = _evidence_reader_from_environment()
    environmental_launcher = _environmental_launcher_from_environment(repository)
    authorizer = request_context.get("authorizer") or {}
    jwt = authorizer.get("jwt") or {}
    claims = jwt.get("claims") or {}
    reviewer_id = claims.get("sub") if isinstance(claims, Mapping) else None
    response = handle_request(
        method, path, query, repository, request_id, event.get("body"), origin,
        investigation_store, investigation_launcher, review_store, evidence_reader, reviewer_id,
        environmental_launcher,
    )
    return response.gateway_response()


def _dynamo_repository_from_environment() -> CandidateEventRepository:
    table_name = os.environ.get("EVENT_TABLE")
    if not table_name:
        raise RuntimeError("EVENT_TABLE is not configured")
    from backend.api.dynamodb_repository import DynamoCandidateEventRepository

    return DynamoCandidateEventRepository(table_name)


def _investigation_services_from_environment():
    table_name = os.environ.get("INVESTIGATION_TABLE")
    queue_url = os.environ.get("INVESTIGATION_QUEUE_URL")
    if not table_name or not queue_url:
        return None, None
    import boto3

    from backend.agent.storage import DynamoInvestigationStore, SqsInvestigationLauncher

    store = DynamoInvestigationStore(boto3.resource("dynamodb").Table(table_name))
    launcher = SqsInvestigationLauncher(store, queue_url, boto3.client("sqs"))
    return store, launcher


def _review_store_from_environment():
    table_name = os.environ.get("REVIEW_OUTCOME_TABLE")
    if not table_name:
        return None
    import boto3

    from backend.api.review_store import DynamoReviewOutcomeStore

    return DynamoReviewOutcomeStore(boto3.resource("dynamodb").Table(table_name))


def _evidence_reader_from_environment():
    table_name = os.environ.get("EVIDENCE_TABLE")
    if not table_name:
        return None
    import boto3

    from backend.agent.evidence import DynamoEvidenceRepository

    return DynamoEvidenceRepository(table_name, boto3.resource("dynamodb").Table(table_name))


def _environmental_launcher_from_environment(repository):
    queue_url = os.environ.get("ENVIRONMENTAL_ANALYSIS_QUEUE_URL")
    if not queue_url:
        return None
    import boto3

    from backend.features.environmental import EnvironmentalAnalysisLauncher

    return EnvironmentalAnalysisLauncher(repository, queue_url, boto3.client("sqs"))
