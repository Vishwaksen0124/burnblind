# Monitoring Blind Spot Map

## Problem

A monitoring system can produce detections while still having areas/times where its ability to observe is weak.

## User value

The operator sees where monitoring is unreliable, instead of only seeing detected fires.

## Inputs

- observation availability
- observation gap
- data-quality flags
- sensor coverage/resolution
- timing risk
- historical fire activity
- cross-sensor availability

## Score

Use a configurable normalized score:

```text
blindness =
  w_gap * observation_gap
+ w_quality * data_quality_risk
+ w_sensor * sensor_coverage_gap
+ w_timing * timing_risk
```

Store the weight/version configuration.

## Important wording

Use `monitoring blind spot`, `observability gap`, or `observation gap`.

Do NOT call this `probability of missed fire` unless scientifically calibrated.

## Map layer

```text
Events
Blind Spots
Sensor Disagreement
Potential Exposure
```

Clicking a blind spot shows location, score band, drivers, recent events and historical context.

## Tests

- missing observation
- poor-quality observation
- normal coverage
- high historical activity
- sensor unavailable
- boundary cells
- stable score under repeated processing
