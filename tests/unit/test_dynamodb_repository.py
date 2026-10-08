from datetime import datetime, timezone

from backend.api.dynamodb_repository import DynamoCandidateEventRepository
from backend.api.repository import EventFilters
from backend.common.models import CandidateEvent
from backend.common.serialization import candidate_event_to_dict


def make_event(event_id, day, latitude=30.9):
    timestamp = datetime(2025, 10, day, 7, tzinfo=timezone.utc)
    event = CandidateEvent(
        event_id=event_id,
        grid_id="grid-v1-utm43n-5000m-1-1",
        detected_at_utc=timestamp,
        last_observed_at_utc=timestamp,
        latitude=latitude,
        longitude=75.85,
        detection_count=1,
        sources=("GK2A_AMI",),
        evidence_ids=(f"obs_{day}",),
        data_mode="HISTORICAL_REPLAY",
        processing_version="candidate-events-v1",
    )
    item = candidate_event_to_dict(event)
    item["data_mode"] = event.data_mode
    return event, item


class FakeTable:
    def __init__(self, items):
        self.items = items
        self.query_calls = []

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        start_key = kwargs.get("ExclusiveStartKey")
        start_index = 0
        if start_key:
            start_index = next(
                index + 1 for index, item in enumerate(self.items)
                if item["event_id"] == start_key["event_id"]
            )
        items = self.items[start_index : start_index + kwargs["Limit"]]
        response = {"Items": items}
        if start_index + len(items) < len(self.items):
            response["LastEvaluatedKey"] = {"event_id": items[-1]["event_id"]}
        return response

    def get_item(self, **kwargs):
        item = next((item for item in self.items if item["event_id"] == kwargs["Key"]["event_id"]), None)
        return {"Item": item} if item else {}


def test_dynamo_repository_uses_index_and_cursor_without_duplicate_pages():
    events = [make_event(f"evt_{index:024x}", index + 1) for index in range(3)]
    table = FakeTable([item for _, item in events])
    repository = DynamoCandidateEventRepository("Events", table=table)

    first, cursor = repository.list(EventFilters(), 1, None)
    second, next_cursor = repository.list(EventFilters(), 1, cursor)

    assert first[0].event_id == events[0][0].event_id
    assert second[0].event_id == events[1][0].event_id
    assert first[0].event_id != second[0].event_id
    assert next_cursor is not None
    assert table.query_calls[0]["IndexName"] == "data-mode-detected-at"


def test_dynamo_repository_applies_timestamp_and_bbox_filters():
    events = [make_event("evt_000000000000000000000001", 1, latitude=30.9), make_event("evt_000000000000000000000002", 2, latitude=27.5)]
    table = FakeTable([item for _, item in events])
    repository = DynamoCandidateEventRepository("Events", table=table)
    filters = EventFilters(
        start=datetime(2025, 10, 1, tzinfo=timezone.utc),
        end=datetime(2025, 10, 2, 23, tzinfo=timezone.utc),
        bbox=(73, 29, 78, 32),
    )

    results, cursor = repository.list(filters, 10, None)

    assert [item.event_id for item in results] == [events[0][0].event_id]
    assert cursor is None
    assert "BETWEEN" in table.query_calls[0]["KeyConditionExpression"]


def test_dynamo_repository_reads_event_detail():
    event, item = make_event("evt_000000000000000000000001", 1)
    repository = DynamoCandidateEventRepository("Events", table=FakeTable([item]))

    assert repository.get(event.event_id) == event
