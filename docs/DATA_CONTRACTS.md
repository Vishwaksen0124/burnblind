# BurnBlind — Data Contracts

## Purpose

These are the canonical contracts shared by ingestion, processing, API, storage, tests, and the Investigation Agent. Implement them as typed models.

## Observation

```json
{
  "observation_id": "obs_001",
  "source": "GK2A",
  "timestamp_utc": "2026-10-09T11:30:00Z",
  "latitude": 30.90,
  "longitude": 75.85,
  "grid_id": "grid_123",
  "thermal_anomaly": 0.82,
  "quality": 0.91,
  "source_version": "v1"
}
```

## Event

```json
{
  "event_id": "evt_001",
  "grid_id": "grid_123",
  "detected_at_utc": "2026-10-09T11:40:00Z",
  "latitude": 30.90,
  "longitude": 75.85,
  "observation_gap_hours": 3.4,
  "blindness_score": 0.79,
  "fire_likelihood": 0.82,
  "uncertainty": 0.31,
  "exposure_estimate": 64200,
  "priority_score": 0.88,
  "status": "REVIEW_REQUIRED",
  "investigation_status": "QUEUED",
  "feature_version": "features-v1",
  "scoring_version": "score-v1"
}
```

## Investigation

```json
{
  "investigation_id": "inv_001",
  "event_id": "evt_001",
  "agent_version": "agent-v1",
  "prompt_version": "prompt-v1",
  "started_at_utc": "2026-10-09T11:41:00Z",
  "completed_at_utc": "2026-10-09T11:42:00Z",
  "classification": "HIGH_PRIORITY",
  "confidence": 0.84,
  "evidence": [],
  "contradictions": [],
  "missing_evidence": [],
  "reasoning_summary": "",
  "recommended_action": "HUMAN_VERIFICATION"
}
```

## Status enums

Event:

```text
NEW
CANDIDATE
PRIORITIZED
INVESTIGATION_QUEUED
INVESTIGATING
REVIEW_REQUIRED
CONFIRMED
DISMISSED
```

Investigation:

```text
NOT_REQUIRED
QUEUED
RUNNING
COMPLETED
FAILED
```

## Rules

- timestamps are UTC internally
- latitude must be -90..90
- longitude must be -180..180
- scores are normalized 0..1 unless explicitly documented otherwise
- every derived result records its feature/scoring version
- source values and derived values must remain distinguishable
