# Feature Upgrade Plan

## Existing flow

```text
Satellite/Fire Data
 → Observation Processing
 → Candidate Events
 → Blindness + Fire Likelihood
 → Impact
 → Priority
 → Investigation Agent
```

## Updated flow

```text
Satellite/Fire Data
 → Observation Processing
 → Monitoring Coverage Assessment
 → Candidate Events
 → Historical Context
 → Cross-Sensor Comparison
 → Weather/Wind
 → Population Exposure
 → Priority Engine
 → Action Center
 → Selected/Uncertain Events
 → Investigation Agent
 → Human Review
 → Outcome
 → Replay/Evaluation
```

## Product questions

Every feature must answer one of:
1. Where is monitoring weak?
2. What deserves attention?
3. Why?
4. Could people be affected?
5. What evidence agrees or conflicts?
6. What should a human investigate next?
