# BurnBlind — Implementation Plan

This is the master execution checklist. Follow the order.

## Phase 0 — Requirements and project contract

- [x] Confirm current hackathon rules (official page checked 2026-10-08)
- [x] Confirm AWS requirement
- [ ] Confirm allowed model/provider
- [x] Read `docs/REQUIREMENTS.md`
- [ ] Confirm project eligibility
- [ ] Confirm current hackathon submission requirements
- [ ] Freeze Punjab/Haryana MVP
- [ ] Freeze terminology
- [ ] Freeze architecture
- [x] Create Git repository
- [x] Confirm project implementation began on the published event start date, October 8, 2026
- [x] No project implementation commits predate the event opening
- [x] Record architecture decisions in `docs/DECISIONS.md`
- [x] Create `docs/DATA_SOURCES.md` provenance manifest

## Phase 1 — Architecture and repository

- [x] Create initial directory structure
- [x] Python project metadata and dependency declaration
- [x] Frontend application (map-first historical replay dashboard)
- [ ] Linting/formatting
- [x] Test runner configuration
- [x] Frontend and backend CI/CD workflows use repository-scoped AWS OIDC roles (`.github/workflows/amplify-deploy.yml`, `.github/workflows/backend-deploy.yml`)
- [x] README updated with the current implementation and local data workflow

## Phase 2 — Data contracts FIRST

- [x] Observation schema
- [x] Fire-event schema
- [x] Weather schema
- [x] Population schema
- [x] Event schema
- [x] Investigation schema
- [x] Validation models
- [x] Synthetic contract fixtures clearly labeled as non-observational

Phase 2 gate: passing unit tests cover contract bounds, timestamps, enum
validation, source serialization, and missing optional measurements.

**Gate:** No scoring implementation until schemas and fixtures pass.

## Phase 3 — Real historical data foundation

### Primary historical baseline

- [x] Download/use GK2A 2019–2025 Punjab/Haryana fire hotspot dataset
- [x] Record source/provenance
- [x] Record dataset version/checksum where available
- [x] Inspect schema and fields
- [x] Validate timestamps
- [x] Validate coordinate ranges
- [x] Validate embedded region/year/month metadata and Punjab/Haryana study-envelope coordinates
- [x] Map records to the common 5 km UTM grid
- [x] Derive historical source-detection counts by grid
- [x] Derive seasonal/monthly detection patterns
- [x] Derive local-hour detection patterns
- [x] Store a small real-data development sample with source manifest under `data/sample/`
- [ ] Store full historical data in S3 when deployed

### Independent reference source

- [ ] Obtain historical NASA FIRMS MODIS/VIIRS data for the MVP geography/time period
- [x] Implement the schema-aware FIRMS CSV normalizer
- [x] Implement a key-safe archive downloader for standard MODIS/VIIRS products
- [ ] Normalize acquired FIRMS records
- [ ] Validate timestamps and coordinates
- [ ] Map observations to the same grid
- [x] Implement spatial/temporal matching and strict sensor comparison logic
- [ ] Acquire independent FIRMS reference records and validate comparison against them

### Current observation source

- [ ] Test access to NOAA GK2A AWS Open Data
- [ ] Identify the exact GK2A products/channels required
- [ ] Download a small development sample
- [ ] Validate timestamps, geolocation and quality metadata
- [ ] Document access and processing assumptions

### Important scope rule

Do **not** download or process years of raw GK2A imagery before the historical baseline and feature pipeline work.

Start with the released GK2A fire dataset + FIRMS historical data. Add raw/current GK2A processing only after the baseline pipeline is reproducible.

**Gate:** historical baseline can be loaded reproducibly, mapped to the common grid, and queried by location/date/time.

## Phase 4 — Local preprocessing

**Gate:** all canonical data-contract tests must pass before preprocessing is accepted.


- [x] Normalize GK2A historical dataset
- [ ] Normalize FIRMS historical dataset
- [ ] Normalize current GK2A observations
- [x] Timestamp normalization
- [x] Coordinate normalization
- [x] Grid mapping
- [x] Sensor normalization
- [x] Reject malformed rows and invalid coordinates/timestamps rather than silently skipping them
- [x] Feature-ready canonical JSONL records

**Gate:** preprocessing tests pass.

