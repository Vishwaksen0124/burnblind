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

The SAM stack provisions the replay API, encrypted event/evidence/investigation
tables, a FIFO request queue, and an on-demand Strands worker. Investigations
are queued automatically when persisted normalized score features satisfy the
configured qualification policy. Candidate replay rows without score features
are skipped; an analyst override remains available. Build and deploy with:

```text
sam build --template-file infrastructure/sam/template.yaml
sam deploy --stack-name burnblind-replay --resolve-s3 --capabilities CAPABILITY_IAM \
  --parameter-overrides DashboardOrigin=https://main.d3k8g1d6au7814.amplifyapp.com \
    InvestigationModelProvider=bedrock-mantle DeepSeekModelId=deepseek.v3.2
```

Set `DashboardOrigin` to the Amplify branch URL and retain the local Vite
origin in `LocalDashboardOrigin`. Seed candidate and attached source records
using `EVENT_TABLE=<stack output> EVIDENCE_TABLE=<stack output> python scripts/seed_dynamodb.py`.
Push frontend changes to `main` to run `.github/workflows/amplify-deploy.yml`,
which builds the frontend, audits npm dependencies, assumes the AWS deploy role
through GitHub OIDC, and publishes the build to Amplify. The backend SAM stack
is built and deployed by `.github/workflows/backend-deploy.yml` on relevant
changes to `main`. Both pipelines use repository-scoped GitHub OIDC roles; no
static AWS credentials are stored in GitHub. The Amplify app is published by
GitHub Actions rather than linked directly to a Git provider. Raw and processed
archives are not deployed.

### Reviewer authentication

The SAM stack provisions a Cognito user pool with self-registration disabled,
a public app client, and an API Gateway JWT authorizer. Event and investigation
reads remain public. Investigation requests and human-review outcome writes
require the `aws.cognito.signin.user.admin` access-token scope. The Lambda
handler also requires the validated JWT subject, which it stores as the review
author. Cognito user-pool and client IDs are public configuration, not secrets.

After the first authenticated backend deployment, set the Amplify workflow
repository variables `REVIEWER_USER_POOL_ID` and
`REVIEWER_USER_POOL_CLIENT_ID` from the stack outputs. The browser sign-in uses
the Cognito user-pool API and keeps its short-lived session in session storage.
Reviewer accounts must be provisioned by an AWS administrator; do not enable
public sign-up. Example administrator action:

```sh
aws cognito-idp admin-create-user \
  --user-pool-id "$REVIEWER_USER_POOL_ID" \\
  --username reviewer@example.org \\
  --user-attributes Name=email,Value=reviewer@example.org Name=email_verified,Value=true \
  --region us-east-2
```

Do not commit a reviewer password or paste it into chat. Complete the temporary
password challenge through the sign-in screen.

The investigator uses Strands Agents with Amazon Bedrock DeepSeek V3.2
(`deepseek.v3.2`) through the `bedrock-mantle` OpenAI-compatible endpoint in
the stack region. The verified Mantle call succeeded with the existing AWS
credentials. The worker role grants `bedrock-mantle:CreateInference` only for
the account's default project, plus the required Mantle bearer-token action.
Its separate Bedrock Runtime permission is scoped to the configured model.
Reserved concurrency is two. The stack has no
scheduled agent trigger. The DynamoDB stream qualification worker runs only
when score features are attached; the current replay seeder does not derive
those features. After adding the missing
`bedrock-mantle:CallWithBearerToken` permission, a retry of one previously
failed event completed and its source-cited report was persisted to DynamoDB.
The Lambda log for that invocation contains no error.

The Amplify publish workflow assumes the role provisioned by
`infrastructure/sam/github-actions-role.yaml`. GitHub OIDC subjects include
immutable owner and repository IDs, so pass both the owner/repository names
and IDs when creating that stack. For this repository those IDs are
`169535794` and `1409821450`.

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
- [x] Amplify app and production branch created
- [x] FIFO investigation queue and dead-letter queue defined
- [x] DynamoDB stream score qualification worker defined
- [x] API Lambda deployed
- [ ] EventBridge deployed
- [x] API Gateway deployed
- [x] CloudWatch log group with 14-day retention verified
- [x] Amplify deployed
- [x] DeepSeek model ID and worker environment configured
- [x] investigation worker environment configured
- [x] public Amplify URL returns HTTP 200
- [ ] Reviewer Cognito authorizer deployed and authenticated mutation smoke tested

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
