# BurnBlind — Master Checklist

## Current implementation status (2026-10-10, post-deployment verification)

The application foundation and feature code are substantially implemented, but
the end-to-end release is **not complete**. A checked implementation item does
not imply that its live data source or deployed AWS path has been verified.

| Area | Implemented | Still required for release |
| --- | --- | --- |
| Frontend | Landing, monitoring, event detail, investigation, replay, and methodology views; responsive map-first UI; Amplify CI deployment returned HTTP 200 | Browser interaction and visual review at desktop/mobile widths |
| Feature upgrade | Scoring, comparison, exposure, replay, human outcome, event-scoped agent paths exist; four independent FIRMS comparisons and 250 sourced exposure estimates are visible in production | Attach complete historical/coverage/score evidence to replay; validate more live-source cases |
| Agent | Strands integration, event-scoped evidence packet/report, DeepSeek V3.2 Mantle; cross-sensor status handling and retry race regressions covered by unit tests | Broader model scenario evaluation and live integration coverage |
| AWS | Amplify and backend OIDC workflows passed; SAM stack deployed; health, summary, event, action-center, investigation, map-layer and CORS smoke checks passed; one queue-to-report flow verified; Cognito JWT protects both API path forms and anonymous mutation probes return 401 | Invited-reviewer write test, security/cost review and ongoing operational verification |
| Data | GK2A replay sample is present; weather and WorldPop adapters are implemented | FIRMS key/reference data, licensing review, live source checks, full artifact lifecycle |
| Quality | 115 tests, production frontend build, SAM validation, deployed API/CORS/auth smoke checks, production sensor map shows four sourced comparisons, all 250 environmental projections audited and repaired | Browser e2e, authenticated reviewer write, source-to-storage integration, security and cost review |

The production S3 artifact bucket uses versioning and expires noncurrent versions
after 90 days; incomplete multipart uploads expire after 7 days. Current object
versions are retained. This policy was deployed through Backend CI/CD after
scoping the CloudFormation execution role's lifecycle permissions to the
BurnBlind artifact-bucket ARN pattern.

The backend and model path were verified on 2026-10-09. Reviewer JWT
authentication is deployed in API Gateway, the Lambda handler, and frontend.
Both `/api` and unprefixed protected POST routes were probed anonymously and
returned 401; public event reads returned 200. A real invited reviewer is
still needed to complete the authenticated sign-in and outcome-write check.

## Hackathon

- [x] Read current official event page
- [x] Read current official rules
- [ ] Verify Builder Center enrollment status
- [ ] Confirm submission requirements

## Product

- [ ] Problem clearly defined
- [ ] User clearly defined
- [ ] MVP geography frozen
- [x] Product flow documented

## Data

- [ ] GK2A historical dataset acquired
- [x] FIRMS historical reference acquired for Oct–Nov 2025; six matched observations attached to four events
- [ ] GK2A AWS Open Data access tested
- [x] Weather source selected
- [x] Population source selected

- [x] Sources selected
- [ ] Licensing/provenance checked
- [x] Schemas defined
- [x] Sample data validated
- [ ] S3 structure defined

## Intelligence

- [ ] Observation gap
- [ ] Thermal feature
- [ ] Historical risk
- [ ] Sensor disagreement
- [ ] Blindness score
- [ ] Fire likelihood
- [ ] Impact
- [ ] Priority

## Agent

- [x] DynamoDB stream qualification with configured score thresholds
- [x] Analyst override request from event detail
- [x] Strands SDK
- [x] Amazon Bedrock Mantle DeepSeek V3.2 provider
- [x] Read-only, event-scoped evidence tools
- [x] Evidence ID grounding and structured output
- [ ] Broader model evaluation set
- [x] Failure status preserves candidate event for human review

## AWS

- [x] S3 (private encrypted sample artifact bucket)
- [x] FIFO SQS investigation queue
- [x] FIFO DLQ with bounded retry
- [x] DynamoDB Streams score qualification function
- [x] DynamoDB
- [x] API Lambda
- [x] API Gateway
- [ ] EventBridge
- [x] CloudWatch log retention
- [x] Amplify deployment through GitHub Actions OIDC
- [x] Public GitHub repository and GitHub Actions OIDC CI/CD

## Frontend

- [x] Heat/thermal visual language
- [x] Product
- [x] How it works
- [x] Dashboard (historical replay mode)
- [x] Investigation status and report UI
- [x] Data & methodology
- [x] Error states
- [x] Loading states

