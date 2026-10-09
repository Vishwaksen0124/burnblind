from backend.features.trigger import insert_event_ids


def test_environmental_trigger_selects_only_new_events():
    event = {
        "Records": [
            {
                "eventName": "MODIFY",
                "dynamodb": {"NewImage": {"event_id": {"S": "evt_modified"}}},
            },
            {
                "eventName": "INSERT",
                "dynamodb": {"NewImage": {"event_id": {"S": "evt_new"}}},
            },
            {"eventName": "INSERT", "dynamodb": {"NewImage": {}}},
        ]
    }

    assert insert_event_ids(event) == ["evt_new"]