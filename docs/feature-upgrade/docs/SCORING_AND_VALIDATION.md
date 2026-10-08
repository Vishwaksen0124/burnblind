# Scoring and Validation

## Deterministic scoring

The agent does not calculate the core priority score.

Inputs:

- thermal evidence
- independent fire evidence
- historical activity
- sensor agreement
- observation quality
- monitoring blindness
- exposure
- urgency

## Avoid false precision

Do not display `83.72% probability of fire` unless the model is calibrated.

Prefer:

```text
Fire evidence: HIGH
Evidence quality: MEDIUM
Priority: HIGH
```

## Temporal leakage

For an event at time T, do not use data observed after T as an input feature.

## Suggested holdout

```text
2019–2023 development
2024–2025 holdout
```

Document all limitations.

## Metrics

Detection:
- precision
- recall
- false-positive rate
- time-to-reference-detection

Prioritization:
- precision@K
- recall@K
- high-priority hit rate

Agent:
- groundedness
- tool accuracy
- recommendation correctness
- schema validity
