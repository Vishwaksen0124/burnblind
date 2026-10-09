# BurnBlind — 3-Minute Demo Plan

## 0:00–0:20 — Problem

Show the dashboard.

Say:

> Satellite monitoring is powerful, but different sensors observe the world at different times and resolutions. BurnBlind identifies where monitoring confidence is weak and helps operators decide what deserves attention.

## 0:20–0:50 — Observe

Show map and event.

Explain:

- satellite observations
- observation gap
- thermal evidence
- historical pattern

## 0:50–1:20 — Environmental context

Open event.

Show:

- event-time ERA5 wind, when environmental analysis has been run
- the WorldPop estimate and its directional screening corridor
- sensor comparison only if independent matched evidence is attached

Explain that disagreement is treated as evidence, not automatic proof of a missed fire.

Blind-spot scores and sensor disagreement are shown only when the replay
contains actual sensor coverage or comparison evidence. The current GK2A-only
replay cannot support those claims.

## 1:20–1:50 — Impact

If not already prepared, select a candidate and run **Environmental analysis**.
This queries source data and does not invoke the Investigation Agent.

Show:

- wind
- directional corridor
- estimated exposure

## 1:50–2:30 — Investigation Agent

Trigger/open investigation.

Show:

```text
Evidence
↓
Tools
↓
Cross-check
↓
Recommendation
```

Emphasize:

> The agent is not calculating the basic score. It investigates a high-value/uncertain event using deterministic evidence tools.

## 2:30–2:50 — AWS

Show architecture:

```text
S3
 ↓
SQS
 ↓
Lambda
 ↓
DynamoDB
 ↓
API Gateway
 ↓
Amplify

EventBridge → scheduled processing
CloudWatch → observability
Strands → Investigation Agent
```

## 2:50–3:00 — Impact

Close with:

> BurnBlind turns a satellite monitoring gap into an actionable investigation queue.

## Demo fallback

Have a deterministic local fixture ready.

For a bounded source-enrichment pass before the demo, use:

```text
python scripts/enrich_environmental.py --region '<AWS region>' --limit 5

Then refresh the event view. This invokes deterministic weather and population
sources; use an investigation only for the event you want to inspect with the
agent.
```

must still work.
