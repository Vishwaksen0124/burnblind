# API, AWS and Security Changes

## APIs

```text
GET  /summary
GET  /events
GET  /events/{id}
GET  /events/{id}/sensor-comparison
GET  /events/{id}/exposure
POST /events/{id}/investigate
GET  /events/{id}/investigation
POST /events/{id}/review
GET  /replay
GET  /replay/{timestamp}
```

## AWS

Existing flow remains:

```text
Amplify → API Gateway → Lambda → DynamoDB
S3 → SQS → processing Lambda → DynamoDB
EventBridge → scheduled ingestion
High priority → investigation SQS → Lambda → Strands → real model
CloudWatch → logs/metrics/traces
```

Add S3:
```text
processed/blind-spots/
processed/sensor-comparisons/
processed/exposure/
replay/
provenance/
```

Add DynamoDB:
```text
ReviewOutcomes
```

## Agent observability

Use OpenTelemetry/CloudWatch to capture:
- model calls
- tool calls
- orchestration
- latency
- failures

## Security

Agent tools must be read-only where possible and explicitly allowlisted.

Never give the agent:
- arbitrary shell execution
- unrestricted HTTP
- IAM mutation
- infrastructure mutation

Treat external data as untrusted input.

Use least-privilege IAM, private S3, request validation and structured output validation.
