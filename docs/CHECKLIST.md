# BurnBlind — Master Checklist

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
- [ ] FIRMS historical reference acquired
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
- [x] Amplify manual deployment
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


- [x] Unit tests (77 passing locally, 2026-10-09)
- [ ] Integration tests
- [x] Agent grounding and event-scope tests
- [ ] End-to-end test against the newly deployed backend
- [ ] Security review including authenticated human-review submissions
- [ ] Deployment smoke test
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
- [ ] FIRMS MAP_KEY configured and historical reference files acquired
- [x] Deterministic scoring component and explicit versioned trigger config; feature derivation is implemented but replay seed rows lack complete score inputs
- [x] Replay event generation and stable IDs
- [x] Read-only API with validated filters, pagination, and gated investigation route
- [x] Responsive map-first replay dashboard with explicit historical labeling
- [x] Event evidence detail, investigation status, system overview, and data methodology screens
- [x] SAM template validated; private S3, DynamoDB GSI, API Gateway, and Lambda defined
- [x] Deploy AWS API/data stack and seed 250-cluster replay sample
- [x] Public dashboard deployed with Amplify; browser-origin CORS verified
- [x] Source-backed feature derivation, on-demand population exposure client, and event-scoped investigation packet implemented; live-source and model verification remain

## Local verification and remaining release gates (2026-10-09)

- [x] pytest -q: 77 passed
- [x] npm run build: Vite production build passed
- [x] sam validate --lint --template-file infrastructure/sam/template.yaml
- [x] sam build --template-file infrastructure/sam/template.yaml
- [x] Confirmed the built Event API includes backend/processing; the investigator includes backend/impact and backend/processing
- [x] Frontend includes live-loaded replay distribution, source counts, source limitations, investigation input/output documentation, review outcomes, and replay controls
- [ ] Backend changes deployed and smoke-tested against AWS
- [ ] CI/CD role expanded with a dedicated least-privilege SAM deployment role
- [ ] NASA FIRMS MAP_KEY stored in AWS Secrets Manager and historical comparison records acquired
- [ ] Live model invocation and investigation verified after AWS role setup
- [ ] Historical context and observation-coverage records attached to replay events before publishing score or blindness layers

**Release note:** the currently available GitHub OIDC role is scoped to Amplify publishing only. The renewed local AWS CLI identity resolves to the account root user, so it is not used to deploy backend changes. Switch to an approved deployment role before changing AWS resources. No FIRMS key was found in the repository or GitHub secrets; provide only its Secrets Manager ARN/name, never the key value in chat.
