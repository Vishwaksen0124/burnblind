from datetime import datetime, timezone
import json

from backend.api.handler import handle_request
from backend.api.repository import EventFilters, MemoryCandidateEventRepository
from backend.common.models import CandidateEvent


def event(event_id, day, lat=30.9, lon=75.85):
    timestamp = datetime(2025, 10, day, 7, 0, tzinfo=timezone.utc)
    return CandidateEvent(
        event_id=event_id,
        grid_id="grid-v1-utm43n-5000m-1-1",
        detected_at_utc=timestamp,
        last_observed_at_utc=timestamp,
        latitude=lat,
        longitude=lon,
        detection_count=2,
        sources=("GK2A_AMI",),
        evidence_ids=(f"obs_{day}_1", f"obs_{day}_2"),
        data_mode="HISTORICAL_REPLAY",
        processing_version="candidate-events-v1",
    )


def repository():
    return MemoryCandidateEventRepository(
        [
            event("evt_000000000000000000000001", 1),
            event("evt_000000000000000000000002", 2, lat=29.7),
            event("evt_000000000000000000000003", 3),
        ]
    )


def test_health_response_includes_correlation_id_and_replay_mode():
    response = handle_request("GET", "/api/health", {}, repository(), "request-123")

    assert response.status_code == 200
    assert response.body["status"] == "ok"
    assert response.body["data_mode"] == "HISTORICAL_REPLAY"
    assert response.body["correlation_id"] == "request-123"


def test_events_filters_and_cursor_are_stable():
    first = handle_request("GET", "/api/events", {"limit": "1"}, repository())
    first_id = first.body["items"][0]["event_id"]
    cursor = first.body["next_cursor"]
    second = handle_request("GET", "/api/events", {"limit": "1", "cursor": cursor}, repository())

    assert first.status_code == second.status_code == 200
    assert first_id != second.body["items"][0]["event_id"]
    assert first.body["data_mode"] == "HISTORICAL_REPLAY"
    assert second.body["items"][0]["priority_score"] is None


def test_events_rejects_invalid_query_and_filter_specific_cursor():
    bad_limit = handle_request("GET", "/api/events", {"limit": "500"}, repository())
    cursor = repository().list(EventFilters(), 1, None)[1]
    changed_filter = handle_request("GET", "/api/events", {"limit": "1", "status": "CANDIDATE", "cursor": cursor}, repository())

    assert bad_limit.status_code == 400
    assert bad_limit.body["error"]["code"] == "INVALID_QUERY"
    assert changed_filter.status_code == 400
    assert changed_filter.body["error"]["code"] == "INVALID_CURSOR"


def test_event_detail_and_investigation_are_grounded_in_available_state():
    event_id = "evt_000000000000000000000001"
    detail = handle_request("GET", f"/api/events/{event_id}", {}, repository())
    investigation = handle_request("GET", f"/api/events/{event_id}/investigation", {}, repository())
    queue = handle_request("POST", f"/api/events/{event_id}/investigate", {}, repository())

    assert detail.status_code == 200
    assert detail.body["score_status"] == "AWAITING_REQUIRED_FEATURES"
    assert investigation.body["investigation"] is None
    assert queue.status_code == 409
    assert queue.body["error"]["code"] == "INVESTIGATION_NOT_READY"


def test_investigation_queue_returns_accepted_and_current_status():
    class Launcher:
        def enqueue(self, candidate, request_id):
            assert candidate.event_id == "evt_000000000000000000000001"
            assert request_id == "request-456"
            return {"status": "QUEUED"}, True

    class Store:
        def get(self, event_id):
            return {
                "status": "COMPLETED",
                "report": {"classification": "REVIEW_REQUIRED"},
                "requested_at_utc": "2025-10-01T07:00:00Z",
                "completed_at_utc": "2025-10-01T07:00:03Z",
            }

    event_id = "evt_000000000000000000000001"
    queued = handle_request(
        "POST", f"/events/{event_id}/investigate", {}, repository(), "request-456",
        investigation_launcher=Launcher(),
    )
    current = handle_request(
        "GET", f"/events/{event_id}/investigation", {}, repository(),
        investigation_store=Store(),
    )

    assert queued.status_code == 202
    assert queued.body["status"] == "QUEUED"
    assert current.body["status"] == "COMPLETED"
    assert current.body["investigation"]["classification"] == "REVIEW_REQUIRED"


def test_unknown_events_and_malformed_ids_return_structured_errors():
    missing = handle_request("GET", "/api/events/evt_000000000000000000000099", {}, repository())
    malformed = handle_request("GET", "/api/events/not-an-id", {}, repository())

    assert missing.status_code == 404
    assert missing.body["error"]["code"] == "EVENT_NOT_FOUND"
    assert malformed.status_code == 400
    assert malformed.body["error"]["code"] == "INVALID_EVENT_ID"


def test_review_outcomes_are_validated_and_persisted():
    class ReviewStore:
        items = []

        def record(self, event_id, outcome, notes, request_id):
            saved = {"event_id": event_id, "outcome": outcome, "notes": notes, "request_id": request_id}
            self.items.append(saved)
            return saved

        def list_for_event(self, event_id):
            return [item for item in self.items if item["event_id"] == event_id]

    store = ReviewStore()
    event_id = "evt_000000000000000000000001"
    saved = handle_request(
        "POST", f"/events/{event_id}/review", {}, repository(), "review-request",
        body=json.dumps({"outcome": "NEEDS_VERIFICATION", "notes": "Compare a later pass."}),
        review_store=store,
    )
    listed = handle_request("GET", f"/events/{event_id}/review", {}, repository(), review_store=store)
    invalid = handle_request(
        "POST", f"/events/{event_id}/review", {}, repository(),
        body=json.dumps({"outcome": "EVACUATE"}), review_store=store,
    )

    assert saved.status_code == 201
    assert listed.body["items"][0]["outcome"] == "NEEDS_VERIFICATION"
    assert invalid.status_code == 400


def test_replay_endpoint_respects_requested_historical_time():
    response = handle_request("GET", "/replay", {"at": "2025-10-02T12:00:00Z", "limit": "10"}, repository())

    assert response.status_code == 200
    assert response.body["data_mode"] == "HISTORICAL_REPLAY"
    assert all(item["detected_at_utc"] <= response.body["at_utc"] for item in response.body["items"])


def test_action_center_and_map_layers_report_missing_inputs_without_inventing_data():
    action = handle_request("GET", "/action-center", {"limit": "3"}, repository())
    blindness = handle_request("GET", "/map-layers", {"layer": "blind-spots"}, repository())
    comparison = handle_request("GET", "/map-layers", {"layer": "sensor-disagreement"}, repository())

    assert action.status_code == 200
    assert action.body["counts"]["MORE_EVIDENCE_NEEDED"] == 3
    assert blindness.body["status"] == "UNAVAILABLE"
    assert blindness.body["items"] == []
    assert "coverage" in blindness.body["reason"]
    assert comparison.body["status"] == "UNAVAILABLE"


def test_event_feature_routes_explicitly_report_unavailable_data():
    event_id = "evt_000000000000000000000001"
    response = handle_request("GET", f"/events/{event_id}/exposure", {}, repository())

    assert response.status_code == 200
    assert response.body["status"] == "UNAVAILABLE"
    assert response.body["result"] is None