## Phase 5 — Environmental feature engine

- [x] observation gap with UTC and future-observation leakage validation
- [ ] thermal anomaly
- [x] historical source-detection context with an event-time cutoff
- [x] sensor disagreement (only with explicit matched observations and coverage evidence)
- [x] timing-risk and observation-quality input normalization
- [ ] Attach source-backed coverage/quality records to the replay event pipeline
- [x] Cross-source detection matching primitive (same metric grid/time window)

Every feature:

- [ ] documented
- [ ] unit tested
- [ ] edge-case tested

## Phase 6 — Scoring

- [x] Deterministic blindness score from normalized inputs
- [x] Heuristic fire-likelihood score from normalized inputs
- [x] Missingness/disagreement uncertainty score
- [x] Priority score, unavailable when required inputs are missing
- [x] Versioned score weights and trigger thresholds
- [ ] validate historical examples

**Gate:** identical input produces identical output.

## Phase 7 — Impact

- [x] Historical ERA5 wind ingestion with explicit missing-value handling
- [x] Downwind bearing and geodesic directional screening corridor
- [x] Asynchronous WorldPop v2 polygon population-sum client
- [x] Event-scoped directional screening corridor and stored estimate provenance
- [x] Explicit assumptions and limitations
- [ ] Live WorldPop service verification and confidence calibration

## Phase 8 — Event engine

- [x] event generation
- [x] deterministic clustering within same grid/time window
- [x] stable content-derived event IDs
- [ ] persistent state transitions
- [ ] priority assignment

## Phase 9 — S3

- [x] private encrypted bucket in SAM template
- [ ] bucket use for deployed replay artifacts
- [ ] raw prefix
- [ ] processed prefix
- [ ] historical prefix
- [ ] investigation artifact prefix
- [ ] encryption
- [ ] versioning where useful
- [ ] lifecycle policy
- [ ] IAM
- [ ] upload/read tests
- [ ] public-access block verified

## Phase 10 — SQS

- [ ] processing queue
- [ ] investigation queue
- [ ] DLQ
- [ ] visibility timeout
- [ ] retry policy
- [ ] idempotency
- [ ] poison-message behavior
- [ ] worker failure tests

## Phase 11 — Lambda

**Gate:** local processing and queue tests pass before cloud deployment.

- [x] define API Lambda boundary
- [x] define timeout/memory configuration
- [ ] package geospatial dependencies safely
- [ ] ingestion
- [ ] processing
- [ ] scoring
- [ ] impact
- [x] API
- [ ] investigation launcher

## Phase 12 — DynamoDB

- [x] Events table
- [ ] Investigations table
- [x] event keys and `data-mode-detected-at` index
- [ ] status fields
- [ ] timestamps
- [ ] version/concurrency handling
- [ ] TTL policy if appropriate
- [ ] persistence
- [ ] concurrency tests

## Phase 13 — EventBridge

- [ ] scheduled ingestion
- [ ] scheduled processing if required
- [ ] duplicate protection

## Phase 14 — Investigation Agent

**Status:** Agent worker and automatic DynamoDB stream qualification are
implemented. Events qualify from versioned normalized score features; replay
seed rows have no score features and therefore do not auto-enqueue. Analysts
can still request an override from the event detail view.

- [x] configure Strands separately from the Bedrock Mantle model provider
- [x] inject a fake agent factory for deterministic runtime tests


- [x] select Amazon Bedrock Mantle DeepSeek V3.2 (`deepseek.v3.2`)
- [x] configure Strands
- [x] agent instructions
- [x] output schema
- [x] Application-side event and source evidence readers
- [x] Assemble satellite, weather, exposure, history, and comparison results before model invocation
- [x] Requested-event scoping and evidence validation
- [x] Model receives a bounded JSON input packet and has no callable retrieval tools
- [ ] Historical context and explicit observation-coverage evidence attached to the deployed replay
- [x] evidence grounding
- [x] DynamoDB stream evaluates the existing versioned investigation trigger
- [x] analyst override request available in the event detail view
- [x] empty feature records do not qualify from missingness alone
- [x] failed run leaves candidate event available for human review

