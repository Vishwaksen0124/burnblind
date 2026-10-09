# GitHub Actions → Amplify and SAM CI/CD

## Workflow behavior

- Pull requests targeting `main` install locked npm dependencies, run the npm
  advisory check, and build the dashboard. They do not deploy.
- Pushes to `main` do the same checks, then request short-lived AWS credentials
  through GitHub OIDC and publish the build to the existing Amplify `main`
  branch.
- The dashboard workflow can also be dispatched manually for configuration-
  only frontend rebuilds after the backend stack has produced public outputs.
- AWS credentials are not stored in GitHub secrets. The role is restricted to
  one repository's `main` branch and can publish only this Amplify branch.
- `.github/workflows/backend-deploy.yml` runs backend unit tests, SAM lint
  validation, and SAM packaging on pull requests and relevant pushes. A push
  to `main` deploys only the `burnblind-replay` stack through a separate OIDC
  role and a CloudFormation execution role protected by the
  `BurnBlindRuntimeBoundary` permissions boundary.
- No static AWS credentials are required in GitHub. The backend workflow reads
  only these repository variables: `AWS_BACKEND_DEPLOY_ROLE_ARN` and
  `BURNBLIND_CFN_EXECUTION_ROLE_ARN`.
- The Amplify build reads public, non-secret reviewer configuration from
  `REVIEWER_USER_POOL_ID` and `REVIEWER_USER_POOL_CLIENT_ID`. These are Cognito
  resource identifiers, not credentials. Reviewer passwords and tokens are
  never CI variables or secrets.

The publisher uses Amplify's manual deployment API. That is the deployment
mechanism; the CI/CD trigger and build are automatic on every push to `main`.
This avoids granting Amplify a long-lived GitHub token.

## Setup after the repository exists

1. Deploy/update `infrastructure/sam/github-actions-role.yaml` with the exact
   GitHub owner/repository identity values already recorded in the
   `burnblind-github-actions-deploy` stack. It adds a stack-scoped backend
   deploy role, a CloudFormation execution role, and a permissions boundary.
2. Keep the existing output `GitHubActionsRoleArn` in repository variable
   `AWS_DEPLOY_ROLE_ARN`; add `GitHubActionsBackendRoleArn` as
   `AWS_BACKEND_DEPLOY_ROLE_ARN` and `BurnBlindCloudFormationExecutionRoleArn`
   as `BURNBLIND_CFN_EXECUTION_ROLE_ARN`.
3. Push to `main`. The frontend workflow publishes Amplify; the backend
   workflow validates/tests/builds and deploys the SAM stack on relevant code
   changes. Pull requests never deploy.

Repository: <https://github.com/Vishwaksen0124/burnblind>  
Amplify app: `d3k8g1d6au7814`  
Amplify branch: `main`  
Site: <https://main.d3k8g1d6au7814.amplifyapp.com>

Both GitHub Actions workflows and the role template are included in this
repository. The OIDC roles and repository variables must be configured before
pushes can deploy. The NASA FIRMS MAP_KEY is a separate runtime secret: keep it
in AWS Secrets Manager and pass only its ARN/name when ingestion is connected;
never add it to GitHub variables, secrets, logs, or source files.
