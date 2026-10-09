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

## Environmental analysis

New events are automatically queued for environmental analysis. The
`POST /events/{event_id}/environmental-analysis` route requires the reviewer
JWT and is an idempotent retry/reprocess action. It enqueues deterministic
weather, historical-context, exposure, coverage, and sensor-comparison
enrichment. It does not calculate core scores or invoke the Investigation
Agent.
The request returns `202` with `status: PROCESSING`; poll the read endpoint for
completion:

```text
GET /events/{event_id}/environmental-analysis
GET /events/{event_id}/exposure
GET /events/{event_id}/sensor-comparison
GET /map-layers?layer=exposure
```

Event-time wind comes from Open-Meteo ERA5. Population estimates use WorldPop
Global2 within a documented directional screening corridor. Blind-spot values
remain unavailable unless valid sensor coverage and quality inputs are
attached. Missing second-sensor data is never interpreted as a non-detection.

## POST /events/{event_id}/investigate

Explicitly requests an analyst override investigation for an existing
candidate. It returns `202` with the queue status. A completed investigation
is deduplicated for that event; failed work can be retried. Scoring
qualification is recorded first; a reviewer explicitly decides whether to
request the investigation.

```json
{
  "event_id": "evt_...",
  "status": "QUEUED",
  "already_requested": false,
  "correlation_id": "..."
}
```

`GET /events/{event_id}/investigation` returns `NOT_REQUESTED`, `QUEUED`,
`RUNNING`, `COMPLETED`, or `FAILED`. Completed reports include citations to
source observation IDs; model confidence is intentionally null. Investigations
are advisory and require human review.

## Automatic qualification

When an event record receives normalized `score_features`, the stream worker
applies `config/scoring.v1.json`. A record with no usable evidence does not
qualify from missingness alone. The worker stores the score snapshot, policy
version, and trigger reasons with the investigation. The feature producer is
responsible for writing validated feature inputs; candidate rows without them
remain unassessed and are not auto-enqueued.

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

Event, investigation, and replay reads remain public. These two mutation routes
require a Cognito access token accepted by the API Gateway `ReviewerJwt`
authorizer and the `aws.cognito.signin.user.admin` scope:

- `POST /events/{event_id}/investigate`
- `POST /events/{event_id}/review`
- `POST /events/{event_id}/environmental-analysis`

The deployed HTTP API registers both the `/api/...` browser paths and the
unprefixed route forms above so the public proxy route cannot bypass JWT
validation. Environmental analysis is delivered through its own FIFO queue and
Lambda with no model invocation permissions.

Anonymous requests receive `401`; reviewer accounts are administrator-created
and public self-registration is disabled. The API Lambda also requires the
validated JWT subject before processing either write. Store that subject with
human review outcomes as the reviewer identifier. Pool and app-client IDs are
public frontend configuration; passwords and tokens are never stored in source
control. See `docs/SECURITY.md` and `docs/DEPLOYMENT.md` for provisioning.
