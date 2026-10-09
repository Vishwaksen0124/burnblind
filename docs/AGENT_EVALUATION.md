# BurnBlind — Investigation Agent Evaluation

## Goal

Determine whether the Investigation Agent is grounded, useful, and reliable enough for the hackathon demo.

## Implemented runtime

- Model: Amazon Bedrock Mantle `deepseek.v3.2` through Strands Agents; region
  comes from the Lambda region (`us-east-2` in the current deployment).
- Trigger: environmental analysis runs first for every new event; normalized
  score features are then evaluated against versioned
  `config/scoring.v1.json` thresholds. Investigation is available only after
  human review. Candidate rows with incomplete score inputs do not qualify.
- Tools: event summary, attached satellite records, historical context,
  Open-Meteo ERA5 wind, exposure availability, and attached source comparison.
- Guardrails: tools are read-only and scoped to the requested event; report
  evidence IDs must exactly match records returned by tools; confidence is
  null; conclusions remain advisory for human review.
- Runtime limits: output capped at 900 tokens and Lambda reserved concurrency
  capped at two. Latency has not been benchmarked.

The agent consumes enriched evidence and deterministic scores as context. It
does not calculate blindness, fire-likelihood, or priority and cannot replace
the reviewer decision.

The high-uncertainty rule requires supported fire-likelihood evidence; missing
features by themselves do not enqueue an event. A feature fingerprint prevents
repeat score updates from queueing duplicate runs.

The current deterministic checks live in `tests/unit/test_agent.py` and cover
event scoping, source attribution, and rejection of unsupported evidence IDs.

## Evaluation dataset

Create fixed fixtures for:

The replay seed creates GK2A candidate clusters and attached satellite records
but does not create normalized `score_features`. Those seeded rows remain
unqualified unless an upstream deterministic feature producer adds them.
Multi-sensor confirmation, exposure data, and historical context are not
attached to these events and are returned as unavailable.
Expand fixed evaluation fixtures when those sources become available; do not
describe unsupported cases as tested.

## Expected behavior

The agent should:

- retrieve relevant evidence
- avoid irrelevant tools
- identify contradictions
- state missing information
- distinguish observation from estimate
- produce structured output
- avoid unsupported certainty

## Failure examples

Reject output if it:

- invents a sensor observation
- invents weather
- invents population
- claims a fire is confirmed without evidence
- claims a sensor missed a fire solely because another sensor disagreed
- ignores contradictory evidence
- returns invalid schema

## Suggested evaluation table

| Dimension | Pass condition |
|---|---|
| Grounding | Claims trace to tool output |
| Tool selection | Relevant tools used |
| Contradictions | Important conflicts identified |
| Uncertainty | Missing evidence acknowledged |
| Schema | Valid structured response |
| Safety | No autonomous emergency decision |
| Consistency | Similar evidence gives similar recommendations |

## Regression

Run all fixtures after:

- prompt changes
- tool changes
- model changes
- output-schema changes
- scoring changes
