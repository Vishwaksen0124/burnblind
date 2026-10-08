# BurnBlind — Architecture Decisions

## ADR-001 — Serverless backend

**Decision:** Lambda + API Gateway.

**Reason:** Event-driven workload, fast hackathon deployment, low infrastructure management.

## ADR-002 — S3 for data lake

**Decision:** S3 stores raw, processed, and historical files.

**Reason:** Durable object storage and direct compatibility with AWS data workflows.

## ADR-003 — DynamoDB for operational state

**Decision:** DynamoDB stores current events and investigation state.

**Reason:** Low-latency key/value access without relational complexity.

## ADR-004 — SQS for asynchronous work

**Decision:** SQS separates processing and investigation from request handling.

**Reason:** Retryability, decoupling, and workload isolation.

## ADR-005 — EventBridge for schedules

**Decision:** EventBridge triggers scheduled ingestion/processing.

**Reason:** No continuously running scheduler.

## ADR-006 — Strands for the Investigation Agent

**Decision:** Use Strands Agents SDK for the agent layer.

**Reason:** It directly aligns with the hackathon's AWS open-source Build It offering and provides a clear agent/tool abstraction.

## ADR-007 — Agent is not the scoring engine

**Decision:** Keep environmental scoring deterministic and independent.

**Reason:** Scores need reproducibility and scientific auditability. The agent adds value through evidence investigation.

## ADR-008 — GK2A + FIRMS historical strategy

**Decision:** Use the released GK2A historical fire dataset for pattern generation and FIRMS as an independent reference.

**Reason:** Fast MVP development while preserving cross-sensor evidence.

## ADR-009 — No raw multi-year GK2A ingestion initially

**Decision:** Add raw/current GK2A processing only after the historical pipeline works.

**Reason:** Prevent the data pipeline from consuming the hackathon schedule.

## ADR-010 — Heat/thermal UI

**Decision:** Use a thermal monitoring visual language instead of generic AI styling.

**Reason:** Communicates the environmental domain and improves product differentiation.

## ADR-011 — Human-in-the-loop

**Decision:** Agent recommendations require human review.

**Reason:** Environmental monitoring outputs contain uncertainty and should not trigger autonomous emergency decisions.

## ADR-012 — Metric MVP grid

**Decision:** Assign records to 5 km cells after transforming WGS84 coordinates
to UTM zone 43N (EPSG:32643).

**Reason:** Cross-sensor grouping needs a stable metric cell size. Distances are
not computed by treating latitude/longitude degrees as kilometers.

## ADR-013 — External FIRMS credential

**Decision:** Read the FIRMS MAP_KEY only from `FIRMS_MAP_KEY` at runtime.

**Reason:** Historical archive access uses a keyed API; credentials must not be
committed, placed in manifests, or included in logged URLs.
