# BurnBlind — Investigation Agent

## 1. Purpose

The Investigation Agent is not the main fire detector.

Its purpose is:

> **Investigate important or uncertain environmental events by gathering relevant evidence through tools and produce a grounded recommendation for human review.**

## 2. Why an agent?

A deterministic score can identify an event.

An agent is useful when the event requires:

- multiple evidence lookups
- deciding which evidence is relevant
- reconciling conflicting observations
- identifying missing evidence
- producing an evidence-backed investigation report

If the task were simply:

```text
score > 80 → print "HIGH"
```

an agent would not be justified.

## 3. Trigger policy

The DynamoDB stream trigger evaluates an event when normalized `score_features`
are written. It uses versioned thresholds from `config/scoring.v1.json` and
queues on high priority, high uncertainty with supported fire-likelihood
evidence, high blindness with moderate likelihood, or high exposure. Missing
features alone do not qualify an event. Historical candidate rows without
score features are not auto-enqueued; an analyst can still request an override
from the event detail view.

## 4. Agent tools

### get_event

Returns deterministic event data.

### get_satellite_evidence

Returns relevant sensor observations and timestamps.

### get_historical_context

Returns historical activity around the location/time.

### get_weather_context

Returns wind and relevant weather information.

### get_exposure_context

Returns population/sensitive-location estimates.

### get_sensor_comparison

Returns normalized cross-sensor comparison.

## 5. Agent workflow

```text
Receive event
    ↓
Read event summary
    ↓
Assess evidence available
    ↓
Select useful tools
    ↓
Gather evidence
    ↓
Compare evidence
    ↓
Identify contradictions
    ↓
Assess confidence
    ↓
Produce recommendation
```

## 6. Structured output

The deployed contract allows `REVIEW_REQUIRED` or `INSUFFICIENT_EVIDENCE`,
requires source evidence IDs for every cited finding, and intentionally stores
no model confidence score. Reports include a concise summary, contradictions,
missing evidence, and a human-facing recommendation. `HIGH_PRIORITY` and
`CONFIRMED` are not valid model classifications.

```json
{
  "classification": "REVIEW_REQUIRED",
  "evidence": [
    {
      "evidence_id": "obs_123",
      "interpretation": "A satellite source record is attached for review."
    }
  ],
  "contradictions": [],
  "missing_evidence": [],
  "summary": "A source record is available for human review.",
  "recommended_action": "HUMAN_VERIFICATION"
}
```

Do not expose hidden chain-of-thought.

Store concise evidence, conclusions, and uncertainty.

## 7. Grounding rules

The agent MUST:

- use tool-returned evidence
- distinguish observations from estimates
- mention missing evidence
- acknowledge contradictions
- avoid fabricated values
- avoid fabricated sources
- avoid claiming certainty where data is uncertain

## 8. Agent instructions

Core behavior:

```text
You are an environmental investigation agent.

Investigate the supplied event using available evidence tools.

Do not invent observations.

Treat sensor disagreement as evidence requiring interpretation,
not proof that a fire was missed.

Separate:
1. observed facts,
2. derived estimates,
3. historical context,
4. uncertainty.

Use only evidence returned by tools.

If evidence is insufficient, say so.

Your job is to recommend whether human investigation is warranted,
not to make autonomous emergency decisions.
```

## 9. Accuracy strategy

Agent quality depends primarily on tool quality.

Implement:

- typed tool schemas
- deterministic tool outputs
- source metadata
- structured output validation
- evidence citations
- evaluation fixtures
- regression tests

## 10. Investigation evaluation

Test:

1. high-confidence event
2. false-positive-like event
3. conflicting sensors
4. missing weather
5. missing satellite
6. high exposure
7. low priority
8. contradictory historical evidence

Metrics:

- factual grounding
- evidence coverage
- correct tool use
- contradiction handling
- structured output validity
- recommendation consistency
- hallucination rate

## 11. Fallback

If the model is unavailable:

```text
Agent unavailable
     ↓
Event remains visible
     ↓
The historical candidate event remains visible
     ↓
Status = REVIEW_REQUIRED
```

## 12. Tool contracts

Every agent tool must have:

- typed input schema
- typed output schema
- timeout
- error response
- source metadata
- event ID
- timestamp

Example:

```json
{
  "event_id": "evt_001",
  "source": "FIRMS",
  "observed_at": "2026-10-08T12:20:00Z",
  "records": [],
  "status": "OK"
}
```

## 13. Tool access policy

The agent may read evidence but must not:

- modify source data
- modify scoring configuration
- modify IAM
- deploy infrastructure
- execute arbitrary shell commands
- make emergency notifications autonomously

## 14. Deployed implementation

- Strands Agents SDK with Amazon Bedrock DeepSeek V3.2 (`deepseek.v3.2`).
- A qualifying score update or analyst override is persisted in DynamoDB and
  dispatched through an encrypted FIFO SQS queue with a dead-letter queue.
- The worker has a 120-second timeout, 900-token model output cap, and reserved
  concurrency of two. Latency has not been benchmarked.
- Read-only tools are scoped to the requested event. Report evidence IDs are
  checked against evidence returned during that invocation.
- `tests/unit/test_agent.py` covers request scoping and evidence citation
  validation. Broader scenario evaluation remains pending because several
  evidence sources are not present in the replay.

## 15. Investigation lifecycle

```text
TRIGGERED
  ↓
QUEUED
  ↓
RUNNING
  ↓
COMPLETED
  ├── HIGH_PRIORITY
  ├── REVIEW_REQUIRED
  └── INSUFFICIENT_EVIDENCE
```

Failed runs:

```text
RUNNING → FAILED → RETRY / REVIEW_REQUIRED
```

## 15. Evidence citation

Each agent conclusion should reference evidence IDs rather than relying on free-form source names.

Example:

```json
{
  "claim": "VIIRS had no matching observation within the comparison window.",
  "evidence_ids": ["obs_781", "obs_782"]
}
```

This makes the investigation auditable.

## 16. Deterministic pre-check

Before calling the model, the system should assemble a compact event packet containing:

- event ID
- scores
- relevant observations
- data-quality flags
- historical context
- impact estimate
- trigger reason

This reduces unnecessary model calls and improves grounding.
