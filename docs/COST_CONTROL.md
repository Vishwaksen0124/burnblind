# BurnBlind — AWS Cost Control

## Principles

Keep the hackathon deployment within available AWS Free Tier/credits where practical.

## Controls

- avoid continuous polling
- use deliberate EventBridge frequency
- process only the MVP geography
- download small data windows
- cache/reuse historical data
- invoke the agent only for score-qualified events; unscored candidates are skipped
- retain the analyst override for deliberate manual review
- cap model output at 900 tokens and worker concurrency at two
- use a mock model for tests
- cap investigation retries
- use an SQS DLQ
- avoid unnecessary NAT gateways
- avoid always-on compute
- configure CloudWatch retention

## Pre-deployment checklist

- [ ] No accidental high-frequency polling
- [ ] No repeated multi-year satellite download
- [x] Automatic invocation requires a versioned score qualification decision
- [x] SQS retry count bounded with a DLQ
- [ ] CloudWatch retention checked
- [ ] AWS budget/cost alert configured if available
- [ ] Demo uses deterministic replay where live calls are unnecessary
