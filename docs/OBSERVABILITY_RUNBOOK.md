# BurnBlind — Observability & Operations Runbook

## 1. What to monitor

### Ingestion

- source availability
- records received
- records rejected
- processing latency

### SQS

- queue depth
- oldest message age
- failed messages
- DLQ count

### Lambda

- invocation count
- errors
- duration
- throttles

### API

- request count
- 4xx
- 5xx
- latency

### Agent

- investigation count
- tool failures
- model failures
- duration
- schema validation failures

## 2. Correlation

Every pipeline execution should carry:

```text
correlation_id
event_id
processing_version
```

## 3. Structured logs

Example:

```json
{
  "level": "INFO",
  "service": "score_event",
  "event_id": "evt_001",
  "correlation_id": "req_123",
  "status": "success",
  "duration_ms": 84
}
```

## 4. Incident response

### Queue growing

1. Check worker Lambda errors.
2. Check source volume.
3. Check throttling.
4. Inspect DLQ.
5. Pause ingestion if necessary.

### Agent failing

1. Keep event visible.
2. Mark investigation as unavailable/failed.
3. Inspect model/tool logs.
4. Retry only after root cause is understood.

### Data source unavailable

1. Do not fabricate data.
2. Mark source unavailable.
3. Lower confidence where appropriate.
4. Continue with available evidence.

## 5. Hackathon operational mode

For the demo:

- keep CloudWatch logs enabled
- keep a known-good fixture
- keep a known-good investigation
- keep a deterministic fallback path
- avoid depending on a live external API for every demo step

## 6. Key operational SLO-style targets

Set practical targets after the first benchmark rather than inventing unrealistic numbers.

Track:

- ingestion success rate
- processing success rate
- event processing latency
- investigation completion rate
- API p95 latency
- DLQ count
- source freshness

The first benchmark should establish the baseline used in the final write-up.