## Quality
- [ ] Acceptance criteria checked
- [ ] Reproducibility checked
- [ ] Data drift checks run
- [ ] Cost guardrails verified


- [x] Unit tests (93 passing locally, 2026-10-09)
- [ ] Integration tests
- [x] Agent grounding, event-scope, sensor-comparison, output-schema, and retry-race tests
- [x] One event-scoped queue → Strands/DeepSeek → DynamoDB → investigations API happy path verified
- [x] Anonymous investigation/review mutation probes rejected by the deployed JWT routes
- [ ] Authenticated reviewer sign-in and human-review submission
- [ ] Broader security and cost review
- [x] Backend and public frontend deployment smoke checks
- [x] Live API contract, dashboard CORS, and anonymous mutation rejection smoke checks; same checks are now a post-deploy CI gate
- [ ] Demo rehearsal
- [x] Public GitHub
- [x] Public demo URL

- [ ] Build-window compliance checked
- [ ] Live Open-Meteo source verification
- [x] WorldPop client behavior verified with controlled API fixtures; live source still pending
- [x] Geospatial dependencies tested
- [x] Temporal leakage tests passed
- [ ] Attribution file complete
- [ ] Cost controls verified
- [x] Replay mode clearly labelled

## Implemented foundation (2026-10-08)

- [x] Canonical data contracts and validation tests
- [x] GK2A 2019–2025 source files downloaded and checksum-verified
- [x] GK2A source format normalized to UTC and a 5 km UTM grid
- [x] GK2A metadata, date, coordinate, and broad geography checks
- [x] Historical detection summary and timestamp-bounded query
- [x] 250-record real development sample with provenance manifest
- [x] FIRMS parser and key-safe archive downloader implemented
- [x] Open-Meteo ERA5 wind adapter and directional screening corridor
- [x] FIRMS MAP_KEY stored in AWS Secrets Manager; historical reference files acquired and source-matched records attached
- [x] Deterministic scoring component and explicit versioned trigger config; feature derivation is implemented but replay seed rows lack complete score inputs
- [x] Replay event generation and stable IDs
- [x] Read-only API with validated filters, pagination, and gated investigation route
- [x] Responsive map-first replay dashboard with explicit historical labeling
- [x] Event evidence detail, investigation status, system overview, and data methodology screens
- [x] SAM template validated; private S3, DynamoDB GSI, API Gateway, and Lambda defined
- [x] Deploy AWS API/data stack and seed 250-cluster replay sample
- [x] Public dashboard deployed with Amplify; browser-origin CORS verified
- [x] Source-backed feature derivation, on-demand population exposure client, and event-scoped investigation packet implemented; live-source and model verification remain

## Local verification and remaining release gates (2026-10-10)

- [x] pytest -q: 110 passed (2026-10-10)
- [x] npm run build: Vite production build passed
- [x] sam validate --lint --template-file infrastructure/sam/template.yaml
- [x] sam build --template-file infrastructure/sam/template.yaml
- [x] Confirmed the built Event API includes backend/processing; the investigator includes backend/impact and backend/processing
- [x] Frontend includes live-loaded replay distribution, source counts, source limitations, investigation input/output documentation, review outcomes, and replay controls
- [x] Backend changes deployed and smoke-tested against AWS
- [x] Deployed API smoke checker verified against health, events, action center, blind-spot layer, investigations, and both anonymous protected POST routes
- [x] CI/CD role expanded with a repository/branch-scoped SAM deployment role and runtime permissions boundary
- [ ] NASA FIRMS MAP_KEY stored in AWS Secrets Manager and historical comparison records acquired
- [x] One live DeepSeek V3.2 investigation completed after AWS role setup; report persisted and returned by the investigations API
- [x] Production sensor-comparison map displays four independently sourced matching observation comparisons
- [x] Production exposure map displays source-derived estimates; no agent investigation is triggered by environmental attachment
- [x] S3 artifact versioning and approved 90-day noncurrent lifecycle policy deployed and verified
- [ ] Historical context and observation-coverage records attached to replay events before publishing score or blindness layers

**Release note:** frontend and backend use separate GitHub OIDC roles scoped to this repository's `main` branch. The backend deploy role can update only `burnblind-replay` and pass the dedicated CloudFormation execution role. Lambda roles receive the `BurnBlindRuntimeBoundary` permissions boundary. Backend deployment and one event-scoped model run passed on 2026-10-09. No FIRMS key was found in Secrets Manager or GitHub secrets; provide only its Secrets Manager ARN/name, never the key value in chat.
