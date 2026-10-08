# Action Center

## Purpose

Turn hundreds of candidate detections into a short list of things a human should care about.

## Sections

```text
REQUIRES REVIEW
MORE EVIDENCE NEEDED
LOW PRIORITY
```

## Ranking

Use deterministic inputs:

- fire evidence
- monitoring blindness
- potential exposure
- urgency
- evidence quality

The LLM must not calculate the core priority score.

## Event card

```text
HIGH PRIORITY
Patiala, Punjab
Potential fire event
16:04 UTC

Why:
• Thermal anomaly
• High monitoring blindness
• Sensor disagreement
• Potential exposure: 12.4K

[Review event] [Investigate]
```

The Action Center is the bridge between measurement and human action.
