# BurnBlind — System Architecture

## 1. Architecture principle

Use a serverless, event-driven architecture.

Keep the environmental intelligence engine independent from the frontend and from the Investigation Agent.

The canonical processing order is:

```text
event ingestion/replay
       → environmental analysis for every event
       → deterministic score and priority calculation
       → human review of evidence and reasons
       → Investigation Agent when the reviewer requests it
       → investigation outcome and audit trail
```

Environmental analysis enriches evidence; it does not calculate core scores
or invoke the agent. Missing and late sources are represented explicitly.

## 2. Architecture

```text
                       ┌──────────────────────┐
                       │      Frontend        │
                       │ React / Next.js      │
                       │ Amplify Hosting      │
                       └──────────┬───────────┘
                                  │ HTTPS
                                  ▼
                       ┌──────────────────────┐
                       │     API Gateway      │
                       └──────────┬───────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │       Lambda         │
                       │      API layer       │
                       └──────┬───────┬───────┘
                              │       │
                         ┌────┘       └─────┐
                         ▼                  ▼
                  ┌─────────────┐    ┌─────────────┐
                  │  DynamoDB   │    │      S3     │
                  │ Live state  │    │ Data lake   │
                  └─────────────┘    └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │     SQS     │
                                      │ Work queue  │
                                      └──────┬──────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │   Lambda    │
                                      │   Workers   │
                                      └──────┬──────┘
                                             │
                                             ▼
                                    ┌───────────────────┐
                                    │ Environmental     │
                                    │ Intelligence      │
                                    │ Engine            │
                                    └─────────┬─────────┘
                                              │
                                                                                                          accepted human review
                                              │
                                              ▼
                                    ┌───────────────────┐
                                    │ Investigation     │
                                    │ Agent             │
                                    │ Strands SDK       │
                                    └─────────┬─────────┘
                                              │
                                              ▼
                                         DynamoDB
                                              │
                                              ▼
                                          Frontend

EventBridge → scheduled jobs
CloudWatch  → logs/metrics
```

## 3. Component ownership

### Frontend

Visualization and user interaction only.

### API

Read/write boundary for the frontend.

### Processing workers

Data normalization, feature generation, scoring, and impact calculations.

### Agent

Evidence investigation and recommendation.

### Storage

S3 for durable datasets/files.

DynamoDB for current operational state.

## 4. Why SQS?

SQS separates:

- ingestion from processing
- processing from investigation
- producers from workers

It also provides retry behavior and a dead-letter path.

## 5. Why DynamoDB?

The frontend needs low-latency access to current events and investigation state.

This does not require relational joins.

## 6. Why EventBridge?

Environmental processing can be scheduled without running a server continuously.

## 7. Why Lambda?

The workload is event-driven and intermittent. Lambda minimizes infrastructure management.

## 8. What is intentionally excluded

Unless a concrete requirement appears:

- EC2
- ECS
- EKS
- Fargate
- RDS
- Aurora
- Redis
- SNS
- Cognito

Do not increase architectural complexity without need.

## 9. Geospatial processing boundary

Environmental calculations should be implemented as testable Python modules.

```text
backend/
├── processing/
│   ├── spatial/
│   ├── temporal/
│   ├── sensors/
│   └── quality/
├── scoring/
├── impact/
└── agent/
```

Do not put GeoPandas/Rasterio-heavy processing into API Lambda handlers if it makes deployment packages too large or slow. Separate batch/worker processing from lightweight API handlers.

## 10. Idempotency

Every asynchronous job must be safe to retry.

Use an idempotency key derived from relevant identifiers, for example:

```text
source + source_record_id + processing_version
```

Investigation requests should also have an idempotency key so duplicate SQS messages do not create duplicate investigations.

## 11. Versioned artifacts

Store or associate:

```text
data_source_version
processing_version
feature_version
scoring_version
agent_version
prompt_version
tool_version
```

with derived events and investigations.
