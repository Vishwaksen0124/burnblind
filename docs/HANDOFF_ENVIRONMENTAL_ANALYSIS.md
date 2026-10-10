# Handoff: Environmental Analysis and AWS Verification

Updated 2026-10-10.

See [DATA_QUALITY_AUDIT_2026-10-10.md](DATA_QUALITY_AUDIT_2026-10-10.md) for
the completed 250-event production audit, corrections, and live verification.

## Verified current state

- Backend and frontend deploy through the existing GitHub Actions OIDC workflows. Backend runs execute unit tests, SAM validation/build, deploy the SAM stack, and smoke-test the live API.
- Commits `792904f`, `aacd856`, `c0e3a2e`, and `6ed6547` fixed stale feature fallbacks and derived-evidence pagination. The latest backend deployment completed successfully in workflow `38030910017`.
- Production `/api/map-layers?layer=sensor-disagreement&limit=250` returns four source-matched comparisons, all `AGREEMENT`: two against `MODIS_AQUA`, one `VIIRS_NOAA20`, and one `VIIRS_SNPP`. Each has attached source evidence IDs. Agreement is not fire confirmation.
- After the 2026-10-10 repair, the production exposure map layer returns sourced estimates for all 250 replay events; the blind-spot layer correctly returns unavailable with 0 items because valid coverage/observability inputs are absent. Do not synthesize absent data.
- The 250 event environmental projections now agree with source evidence. Four sensor comparisons are unique and source matched; all report agreement, which is not confirmation. Two positive detections previously mislabeled as coverage are preserved as observations and marked invalid for coverage scoring.
- Six NASA FIRMS observations were attached to four events from Oct–Nov 2025 reference archives. Raw and normalized source artifacts are in private S3 reference prefixes with manifests. Attachment does not launch investigations.
- The production artifact bucket has versioning enabled, noncurrent-version expiry at 90 days, and incomplete multipart upload cleanup at 7 days. Current object versions are retained. Verified from S3 after workflow `38031227320` succeeded.
- The CloudFormation execution role received `GetLifecycleConfiguration` and `PutLifecycleConfiguration` scoped to `arn:aws:s3:::burnblind-replay-replayartifactbucket-*`. This was required after the first backend deployment rolled back on `PutLifecycleConfiguration` AccessDenied.

## CI/CD and one-time role update

Application and SAM changes deploy through `.github/workflows/backend-deploy.yml` and GitHub OIDC; frontend changes use `.github/workflows/amplify-deploy.yml`. The code and SAM changes described here were deployed by those workflows.

The one separate AWS CLI operation updated the existing `burnblind-github-actions-deploy` role stack. The backend workflow's CloudFormation execution role lacked permission to install the approved bucket lifecycle policy. The added permissions are restricted to the BurnBlind artifact-bucket name pattern. The normal backend workflow then deployed SAM successfully.

## Relevant fixes

- `backend/api/feature_views.py`: source-derived evidence takes precedence over stale event summaries; unavailable placeholders no longer hide usable records.
- `backend/agent/evidence.py`: latest derived-record reads page the evidence GSI newest-first until the requested evidence type appears.
- `backend/processing/evidence_comparison.py`: only explicit, quality-valid negative coverage records can represent coverage; positive detection rows remain observations.
- `infrastructure/sam/template.yaml`: artifact bucket versioning/lifecycle policy.
- `infrastructure/sam/github-actions-role.yaml`: narrowly scoped lifecycle permissions for the CloudFormation execution role.

## Remaining release gates

Investigation remains an explicit event-scoped action; attaching environmental evidence does not invoke Strands or queue all events. Lack of an observation is not treated as a non-detection, and absent features must not be fabricated.

Complete reviewer sign-in and authenticated review submission, browser visual/accessibility review, broader live-source checks, and end-to-end failure-path coverage remain outstanding. API smoke tests do not verify those gates.

## Secrets

See [SECRETS_AUDIT.md](SECRETS_AUDIT.md). The NASA FIRMS MAP_KEY is stored in AWS Secrets Manager under `burnblind/firms-map-key`; only metadata was inspected. Never retrieve or put secret values in source, logs, manifests, or chat.
