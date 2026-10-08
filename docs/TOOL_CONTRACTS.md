# BurnBlind — Investigation Agent Tool Contracts

## Purpose

Agent tools are deterministic evidence interfaces. The model should reason over their outputs, not directly over arbitrary infrastructure.

## get_event

Input:
```json
{"event_id":"evt_001"}
```

Output:
- event metadata
- deterministic scores
- status
- version metadata

## get_satellite_evidence

Input:
```json
{"event_id":"evt_001","window_hours":6}
```

Output:
- observations
- sensor
- timestamps
- quality flags
- spatial/temporal matching metadata

## get_historical_context

Output:
- historical event counts
- seasonal activity
- time-of-day activity
- comparison to baseline

## get_weather

Output:
- wind speed
- wind direction
- timestamp
- source
- quality/availability

## get_exposure

Output:
- estimated exposure
- corridor assumptions
- source
- uncertainty

## get_sensor_comparison

Output:
- matched observations
- temporal difference
- spatial tolerance
- sensor resolution metadata
- agreement/disagreement summary

## Tool rules

- Tools are read-only for the MVP.
- Tools must validate event IDs.
- Tools must return structured errors.
- Tools must include source metadata.
- Tools must never fabricate missing values.
- Tool output must be safe to include in an agent prompt.
