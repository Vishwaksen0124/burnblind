# BurnBlind — AWS Build & Ship Architecture

## 1. Hackathon mapping

### Build It

| AWS/open-source technology | Role |
|---|---|
| Strands Agents SDK | Investigation Agent |
| SAM CLI | Local serverless development/testing |

### Ship It

| AWS service | Role |
|---|---|
| Amplify Hosting | Frontend |
| API Gateway | HTTP API |
| Lambda | API + processing |
| S3 | Raw/processed/historical data |
| DynamoDB | Current events/investigations |
| SQS | Async processing |
| EventBridge | Scheduling |
| CloudWatch | Logs/metrics |
| Amazon Bedrock Mantle | DeepSeek inference provider for the Strands investigation agent |
| SageMaker AI | Optional model provider if the account has endpoint quota |

## 2. Service-by-service design

### Amplify

Host frontend.

No environmental calculations in client-side code.

### API Gateway

Suggested endpoints:

```text
GET  /health
GET  /summary
GET  /events
GET  /events/{id}
GET  /events/{id}/investigation
POST /events/{id}/investigate
```

### Lambda

Suggested functions:

```text
ingest_data
process_observation
calculate_features
score_event
calculate_impact
api_events
api_event_detail
start_investigation
persist_investigation
```

### S3

```text
burnblind-data/
├── raw/
│   ├── satellite/
│   ├── fires/
│   ├── weather/
│   └── population/
├── processed/
│   ├── observations/
│   ├── grids/
│   └── features/
├── historical/
└── investigations/
```

### SQS

Queues:

```text
burnblind-processing
burnblind-investigation
burnblind-processing-dlq
burnblind-investigation-dlq
```

Keep one queue if scope requires simplicity; split only when workload isolation matters.

### DynamoDB

Recommended logical tables:

```text
Events
Investigations
```

Do not create multiple tables without a requirement.

### EventBridge

Scheduled:

```text
data ingestion
processing
```

### CloudWatch

Log:

- correlation ID
- event ID
- Lambda name
- processing duration
- errors
- agent execution status
- tool failures

## 3. IAM

Use least privilege.

Examples:

- ingestion Lambda → S3 write
- processing Lambda → S3 read + DynamoDB write + SQS
- API Lambda → DynamoDB read
- agent Lambda → DynamoDB read + approved evidence tools
- no wildcard permissions unless unavoidable

## 4. Secrets

Never commit credentials.

Use environment variables for non-secret configuration.

Use an appropriate AWS secret mechanism for model/API credentials.

## 5. Deployment principle

Build locally first:

```text
SAM local
+
sample data
+
Strands
```

Then deploy:

```text
S3
DynamoDB
SQS
Lambda
EventBridge
API Gateway
Amplify
CloudWatch
```

## 6. AWS proof for judging

The demo should visibly establish:

- deployed frontend URL
- AWS architecture
- Lambda execution
- S3 data
- SQS processing
- DynamoDB event state
- CloudWatch logs
- Investigation Agent

## 7. Model-serving decision

The deployed model-provider boundary is:

```text
Candidate event
      ↓
Strands Agent ── DeepSeek V3.2 on Bedrock Mantle
      ↓
Event-scoped read-only evidence tools
      ↓
Evidence-cited structured report
      ↓
DynamoDB → dashboard UI
```

The model provider remains independently configurable while Strands owns the
agent loop, tool execution, and structured report contract. The deployed
Mantle model ID is `deepseek.v3.2`; the Lambda role is scoped to the default
Bedrock project.

The model provider is not the source of environmental truth. Deterministic evidence tools remain authoritative.

## 8. Data-source integration

The first historical pipeline uses:

```text
Zenodo GK2A 2019–2025 dataset
        +
NASA FIRMS historical data
```

Current/near-current GK2A processing can use the public NOAA GK2A S3 dataset.

## 9. Dead-letter handling

Both processing and investigation queues should have a DLQ in the deployed architecture.

A DLQ message must contain enough metadata to diagnose:

- event ID
- source message ID
- processing version
- error category
- timestamp

Do not silently discard failed work.

## 9. Local Build → AWS Ship

Local development should use the same logical boundaries as production:

```text
SAM local
  ↓
Lambda-compatible handlers
  ↓
local/sample S3-compatible inputs where practical
  ↓
SQS-shaped messages
  ↓
deterministic processing
```

The local environment must not depend on paid AWS services to run the core tests.

## 10. Agent model-provider abstraction

The agent implementation must separate:

```text
Strands Agent
     ↓
Model Provider Adapter
     ↓
Selected model
```

Do not hard-code application logic to one model API.

The model provider may be:
- SageMaker AI,
- another supported provider,
- or a local/mock provider for tests.

The production provider should be selected based on access, latency, cost, and hackathon constraints.

## 11. Public demo architecture

The deployed public surface should expose only:

```text
Amplify
  ↓
API Gateway
  ↓
API Lambda
```

Do not expose:
- S3 buckets publicly
- DynamoDB directly
- SQS directly
- agent tools directly

## 12. CloudWatch operational signals

At minimum create alarms/visibility for:

- Lambda errors
- SQS DLQ messages
- investigation failures
- API 5xx
- ingestion failure

## 13. Deployed MVP slice (2026-10-08)

The current `burnblind-replay` stack in `us-east-2` contains the HTTP API,
read-only Lambda, pay-per-request Events table, and private encrypted S3
artifact bucket. It serves 250 explicitly historical candidate clusters.
CloudWatch retains API Lambda logs for 14 days. The S3 `replay/` prefix holds
the sample JSONL and its CC BY 4.0 source manifest; raw research files remain
local/ignored. The dashboard is deployed through Amplify manual hosting at
`https://main.d3k8g1d6au7814.amplifyapp.com`, with API CORS restricted to that
origin plus `http://127.0.0.1:5173` for local development. Queue processing,
schedules, feature derivation, and agent execution
are not deployed. Direct CloudFront creation was denied for account
verification, but Amplify managed hosting succeeded.

API base URL: `https://ad4m8eny2m.execute-api.us-east-2.amazonaws.com/prod`.
