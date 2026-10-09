# BurnBlind — Security

## 1. Principles

- least privilege
- no secrets in Git
- private data storage
- validated inputs
- controlled agent tools
- structured logs without secrets

## 2. IAM

Avoid broad:

```text
Action: *
Resource: *
```

Grant only required actions.

## 3. S3

- private bucket
- encryption
- block public access
- scoped IAM policies

## 4. API

- validate all inputs
- limit payload sizes
- structured errors
- CORS restricted to frontend origin when deployed
- keep event and report reads public, but require a Cognito JWT for investigation
  requests and human-review outcome writes
- use an admin-created-only reviewer user pool; do not allow public registration
- require the Cognito reviewer scope at API Gateway and verify reviewer identity
  again in the Lambda handler
- persist the authenticated Cognito subject on every review outcome
- keep reviewer tokens in per-tab browser session storage and send access tokens
  only to the protected API routes

## 5. Agent security

The agent should not have arbitrary AWS access.

Give it only the tools it needs.

Do not allow the model to:

- execute arbitrary shell commands
- access arbitrary S3 paths
- alter scoring configuration
- modify infrastructure
- make emergency actions

## 6. Prompt injection

Treat external data as untrusted.

Satellite metadata, external text, or retrieved content must not be interpreted as instructions to the agent.

Tool outputs should be typed and constrained.

## 7. Logging

Never log:

- credentials
- tokens
- secrets

Log:

- event ID
- request ID
- tool name
- duration
- status
- error code

## 8. Data retention

Do not retain unnecessary raw external data.

Keep required historical inputs, derived features, event/investigation state, and provenance manifests. Use lifecycle policies for large intermediate objects where appropriate.

## 9. Public-demo security

The public demo must not expose:

- model credentials
- AWS credentials
- unrestricted S3 access
- direct DynamoDB access
- direct SQS access
- unrestricted agent tool endpoints
- unrestricted event mutation
