# BurnBlind

## Environmental Monitoring & Incident Investigation Platform

BurnBlind is an environmental intelligence platform that identifies situations where satellite fire monitoring may be incomplete, evaluates multiple independent evidence sources, estimates potential impact, prioritizes events, and invokes an **Investigation Agent** for high-priority or uncertain cases.

### Core pipeline

```text
Satellite / Environmental Data
            ↓
         Observe
            ↓
  Monitoring Blindness
            ↓
    Fire Verification
            ↓
     Impact Estimation
            ↓
      Priority Score
            ↓
 Investigation Agent
            ↓
 Evidence-backed Recommendation
            ↓
       Human Operator
```

## MVP

**Geography:** Punjab + Haryana, India.

**Primary scenario:** agricultural-fire monitoring.

**Primary user:** an environmental monitoring/operator persona who needs to know which potential events deserve attention first.

## Product pages

1. Product overview
2. How it works
3. Monitoring dashboard
4. Event investigation
5. Documentation


## Documentation index

| Document | Purpose |
|---|---|
| `docs/REQUIREMENTS.md` | Hackathon and product requirements |
| `docs/PRODUCT.md` | Product behavior and user workflow |
| `docs/PROBLEM.md` | Problem and scientific framing |
| `docs/DATA_SOURCES.md` | Actual datasets, provenance and acquisition order |
| `docs/DATA_CONTRACTS.md` | Canonical data schemas and status enums |
| `docs/SCORING.md` | Scoring inputs, outputs and versioning |
| `docs/TOOL_CONTRACTS.md` | Investigation Agent tool contracts |
| `docs/DATA_ARCHITECTURE.md` | Data model and storage |
| `docs/SYSTEM_DESIGN.md` | Detailed system behavior |
| `docs/ARCHITECTURE.md` | Component architecture |
| `docs/AWS_ARCHITECTURE.md` | AWS Build → Ship mapping |
| `docs/INVESTIGATION_AGENT.md` | Agent design and tools |
| `docs/AGENT_EVALUATION.md` | Agent evaluation |
| `docs/FRONTEND_DESIGN.md` | Heat/thermal frontend design system |
| `docs/API_SPEC.md` | API contract |
| `docs/CONFIGURATION.md` | Thresholds and environment configuration |
| `docs/IMPLEMENTATION_PLAN.md` | Ordered build checklist |
| `docs/TESTING.md` | Test strategy |
| `docs/ACCEPTANCE_CRITERIA.md` | Definition of done |
| `docs/DEPLOYMENT.md` | Deployment sequence |
| `docs/GITHUB_CI_CD.md` | GitHub Actions build and Amplify deployment automation |
| `docs/OBSERVABILITY_RUNBOOK.md` | Logs, metrics and failure response |
| `docs/SECURITY.md` | Security controls |
| `docs/COST_CONTROL.md` | AWS cost guardrails |
| `docs/ATTRIBUTION.md` | Data/software attribution |
| `docs/DECISIONS.md` | Architecture decisions |
| `docs/DEMO.md` | Three-minute demo |
| `docs/LIMITATIONS.md` | Scientific and product limitations |
| `docs/CHECKLIST.md` | Final checklist |
| `docs/FILE_STRUCTURE.md` | Repository structure |
| `docs/AGENT_INSTRUCTIONS.md` | Instructions for coding agents |

## AWS Build → Ship

### Build It

- Strands Agents SDK
- SAM CLI
- Local/sample data
- Standard Python/React development

### Ship It

- Amplify Hosting
- GitHub Actions + AWS OIDC for automated frontend CI/CD
- API Gateway
- Lambda
- S3
- DynamoDB
- SQS
- EventBridge
- CloudWatch
- Model provider / SageMaker AI if appropriate

## Scientific framing

BurnBlind must not claim that a sensor "missed" a fire unless independent ground truth supports that statement.

Use:

- monitoring blind spot
- observability gap
- cross-sensor disagreement
- potential fire event
- investigation priority

Sensor disagreement is evidence to investigate, not automatic proof of a missed fire.

## Core principle

The deterministic environmental pipeline calculates the environmental intelligence.

The Investigation Agent investigates important or uncertain events using tools and evidence. It does not replace the scoring engine.

## Repository

See `docs/ARCHITECTURE.md`, `docs/SYSTEM_DESIGN.md`, and `docs/IMPLEMENTATION_PLAN.md` before implementation.

## Actual MVP data sources

