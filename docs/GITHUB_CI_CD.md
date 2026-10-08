# GitHub Actions → Amplify CI/CD

## Workflow behavior

- Pull requests targeting `main` install locked npm dependencies, run the npm
  advisory check, and build the dashboard. They do not deploy.
- Pushes to `main` do the same checks, then request short-lived AWS credentials
  through GitHub OIDC and publish the build to the existing Amplify `main`
  branch.
- AWS credentials are not stored in GitHub secrets. The role is restricted to
  one repository's `main` branch and can publish only this Amplify branch.

The publisher uses Amplify's manual deployment API. That is the deployment
mechanism; the CI/CD trigger and build are automatic on every push to `main`.
This avoids granting Amplify a long-lived GitHub token.

## Setup after the repository exists

1. Deploy `infrastructure/sam/github-actions-role.yaml` with the exact GitHub
   owner and repository name. It creates the GitHub OIDC provider and a role
   scoped to the configured repo/branch and Amplify app.
2. Add the output `GitHubActionsRoleArn` as the repository variable
   `AWS_DEPLOY_ROLE_ARN`.
3. Push the workflow to `main`. Pull requests build without deploying; merges
   and direct pushes to `main` publish the Amplify site.

Repository: <https://github.com/Vishwaksen0124/burnblind>  
Amplify app: `d3k8g1d6au7814`  
Amplify branch: `main`  
Site: <https://main.d3k8g1d6au7814.amplifyapp.com>

The GitHub Actions workflow and least-privilege role template are included in
this repository. The role and repository variable must be configured in AWS
and GitHub before pushes can deploy.
