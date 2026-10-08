# BurnBlind — Problem & Scientific Framing

## 1. Problem definition

Satellite fire monitoring is constrained by sensor characteristics. Polar-orbiting sensors can provide high spatial resolution but have revisit gaps. Geostationary sensors provide frequent observations but may have lower spatial resolution.

A useful environmental system should account for these differences rather than treating one sensor as absolute truth.

## 2. Monitoring blindness

A monitoring blind spot is a period/location where the available observation system provides insufficient confidence for timely event detection.

It can arise from:

- observation gaps
- cloud/quality issues
- spatial resolution limitations
- sensor disagreement
- unusual event timing
- missing data

## 3. What BurnBlind measures

BurnBlind estimates:

1. Observability
2. Fire likelihood
3. Potential impact
4. Investigation priority

## 4. What BurnBlind does not claim

It does not automatically prove:

> "Sensor X missed a fire."

Instead:

> "Current observations indicate elevated monitoring uncertainty and evidence consistent with a potential fire event."

## 5. Evidence hierarchy

Prefer evidence in this order:

1. Independent observed fire products
2. Multiple sensor agreement
3. Thermal anomaly
4. Historical event patterns
5. Weather/contextual evidence
6. Model inference

Model inference must never be presented as direct observation.

## 6. Validation principle

Every score must be reproducible from stored input features.

Every agent recommendation must be traceable to evidence returned by tools.


## 7. Initial data strategy

The MVP uses a two-layer historical strategy:

```text
GK2A 2019–2025 historical fire dataset
              +
NASA FIRMS historical active-fire observations
              ↓
       Historical context
              ↓
      Current observations
              ↓
        Event intelligence
```

GK2A and FIRMS must not be treated as identical sensors. Differences in spatial resolution, observation time, and sensor characteristics must be accounted for during comparison.

The historical GK2A dataset is used primarily to establish patterns; FIRMS provides an independent observation/reference source.
