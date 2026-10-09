# BurnBlind — Testing Strategy

## 1. Testing layers

1. Unit correctness
2. Data validation
3. Environmental calculations
4. AWS integration
5. Agent evaluation
6. End-to-end behavior

## 2. Unit tests

Test:

- timestamp conversion
- coordinate validation
- grid assignment
- observation gap
- thermal feature calculation
- historical risk
- sensor matching
- score normalization
- priority
- wind vector
- exposure

## 3. Data tests

Check:

- required fields
- types
- coordinate bounds
- timestamp validity
- duplicates
- missing values
- impossible values
- coverage

## 4. Scoring tests

Include:

- no observation
- recent observation
- high thermal anomaly
- low thermal anomaly
- high historical risk
- sensor agreement
- sensor disagreement
- missing sensor
- contradictory evidence

## 5. Integration tests

Test:

```text
sample
 → S3
 → SQS
 → Lambda
 → DynamoDB
```

The backend deployment workflow also runs `scripts/smoke_deployed_api.py`
after deploy. It checks health, event/action-center/map-layer/investigation
read contracts and dashboard CORS, then verifies that anonymous investigation
and reviewer-write requests return 401. The mutation probes use a reserved,
nonexistent event ID and cannot alter a real event.

## 6. Failure tests

Simulate:

- S3 error
- malformed record
- SQS duplicate
- Lambda failure
- DynamoDB failure
- weather failure
- agent failure
- API failure

Expected fallback must be defined.

## 7. Agent evaluation

Minimum scenarios:

| Case | Expected behavior |
|---|---|
| High evidence | Recommend investigation |
| Weak evidence | State uncertainty |
| Sensor conflict | Explain disagreement |
| Missing weather | Do not invent wind |
| Missing satellite | State limitation |
| High exposure | Elevate concern |
| Low priority | Avoid unnecessary escalation |
| False-positive-like | Avoid overclaiming |

## 8. Agent metrics

Track:

- tool-call correctness
- evidence coverage
- factual grounding
- contradiction detection
- structured output validity
- hallucination rate
- recommendation consistency

## 9. Regression testing

Every agent prompt/tool/schema change must rerun the fixed evaluation suite.

## 10. Definition of test completion

- all critical unit tests pass
- integration path passes
- failure tests pass
- agent evaluation passes agreed threshold
- end-to-end demo passes

## 12. Reproducibility tests

- [ ] Same fixture + same config → same deterministic scores
- [ ] Processing version recorded
- [ ] Source version recorded
- [ ] Agent version recorded
- [ ] Prompt version recorded

## 13. Data drift checks

For each new dataset load:

- [ ] row count compared with previous load
- [ ] geographic bounds checked
- [ ] timestamp range checked
- [ ] missing-value rate checked
- [ ] source schema compared
- [ ] unexpected distribution changes reviewed

## 14. Performance tests

Measure:

- ingestion latency
- processing latency per event
- queue-to-completion latency
- API p95 latency
- investigation latency

Set practical hackathon targets after the first benchmark instead of inventing targets beforehand.

## 15. Cost safety tests

Before public deployment:

- [ ] scheduled jobs have intended frequency
- [ ] no accidental tight polling
- [ ] SQS retry policy is bounded
- [ ] model calls are not triggered for low-value events
- [ ] large raw datasets are not repeatedly downloaded
- [ ] CloudWatch retention is appropriate

## 16. Spatial correctness tests

Test:

- point-to-grid assignment
- CRS transformation
- distance calculations
- corridor geometry
- polygon/raster intersection
- boundary conditions at Punjab/Haryana edges

Use known fixtures with expected geometries.

## 17. Historical validation split

Do not validate the scoring model on the same events used to tune thresholds.

For the historical dataset, use a temporal holdout where practical:

```text
2019–2023 → baseline/tuning
2024–2025 → holdout evaluation
```

If the data volume is insufficient, document the limitation instead of claiming model validation.

## 18. Leakage checks

Do not allow future information to enter features for a historical event.

Examples of leakage:

- using a future FIRMS detection to calculate a current-event feature
- using a full-season count that includes events after the event timestamp
- using post-event weather when simulating real-time detection

All time-dependent features must be computed using information available at the event timestamp.

## 19. Score calibration

If the output is called a probability:

- evaluate calibration
- use a calibration method if necessary
- report validation performance

Otherwise label it:

```text
fire_likelihood_score
```

rather than:

```text
fire_probability
```

## 20. Agent-vs-engine separation test

Verify that:

- changing the LLM does not change deterministic environmental scores
- agent failure does not remove the event
- agent output does not mutate raw evidence
- agent recommendations are based on tool output

## 21. Demo-mode tests

- [ ] fixture is clearly labelled
- [ ] live/replay state is visible
- [ ] source timestamps are shown
- [ ] no fake live claims
