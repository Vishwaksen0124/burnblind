# BurnBlind — API Specification

## Base

`/api`

## GET /health

Returns service health and active dataset mode.

```json
{
  "status": "ok",
  "data_mode": "HISTORICAL_REPLAY",
  "correlation_id": "..."
}
```

## GET /summary

Returns replay summary. Counts describe loaded candidate clusters, not active
fires or validated incidents. Scores and priorities are unavailable until
required deterministic features are populated.

```json
{
  "active_events": 0,
  "candidate_events": 250,
  "scored_events": 0,
  "high_priority": 0,
  "investigating": 0,
  "data_mode": "HISTORICAL_REPLAY",
  "last_updated": "...",
  "correlation_id": "..."
}
```

## GET /events

Query parameters:

```text
priority
status
start
end
bbox
limit
cursor
```

Response:

```json
{
  "items": [],
  "next_cursor": null
}
```

## GET /events/{event_id}

Returns the candidate cluster and source evidence identifiers. Replay items
include null scores and `score_status: AWAITING_REQUIRED_FEATURES`.

## GET /events/{event_id}/investigation

Returns latest investigation if available.

## POST /events/{event_id}/investigate

Returns `409 INVESTIGATION_NOT_READY` while score inputs and trigger policy
are unavailable. No investigation job is queued in the current replay API.

Response:

```json
{
  "error": {
    "code": "INVESTIGATION_NOT_READY",
    "message": "Investigation can be queued after deterministic scores and trigger policy are available."
  },
  "correlation_id": "..."
}
```

## Error format

```json
{
  "error": {
    "code": "EVENT_NOT_FOUND",
    "message": "Event does not exist."
  }
}
```

## API principles

- validate inputs
- use stable schemas
- never expose secrets
- use correlation IDs
- return deterministic error codes
- keep agent internals private

## 7. Public API protection

For the hackathon demo:

- validate query parameters
- cap pagination/page size
- apply API Gateway throttling where appropriate
- reject oversized requests
- expose read-only event APIs publicly where possible
- keep mutation endpoints restricted to required operations

Authentication is optional for the MVP, but public mutation endpoints must not allow arbitrary event updates.
