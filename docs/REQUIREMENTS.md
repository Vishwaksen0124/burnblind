# BurnBlind — Hackathon & Product Requirements

## 1. Hackathon requirements

BurnBlind is being built for WeMakeDevs × AWS Bharat Builds Tour — Environmental Hacks.

Official event page:
https://www.wemakedevs.org/aws/env

Official rules:
https://www.wemakedevs.org/aws/rules

Checked against the official rules page on 2026-10-08. The current rulebook
requires project work to start when the event opens, use AWS (an AWS open
source project or AWS services), and show that use in the demo video. It also
requires a public repository, a YouTube demo of at most three minutes, and a
short project/AWS write-up. Confirm the event-page deadline and Builder Center
verification before submission.

### Current rules that affect implementation

- The project must fit one of the environmental tracks.
- BurnBlind fits the **Air** track through stubble-burning/fire monitoring and exposure.
- Teams can build locally with AWS open-source tools, deploy on AWS, or use both.
- To be eligible for prizes, the project must use at least one AWS open-source tool or be deployed on AWS.
- The event expects a working project and a recorded demo.
- Project work starts when the hackathon starts; learning/practice beforehand is allowed.
- The event page states that judging considers idea/impact, AWS usage, design/usability, execution, and the three-minute demo.
- The submission must follow the event's current submission requirements and deadline.

### AWS Build → Ship alignment

For BurnBlind:

**Build It**

- Strands Agents SDK
- SAM CLI

**Ship It**

- Amplify Hosting
- API Gateway
- Lambda
- S3
- DynamoDB
- SQS
- EventBridge
- CloudWatch
- SageMaker AI if used as the model-serving layer

The architecture should not require every service listed by the event.

## 2. Product requirements

### P0 — Mandatory

- Historical fire data ingestion
- Current/near-current observation ingestion or replay
- Spatial/temporal normalization
- Monitoring-blindness calculation
- Fire-likelihood calculation
- Impact/exposure estimate
- Event priority
- Investigation Agent
- Evidence-backed agent output
- Operational dashboard
- Event investigation view
- AWS deployment or AWS open-source usage
- Tests
- Public documentation
- Reproducible demo path

### P1 — Strongly recommended

- Multi-sensor comparison
- SQS-based asynchronous processing
- EventBridge scheduling
- CloudWatch observability
- Agent evaluation suite
- Human-review status
- Evidence timeline

### P2 — Stretch

- Real-time/current GK2A processing
- Additional sensitive locations
- More advanced smoke dispersion
- Model-based fire classifier
- Automated feedback loop
- Authentication
- Notifications

## 3. Definition of product success

A judge should be able to understand within one minute:

1. what problem exists,
2. what BurnBlind observes,
3. why a blind spot matters,
4. why the event is prioritized,
5. what the Investigation Agent adds,
6. where AWS is used.

## 4. Eligibility note

The official rules state that entrants must be university students in India aged 18+ and require verified university enrollment on AWS Builder Center.

Eligibility must be checked against the organizer's current verification system. Do not hard-code personal eligibility assumptions into the project.

## 5. Build-window compliance

The official rules state that learning, planning and practice may happen before the event, but project work must start when the hackathon opens.

Environmental Hacks runs online **October 8–11, 2026**. The optional in-person build day is October 10 at DTU.

Before the opening:

Allowed:
- architecture/design
- documentation
- learning
- research
- tool installation
- local environment setup
- dataset/source research
- test-plan design

Do not create the actual hackathon project implementation before the opening.

During the event:
- implementation
- integration
- project-specific code
- project-specific UI
- project-specific infrastructure
- project-specific model/agent work

must be created during the event.

Keep repository history consistent with the event rules.

## 6. Submission evidence

The submission consists of:

1. public repository
2. YouTube demo video of up to 3 minutes
3. short write-up covering the problem, build and AWS usage

Judges evaluate what is submitted. A feature that exists only in documentation but is not demonstrated does not count.

Therefore every P0 feature must have:
- a working implementation,
- a visible UI/API path,
- a test,
- and a demo path where practical.

## 7. Track positioning

BurnBlind should enter the **Air** track.

The environmental problem is agricultural-fire monitoring and potential smoke exposure.

The product story should focus on the actionable consequence:

> detecting and investigating poorly observed fire events before they become harder-to-monitor exposure events.

## 8. Eligibility

The official rules currently state that entrants must be university students in India and 18+, with university enrollment verified through AWS Builder Center.

Because eligibility is personal and can change, the repository must not claim the individual is eligible. Verify the user's Builder Center status before submission.
