# Investigation Agent Upgrade

## Trigger

Only investigate:

```text
priority >= HIGH
OR uncertainty >= HIGH
OR blindness >= threshold AND fire likelihood >= MODERATE
OR exposure >= HIGH
```

Thresholds must be configuration, not scattered constants.

## Deterministic pre-investigation packet

- event
- timestamp/location
- deterministic scores
- observation evidence
- data quality
- sensor comparison
- historical context
- weather
- exposure
- trigger reason
- provenance IDs

## Tools

```text
get_event
get_satellite_evidence
get_sensor_comparison
get_historical_context
get_weather_context
get_exposure_context
get_data_provenance
```

## Agent job

1. Cross-check evidence.
2. Identify contradictions.
3. Identify missing evidence.
4. Distinguish observed/derived/historical/estimated.
5. Produce recommendation.
6. Never invent evidence.

## Output

```json
{
  "event_id": "BL-1042",
  "classification": "POTENTIAL_FIRE_EVENT",
  "status": "REVIEW_REQUIRED",
  "summary": "...",
  "evidence": [],
  "contradictions": [],
  "uncertainties": [],
  "missing_evidence": [],
  "recommendation": "HUMAN_VERIFICATION",
  "priority": "HIGH"
}
```

Never expose private chain-of-thought in the frontend.
