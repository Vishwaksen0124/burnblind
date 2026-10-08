# BurnBlind — Acceptance Criteria

## P0 — End-to-end

### AC-001 Data ingestion

Given a valid sample observation, the system stores it with provenance.

### AC-002 Preprocessing

Given observations from supported sources, the system normalizes timestamps, coordinates, and grid IDs.

### AC-003 Historical context

Given an event location/time, the system returns historical fire context.

### AC-004 Blindness score

Given the same features and scoring configuration, the system produces the same blindness score.

### AC-005 Fire likelihood

The system produces a documented, reproducible fire-likelihood result.

### AC-006 Impact

Given wind and population inputs, the system produces a directional exposure estimate or explicitly reports missing inputs.

### AC-007 Priority

The system ranks events using the documented priority policy.

### AC-008 Agent trigger

The Investigation Agent is queued only when trigger conditions are met.

### AC-009 Agent evidence

The agent uses deterministic evidence tools.

### AC-010 Agent grounding

The agent does not claim information absent from tool output.

### AC-011 Agent uncertainty

The agent explicitly identifies missing or conflicting evidence.

### AC-012 Persistence

The event and investigation state are persisted.

### AC-013 API

The frontend can retrieve event and investigation state through the API.

### AC-014 Frontend

An operator can:

- see events,
- filter them,
- open an event,
- inspect evidence,
- read the investigation result.

### AC-015 AWS

The deployed system has a working AWS execution path and logs.

## P1

- current/near-current GK2A ingestion
- SQS DLQ
- EventBridge schedule
- CloudWatch dashboard
- agent evaluation suite
- responsive UI
- evidence timeline

## P2

- authentication
- notifications
- advanced dispersion
- model-based scoring
- continuous feedback learning
