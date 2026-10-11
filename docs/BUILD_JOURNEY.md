# BurnBlind build journey

This guide follows the project through its real, dated Git history. The
repository retains the incremental implementation commits; this page groups
them by product milestone so reviewers can follow the work without reading
every individual fix in sequence.

Hackathon implementation began on **October 8, 2026**. The cited hashes point
to the current `main` history. Later fixes are preserved as separate commits.

## 1. Define the problem and make the replay reproducible — October 8

- [1be6681 — establish the architecture and implementation plan](https://github.com/Vishwaksen0124/burnblind/commit/1be6681)
- [35931ff — add the replay-data and backend-processing foundation](https://github.com/Vishwaksen0124/burnblind/commit/35931ff)

The project began with a bounded geography and historical agricultural-fire
scenario. The first implementation established canonical observation contracts,
time and coordinate handling, candidate-event grouping, and a reproducible
historical replay. This kept the product grounded in sourced events before
building the interface around them.

## 2. Put the evidence on a map — October 8

- [5f5ece4 — build the map-first monitoring experience](https://github.com/Vishwaksen0124/burnblind/commit/5f5ece4)
- [6586652 — build the product landing experience](https://github.com/Vishwaksen0124/burnblind/commit/6586652)
- [06d8465 — label replay mode accurately](https://github.com/Vishwaksen0124/burnblind/commit/06d8465)

The UI was shaped around event location, observation time, and source evidence.
The replay label makes clear that this is historical data rather than a live
alert feed.

## 3. Add the event-scoped investigation agent — October 8

- [962d57f — add the score-triggered Strands investigation agent](https://github.com/Vishwaksen0124/burnblind/commit/962d57f)
- [c4cad73 — route Strands through Bedrock Mantle](https://github.com/Vishwaksen0124/burnblind/commit/c4cad73)
- [f73fbea — adopt the evidence-grounded investigation prompt](https://github.com/Vishwaksen0124/burnblind/commit/f73fbea)
- [2ab9cac — render structured investigation conclusions](https://github.com/Vishwaksen0124/burnblind/commit/2ab9cac)

Strands is the agent framework; Amazon Bedrock Mantle is the model provider,
configured separately. The investigation is scoped to one selected event and
returns a structured, evidence-cited report. The agent supports human review;
it does not certify a fire or make emergency decisions.

## 4. Ship the first AWS deployment — October 8–9

- [7cbc348 — automate Amplify deployment with GitHub OIDC](https://github.com/Vishwaksen0124/burnblind/commit/7cbc348)
- [d17aaf9 — add scoped backend deployment automation](https://github.com/Vishwaksen0124/burnblind/commit/d17aaf9)
- [62c97cd — protect browser mutation routes](https://github.com/Vishwaksen0124/burnblind/commit/62c97cd)

The hosted React app and SAM backend gained separate GitHub Actions workflows.
AWS credentials are obtained through repository-scoped OIDC role assumption,
and reviewer mutations are protected by Cognito JWT authorization.

## 5. Add environmental evidence and human review — October 9

- [0c249cf — add sourced investigation context and review workflows](https://github.com/Vishwaksen0124/burnblind/commit/0c249cf)
- [550df48 — add source-based environmental analysis](https://github.com/Vishwaksen0124/burnblind/commit/550df48)
- [f966d00 — add dedicated event-review pages](https://github.com/Vishwaksen0124/burnblind/commit/f966d00)
- [904b7c3 — refine monitoring and investigation review UI](https://github.com/Vishwaksen0124/burnblind/commit/904b7c3)

The workflow separates deterministic environmental evidence from the LLM
investigation. Reviewers can inspect a compact investigation queue, open an
event-specific report, and record a human outcome through the protected API.

## 6. Integrate and verify independent source records — October 9–10

- [629a692a — attach source-backed FIRMS observations](https://github.com/Vishwaksen0124/burnblind/commit/629a692a)
- [5bcb23b5 — normalize independent FIRMS sensor evidence](https://github.com/Vishwaksen0124/burnblind/commit/5bcb23b5)
- [5007e411 — prefer current evidence over stale event summaries](https://github.com/Vishwaksen0124/burnblind/commit/5007e411)
- [fb2a5691 — page through derived evidence reliably](https://github.com/Vishwaksen0124/burnblind/commit/fb2a5691)

The evidence comparisons use actual matched records, preserve source identity,
and distinguish agreement from confirmation. Open-Meteo ERA5 and WorldPop
provide labelled estimates for environmental context and screening-corridor
population exposure.

## 7. Audit the whole replay and correct unsupported values — October 10

- [6ed1c325 — keep blind-spot scores unavailable without valid inputs](https://github.com/Vishwaksen0124/burnblind/commit/6ed1c325)
- [f07a89ce — fix stale environmental evidence projections](https://github.com/Vishwaksen0124/burnblind/commit/f07a89ce)
- [b90dd3ad — document the 250-event production audit](https://github.com/Vishwaksen0124/burnblind/commit/b90dd3ad)

Reviewing production data exposed two positive detections mislabelled as sensor
coverage, repeated comparison pairs, and an obsolete exposure limitation. The
team corrected the source projections and rechecked all 250 events. Because the
replay lacks valid coverage measurements, the blind-spot layer now honestly
shows zero available scores instead of fabricated zeros.

## Why the commit history is incremental

The commits preserve the sequence of implementation, testing, deployment fixes,
and production-data corrections. The examples above are representative
milestones, not a replacement or reconstruction of Git history. For the full
dated record, see [all commits on `main`](https://github.com/Vishwaksen0124/burnblind/commits/main/).
