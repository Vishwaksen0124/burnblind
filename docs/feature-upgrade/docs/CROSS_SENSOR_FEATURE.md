# Cross-Sensor Disagreement Explorer

## Purpose

Use independent observations to identify events that deserve investigation.

Disagreement is evidence for investigation, not proof that one sensor missed a fire.

## Classification

```text
AGREEMENT
DISAGREEMENT
INDEPENDENT_OBSERVATION_UNAVAILABLE
INCONCLUSIVE
```

## Matching

1. Match observations within a configurable temporal window.
2. Match spatially using a tolerance appropriate to sensor resolution.
3. Apply quality filters.
4. Record spatial and temporal deltas.
5. Classify the comparison.

## Output

```json
{
  "status": "DISAGREEMENT",
  "primary_sensor": "GK2A",
  "comparison_sensor": "VIIRS",
  "temporal_delta_minutes": 6,
  "spatial_delta_km": 2.1,
  "reason": "Thermal signal has no matching independent detection",
  "confidence": "MEDIUM"
}
```

## UI

Show both sensors on the map, their observation times, resolution/quality context, and a clear disagreement label.

Never write `VIIRS missed the fire` unless there is actual validation proving that.