The event detail UI presents qualification reasons, report status, evidence, sensor comparison, exposure availability, and human-review outcomes.
The feature derivation and score-trigger code are implemented and unit-tested, but the seed pipeline still does not attach complete `score_features`; replay seed rows therefore remain unscored.
Source assembly happens before model invocation. The model receives only the event-scoped JSON packet, and unavailable evidence is represented explicitly. On 2026-10-09 the OIDC deployment completed, then one event-scoped investigation invoked `deepseek.v3.2`, completed in about 25 seconds, and persisted a cited report. Broader model scenarios and automatically qualified events remain unverified because the replay seed has no score features.

## Phase 15 — Agent evaluation

- [ ] 10+ model evaluation scenarios (requires additional source fixtures)
- [ ] expected evidence
- [ ] expected classification
- [ ] missing-data tests
- [ ] contradiction tests
- [x] unsupported evidence ID rejection
- [ ] structured-output validation

## Phase 16 — API

- [x] health
- [x] summary
- [x] events
- [x] event detail
- [x] investigation read and gated POST
- [x] API errors
- [x] CORS
- [x] correlation IDs

## Phase 17 — Frontend

- [x] thermal design system
- [x] product page
- [x] how-it-works
- [x] map-first dashboard
- [x] event evidence detail
- [x] investigation list and structured report UI
- [x] data and methodology page
- [x] responsive layout
- [x] loading/error states

## Phase 18 — Infrastructure as code + AWS deployment

**Gate:** all critical local and integration tests pass before public deployment.

- [x] SAM template
- [x] parameter/config separation
- [x] stack outputs
- [x] Amplify deployment publisher script
- [x] private S3
- [x] DynamoDB
- [x] FIFO SQS/DLQ
- [x] API Lambda
- [ ] EventBridge
- [x] API Gateway HTTP API
- [x] CloudWatch API log group with 14-day retention
- [x] Amplify manual frontend hosting
- [x] least-privilege read policy for API Lambda
- [x] API table and CORS environment configuration
- [x] AWS API/data stack deployed (API Gateway, Lambda, DynamoDB, private S3)
- [x] 250-cluster replay sample seeded
- [x] replay JSONL and provenance manifest stored in private S3
- [x] deployed health, summary, event list, CORS, and investigation gate verified
- [x] CORS allows only the Amplify and local Vite origins
- [x] public Amplify dashboard deployed and returned HTTP 200
- [x] Dedicated backend GitHub OIDC deploy role and CloudFormation runtime boundary provisioned
- [ ] First automated SAM backend deployment and cloud smoke test

## Phase 19 — End-to-end

**Gate:** every P0 acceptance criterion in `docs/ACCEPTANCE_CRITERIA.md` passes.

```text
Data
 ↓
S3
 ↓
SQS
 ↓
Lambda
 ↓
Features
 ↓
Scores
 ↓
Event
 ↓
Impact
 ↓
Priority
 ↓
Agent trigger
 ↓
Agent tools
 ↓
Investigation
 ↓
DynamoDB
 ↓
API
 ↓
Frontend
```

- [ ] happy path
- [ ] duplicate message
- [ ] source failure
- [ ] agent failure
- [ ] API failure
- [ ] UI error state
- [ ] CloudWatch verification

## Phase 20 — Documentation and submission verification

- [ ] README matches actual implementation
- [ ] AWS architecture matches deployed resources
- [ ] Data sources have provenance
- [ ] Scientific claims reviewed
- [ ] Agent limitations documented
- [ ] Demo/replay behavior clearly labelled
- [ ] Demo URL works
- [ ] GitHub repository is public
- [ ] Demo video is ≤ 3:00
- [ ] Video is public/unlisted and tested signed out
- [ ] AWS usage is visible in the video
- [ ] Investigation Agent is visible in the video
- [ ] Short write-up complete
- [ ] Source attribution complete
- [ ] No secrets or credentials committed
- [ ] Build-window compliance checked
- [ ] Submission form tested before final submit
- [ ] Final screenshots captured

## Phase 21 — Final demo

- [ ] Select strongest event
- [ ] Select contrasting event
- [ ] Prepare agent investigation
- [ ] Prepare architecture explanation
- [ ] Prepare 3-minute story
- [ ] Prepare deterministic fallback/replay
- [ ] Verify public URL
- [ ] Verify GitHub
