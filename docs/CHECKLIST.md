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
- [ ] Product flow documented

## Data

- [ ] GK2A historical dataset acquired
- [ ] FIRMS historical reference acquired
- [ ] GK2A AWS Open Data access tested
- [ ] Weather source selected
- [ ] Population source selected

- [ ] Sources selected
- [ ] Licensing/provenance checked
- [ ] Schemas defined
- [ ] Sample data validated
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

- [ ] Trigger policy
- [ ] Strands SDK
- [ ] Model provider
- [ ] Tool schemas
- [ ] Evidence grounding
- [ ] Structured output
- [ ] Evaluation set
- [ ] Fallback

## AWS

- [x] S3 (private encrypted sample artifact bucket)
- [ ] SQS
- [ ] DLQ
- [x] DynamoDB
- [x] API Lambda
- [x] API Gateway
- [ ] EventBridge
- [x] CloudWatch log retention
- [x] Amplify manual deployment
- [x] GitHub Actions CI/CD workflow and least-privilege OIDC role template prepared (activation pending repository)

## Frontend

- [x] Heat/thermal visual language
- [ ] Product
- [x] How it works
- [x] Dashboard (historical replay mode)
- [x] Investigation status page (agent implementation pending)
- [x] Data & methodology
- [x] Error states
- [x] Loading states

## Quality
- [ ] Acceptance criteria checked
- [ ] Reproducibility checked
- [ ] Data drift checks run
- [ ] Cost guardrails verified


- [ ] Unit tests
- [ ] Integration tests
- [ ] Agent tests
- [ ] End-to-end test
- [ ] Security review
- [ ] Deployment smoke test
- [ ] Demo rehearsal
- [ ] Public GitHub
- [ ] Public demo URL

- [ ] Build-window compliance checked
- [ ] Open-Meteo weather source verified
- [ ] WorldPop source verified
- [ ] Geospatial dependencies tested
- [ ] Temporal leakage tests passed
- [ ] Attribution file complete
- [ ] Cost controls verified
- [ ] Replay mode clearly labelled

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
- [x] Deterministic scoring component and explicit versioned trigger config (input feature derivation still pending)
- [x] Replay event generation and stable IDs
- [x] Read-only API with validated filters, pagination, and gated investigation route
- [x] Responsive map-first replay dashboard with explicit historical labeling
- [x] Event evidence detail, investigation status, system overview, and data methodology screens
- [x] SAM template validated; private S3, DynamoDB GSI, API Gateway, and Lambda defined
- [x] Deploy AWS API/data stack and seed 250-cluster replay sample
- [x] Public dashboard deployed with Amplify; browser-origin CORS verified
- [ ] Complete feature derivation, population exposure, and investigation agent
