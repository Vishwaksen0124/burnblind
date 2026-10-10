# Secrets and credential locations

Audited: 2026-10-10. Secret values were not retrieved, logged, or copied.

## Application credentials

| Credential or configuration | Authoritative location | Runtime handling |
|---|---|---|
| NASA FIRMS MAP_KEY | AWS Secrets Manager, `burnblind/firms-map-key` in `us-east-2` (ARN suffix `KKIzmd`) | `scripts/fetch_firms_archive.py` reads it on demand. The value is not written to the repository, archive manifest, logs, or Lambda environment. Secret rotation is currently disabled. |
| AWS deployment credentials | GitHub Actions OIDC role assumption | Amplify and backend workflows assume repository-scoped AWS roles; no static AWS access key is required in GitHub. |
| AWS CLI session | AWS CLI `login` credential provider in the local user context | The audited AWS caller was the account root principal. Do not use root for routine ingestion or deployment; switch routine local operations to a least-privilege IAM role. No credential values are recorded here. |
| Reviewer passwords | Amazon Cognito user pool `burnblind-replay-reviewers` | Admin-provisioned accounts; temporary passwords are delivered by Cognito and changed at first sign-in. Passwords are not stored in BurnBlind. |
| Reviewer tokens | Browser tab session storage | Short-lived tokens are sent only to authenticated reviewer endpoints and cleared on sign-out/expiry. |
| Cognito pool/client IDs and API origin | GitHub Actions variables and compiled public frontend configuration | These identifiers are public configuration, not secrets. |
| Bedrock model access | Investigation Lambda execution role | Uses AWS IAM and Bedrock Mantle; no model API key is stored in application configuration. |

## Verification evidence

- AWS Secrets Manager metadata lists `burnblind/firms-map-key`; the secret's
  value was not requested during this audit.
- The secret has no explicit resource policy, replication, or rotation
  configuration. AWS Secrets Manager encrypts the secret at rest; review IAM
  access and rotate the MAP_KEY if its owner or scope changes.
- The deployed Event API Lambda environment contains table/queue names and CORS
  origins only; no FIRMS credential is injected into the function.
- The repository's GitHub Actions secret-name list was empty at audit time.
  Deployment uses GitHub OIDC; frontend IDs are supplied as Actions variables.
- Keep credentials out of command output, URLs, source files, manifests, test
  fixtures, browser storage, and logs. Do not read a secret merely to verify
  that it exists; inspect metadata and test through the credential-consuming
  code path instead.

## Follow-up

- Replace routine local root access with a scoped ingestion/deployment role.
- Review who can read `burnblind/firms-map-key` and set an intentional rotation
  plan with the MAP_KEY owner.
- Re-run this metadata-only audit after credential, IAM, or workflow changes.
