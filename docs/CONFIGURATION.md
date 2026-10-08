# BurnBlind — Configuration

## 1. Configuration principle

No important threshold should be buried inside application code.

Keep:

- scoring thresholds
- agent trigger thresholds
- grid configuration
- data source configuration
- feature versions
- model configuration

in versioned configuration.

## 2. Example

```yaml
scoring:
  version: v1
  blindness_high: 0.70
  fire_likelihood_moderate: 0.50
  priority_high: 0.75
  exposure_high: 50000

agent:
  enabled: true
  trigger_priority: 0.75
  trigger_uncertainty: 0.70

grid:
  version: v1
  cell_size_km: 5

data:
  timezone: Asia/Kolkata
```

These values are placeholders until validated.

The active versioned baseline is `config/scoring.v1.json`. Its weights are
only a transparent heuristic configuration; do not describe the scores as
calibrated probabilities. Keep source-specific feature normalization outside
the scorer and record the config version with every derived event.

## 3. Environment variables

Example:

```text
AWS_REGION
S3_BUCKET
EVENT_TABLE
INVESTIGATION_TABLE
PROCESSING_QUEUE_URL
INVESTIGATION_QUEUE_URL
MODEL_ENDPOINT
LOG_LEVEL
ENVIRONMENT
```

Never commit secrets.

## 4. Versioning

Record:

- scoring version
- feature version
- agent version
- prompt version
- tool version
- data source version

with every investigation.
