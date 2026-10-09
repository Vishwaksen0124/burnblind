# BurnBlind — Scoring Specification

## 1. Score types

BurnBlind must distinguish:

- raw feature
- normalized score
- heuristic likelihood score
- calibrated probability
- confidence

Do not use these terms interchangeably.

## 2. Monitoring blindness

Candidate components:

- observation gap
- data quality
- historical temporal risk
- sensor coverage/disagreement
- relevant observation availability

Illustrative baseline:

```text
blindness_score =
    w1 * observation_gap
  + w2 * sensor_coverage_gap
  + w3 * data_quality_risk
  + w4 * timing_risk
```

Weights are configuration, not scientific truth.

## 3. Fire likelihood

Candidate evidence:

- thermal anomaly
- historical fire activity
- independent active-fire reference
- sensor agreement/disagreement
- observation quality

Initial MVP may use a transparent heuristic. A later classifier is optional.

## 4. Impact

```text
impact =
    downwind_exposure
    × evidence_confidence
```

The exact formula must be versioned.

## 5. Priority

Priority should combine:

```text
fire_likelihood
×
monitoring_blindness
×
potential_exposure
×
urgency
```

Normalize each component before combining.

Do not claim this formula is scientifically validated merely because it produces a useful ranking.

When required components are unavailable, the system may expose a clearly
labelled `PROVISIONAL_MISSING_COMPONENTS` priority using only the available
fire-likelihood and exposure components. This is a triage aid, not the final
priority formula. Final priority remains unavailable until blindness and
urgency inputs are present.

## 6. Validation

The released GK2A dataset and FIRMS observations are observational/reference data, not perfect ground truth.

Therefore:

- evaluate ranking quality against reference detections where possible
- use temporal holdout periods
- report limitations
- avoid claiming true recall/precision against unknown ground truth

## 7. Temporal leakage

For any historical event at time T, only information available at or before T may be used.

Never use:
- future FIRMS detections
- future weather
- full-season counts that include post-event records
- post-event labels as features

## 8. Configuration

All weights and thresholds live in `docs/CONFIGURATION.md` / versioned config.

## 9. Investigation qualification

`backend/scoring/stream_trigger.py` evaluates an event when a deterministic
producer writes a `score_features` map to the Events table. The map uses the
`ScoreFeatures` field names above and normalized `[0, 1]` numeric values. The
stream stores the score version, completeness, trigger reasons, and a
fingerprint to prevent duplicate evaluation of unchanged inputs.

High priority, high uncertainty, high blindness with moderate fire likelihood,
or high exposure qualifies under `config/scoring.v1.json`. High uncertainty
requires a supported fire-likelihood score so an empty feature map does not
queue every candidate. Seeded replay candidates currently have no
`score_features`, so they remain visible without an automatic investigation.

Every event stores the scoring version.

## Current deterministic baseline

`backend/scoring/engine.py` implements versioned weighted means for blindness
and heuristic fire-likelihood inputs. The tracked `config/scoring.v1.json`
contains placeholder weights and trigger thresholds; they are not calibrated
or scientifically validated. The output is a ranking aid, not a probability.

Missing input features are omitted from the corresponding weighted mean and
reduce `evidence_completeness`. If blindness or likelihood inputs are wholly
missing, that score is `null`. Priority uses the specified product of
blindness, fire-likelihood, exposure, and urgency; it is `null` if any of
those inputs is unavailable. Sensor disagreement increases uncertainty and
does not increase fire likelihood by itself.
