# Testing and Evaluation

## Unit tests

Geospatial:
- coordinate transforms
- distance
- spatial matching
- corridor geometry
- raster aggregation

Scoring:
- normalization
- thresholds
- missing features
- config versions

Sensor comparison:
- exact match
- near match
- mismatch
- missing sensor
- bad quality

Exposure:
- wind directions
- no wind
- missing weather
- no population
- invalid coordinates

## Integration tests

```text
S3 → processing → DynamoDB
EventBridge → SQS → worker
SQS → investigation
Investigation → DynamoDB
API → frontend
```

## Failure tests

Simulate:
- FIRMS unavailable
- weather timeout
- S3 missing
- DynamoDB throttling
- duplicate SQS message
- agent timeout
- model authorization error
- malformed tool result

Never fabricate missing evidence.

## Agent evaluation

Use Strands Evals:
- FaithfulnessEvaluator
- CorrectnessEvaluator
- TrajectoryEvaluator
- deterministic evaluators
- tool parameter accuracy
- chaos testing

Cases:
1. strong multi-source agreement
2. GK2A only
3. VIIRS only
4. cross-sensor disagreement
5. missing weather
6. missing population
7. high blindness + moderate fire evidence
8. low-priority event
9. contradictory evidence
10. tool timeout
11. malformed tool output
12. prompt injection in external data

Acceptance targets are engineering targets, not scientific validation.
