# BurnBlind — Deployment Guide

## 1. Local development

Required:

- Python
- Node.js
- AWS CLI
- SAM CLI
- Docker if required by local runtime
- Strands Agents SDK
- frontend package manager

## 2. Local workflow

```text
Run backend
Run frontend
Load sample data
Execute processing
Open dashboard
Trigger investigation
Inspect result
```

## 3. AWS deployment order

The current SAM stack provisions the replay API, Events table, and private
encrypted artifact bucket. Queue workers, scheduled ingestion, and
investigations are later phases. Build and deploy the API/data stack with:

```text
sam build --template-file infrastructure/sam/template.yaml
sam deploy --stack-name burnblind-replay --resolve-s3 --capabilities CAPABILITY_IAM \
  --parameter-overrides DashboardOrigin=https://main.d3k8g1d6au7814.amplifyapp.com
```

Set `DashboardOrigin` to the Amplify branch URL and retain the local Vite
origin in `LocalDashboardOrigin`. Seed only the sample using
`EVENT_TABLE=<stack output> python scripts/seed_dynamodb.py`. Build the client
with `VITE_API_BASE_URL=<ApiBaseUrl>/api`, then publish its `dist/` contents
using `python scripts/deploy_amplify_manual.py --app-id d3k8g1d6au7814 --branch main`.
This manual Amplify app is not linked to a Git provider. Raw and processed
archives are not deployed.

Agent model configuration should be completed before enabling automated investigations.

## 4. Deployment checklist

- [ ] AWS region selected
- [ ] credentials configured
- [x] least-privilege API Lambda IAM role deployed
- [x] SAM template defines private encrypted S3 bucket
- [x] SAM template defines Events table and `data-mode-detected-at` GSI
- [x] AWS API/data stack deployed in `us-east-2`
- [x] 250-cluster replay sample seeded
- [x] replay JSONL and provenance manifest stored in private S3
- [x] API CORS verified for Amplify and local Vite origins
- [x] Amplify manual app and production branch created
- [ ] SQS deployed
- [x] API Lambda deployed
- [ ] EventBridge deployed
- [x] API Gateway deployed
- [x] CloudWatch log group with 14-day retention verified
- [x] Amplify deployed
- [ ] model configured
- [ ] environment variables configured
- [x] public Amplify URL returns HTTP 200

## 5. Smoke tests

```text
GET /health
GET /summary
GET /events
GET /events/{id}
POST /events/{id}/investigate
GET /events/{id}/investigation
```

## 6. Rollback

Keep deployment versioned.

If the latest deployment fails:

1. disable automated processing
2. revert Lambda/API version
3. verify data remains intact
4. rerun smoke tests
5. re-enable schedule
