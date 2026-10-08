# BurnBlind — System Design

## 1. Goals

- detect monitoring gaps
- identify candidate events
- estimate fire likelihood
- estimate potential impact
- prioritize events
- investigate important/uncertain events with an AI agent
- expose evidence to a human operator

## 2. High-level flow

```text
Data
 ↓
Preprocessing
 ↓
Spatial/temporal alignment
 ↓
Feature generation
 ↓
Monitoring blindness
 ↓
Fire likelihood
 ↓
Impact/exposure
 ↓
Priority
 ↓
Agent investigation
 ↓
Human decision
```

## 3. Core entities

### Observation

```text
observation_id
sensor
timestamp
grid_id
latitude
longitude
thermal_features
quality_flags
source
```

### Event

```text
event_id
grid_id
timestamp
latitude
longitude

observation_gap
thermal_anomaly
historical_fire_risk
sensor_disagreement
data_quality

blindness_score
fire_likelihood

wind_speed
wind_direction
exposure_estimate

priority_score

status
investigation_status
```

### Investigation

```text
investigation_id
event_id
started_at
completed_at
agent_version
evidence[]
contradictions[]
classification
confidence
recommendation
```

## 4. Feature calculations

### Observation gap

```text
gap = current_time - most_recent_relevant_observation
```

Normalize to a bounded score.

### Thermal anomaly

Use physically meaningful thermal-band features supported by the selected data source.

### Historical fire risk

Condition historical activity by:

- location
- season/month
- time of day

### Sensor disagreement

Match observations by spatial and temporal tolerance.

Account for resolution differences before comparing.

## 5. Fire likelihood

Start with a transparent baseline.

Example conceptual structure:

```text
fire_likelihood =
    weighted thermal evidence
  + historical evidence
  + multi-sensor evidence
  + quality-adjusted context
```

Weights are configuration and must be documented.

Do not call the result a calibrated probability until validated as one.

## 6. Impact

MVP impact estimation:

```text
fire location
      +
wind vector
      ↓
directional corridor
      ↓
population intersection
      ↓
exposure estimate
```

This is a screening estimate, not a full atmospheric dispersion model.

## 7. Priority

Priority should consider:

- fire likelihood
- monitoring blindness
- exposure
- urgency
- uncertainty

The exact formula must be versioned.

## 8. Event state machine

```text
NEW
 ↓
CANDIDATE
 ↓
PRIORITIZED
 ↓
INVESTIGATION_QUEUED
 ↓
INVESTIGATING
 ↓
REVIEW_REQUIRED
 ↓
CONFIRMED / DISMISSED
```

Normal low-priority events may remain at `PRIORITIZED` without agent investigation.

## 9. Failure behavior

- missing satellite source → reduce confidence
- missing weather → mark impact estimate incomplete
- malformed data → quarantine
- processing failure → SQS retry
- repeated processing failure → DLQ
- agent unavailable → event remains visible
- API failure → return structured error
