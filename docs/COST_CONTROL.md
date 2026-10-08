# BurnBlind — AWS Cost Control

## Principles

Keep the hackathon deployment within available AWS Free Tier/credits where practical.

## Controls

- avoid continuous polling
- use deliberate EventBridge frequency
- process only the MVP geography
- download small data windows
- cache/reuse historical data
- trigger the agent only for qualifying events
- use a mock model for tests
- cap investigation retries
- use an SQS DLQ
- avoid unnecessary NAT gateways
- avoid always-on compute
- configure CloudWatch retention

## Pre-deployment checklist

- [ ] No accidental high-frequency polling
- [ ] No repeated multi-year satellite download
- [ ] No agent invocation for every event
- [ ] SQS retry count bounded
- [ ] CloudWatch retention checked
- [ ] AWS budget/cost alert configured if available
- [ ] Demo uses deterministic replay where live calls are unnecessary