- GK2A 2019–2025 Punjab/Haryana fire dataset: https://zenodo.org/records/20084790
- NASA FIRMS active-fire data: https://firms.modaps.eosdis.nasa.gov/active_fire/
- NOAA GK2A AWS Open Data: https://registry.opendata.aws/noaa-gk2a-pds/

See `docs/DATA_SOURCES.md` for provenance and acquisition rules.

## Current implementation

The backend includes canonical data contracts, a metric 5 km grid, a
version-pinned GK2A historical downloader and normalizer, reproducible
historical summaries, candidate event grouping, and a read-only replay API.
The React frontend provides a map-first 2025 replay, source-backed event
details, investigation status, a six-step system overview, and data/methodology
pages. It omits unavailable scores and agent conclusions rather than filling
them with placeholder values. The Investigation Agent is not implemented yet. A SAM template defines the HTTP API, DynamoDB replay index,
and private encrypted S3 bucket. Scorer weights remain unvalidated
placeholders. The ERA5 wind adapter and geodesic screening corridor exist;
population exposure and the investigation agent remain unimplemented.

### Local data workflow

Python 3.11+ is required. Install the project and development tools:

```bash
python -m pip install -e ".[dev]"
```

Fetch and validate the pinned Zenodo v1 source data. For the full historical
baseline, use the commands below. `--year 2025` downloads only two files and is
intended for a smaller acquisition/parser check.

```bash
python scripts/fetch_gk2a_historical.py
python scripts/normalize_gk2a_release.py
python scripts/build_gk2a_history.py
python scripts/create_gk2a_sample.py
python -m pytest
```

Run the local replay stack in separate terminals after creating the sample:

```bash
python scripts/serve_api.py
cd frontend && npm install && npm run dev
```

Open `http://127.0.0.1:5173`. The dashboard is labeled
`HISTORICAL REPLAY · 2025`; it is not a live feed. Candidate clusters are not
confirmed fires, and scores remain unavailable.

To run the local dashboard against the deployed AWS API, use:

```bash
cd frontend
VITE_API_BASE_URL=https://ad4m8eny2m.execute-api.us-east-2.amazonaws.com/prod/api npm run dev
```

For a single 2025 file, run `python scripts/normalize_gk2a.py PATH_TO_FILE`
after the `--year 2025` download. The full summary/sample builders require all
14 regional/year source files.

Raw and processed data are excluded from Git. The downloader verifies the
publisher's checksums and writes `data/raw/gk2a/manifest.json`; do not edit raw
files in place. The normalization preserves the source confidence flag and
thermal measurements, converts source timestamps from IST to UTC, and assigns
cells after projecting coordinates into UTM zone 43N. Attribution and use
limitations are recorded in `docs/DATA_SOURCES.md` and `docs/ATTRIBUTION.md`.

The NASA FIRMS archive adapter is also implemented. Archive retrieval requires
a free MAP_KEY from NASA; set `FIRMS_MAP_KEY` in your local environment before
running `python scripts/fetch_firms_archive.py`. The key is never written to
the repository. FIRMS acquisition and cross-sensor analysis remain incomplete
until those source files are obtained and validated.

### AWS deployment

Install the AWS extras and use AWS SAM CLI:

```bash
python -m pip install -e '.[aws]'
sam build --template-file infrastructure/sam/template.yaml
sam deploy --stack-name burnblind-replay --resolve-s3 --capabilities CAPABILITY_IAM \
  --parameter-overrides DashboardOrigin=https://main.d3k8g1d6au7814.amplifyapp.com
```

Set `EVENT_TABLE` to the stack output and seed the sample with
`python scripts/seed_dynamodb.py`. Set `VITE_API_BASE_URL` to the deployed
`ApiBaseUrl` plus `/api`, then build and publish through Amplify:

```bash
cd frontend
VITE_API_BASE_URL=https://ad4m8eny2m.execute-api.us-east-2.amazonaws.com/prod/api npm run build
cd ..
python scripts/deploy_amplify_manual.py --app-id d3k8g1d6au7814 --branch main
```

The dashboard is live at
https://main.d3k8g1d6au7814.amplifyapp.com. This is a manual Amplify
deployment without a Git provider connection. The API allows this hosted
origin and the local Vite origin. The API is deployed in `us-east-2` at
`https://ad4m8eny2m.execute-api.us-east-2.amazonaws.com/prod`; its Events table
contains 250 replay clusters. The sample JSONL and its CC BY 4.0 provenance
manifest are stored under the private S3 `replay/` prefix. Raw research data
is not uploaded.
