# BurnBlind — Coding Agent Instructions

This file is intended to guide an implementation coding agent.

## Mission

Implement BurnBlind according to the documentation in `/docs`.

Do not invent architecture that contradicts the docs.

## Required behavior

1. Read `README.md`.
2. Read `docs/REQUIREMENTS.md`.
3. Read `docs/PRODUCT.md`.
4. Read `docs/PROBLEM.md`.
5. Read `docs/DATA_SOURCES.md`.
6. Read `docs/SYSTEM_DESIGN.md`.
7. Read `docs/ARCHITECTURE.md`.
8. Read `docs/AWS_ARCHITECTURE.md`.
9. Read `docs/INVESTIGATION_AGENT.md`.
10. Read `docs/ACCEPTANCE_CRITERIA.md`.
11. Read `docs/DATA_CONTRACTS.md`.
12. Read `docs/SCORING.md`.
13. Read `docs/TOOL_CONTRACTS.md`.
14. Read `docs/IMPLEMENTATION_PLAN.md`.
15. Follow implementation phases in order.

## Non-negotiable rules

### Rule 1 — Do not skip data contracts

Define and test schemas before implementing scoring.

### Rule 2 — Do not fake scientific evidence

Never create fake satellite observations and present them as real.

Fixtures must be clearly marked as sample/demo data.

### Rule 3 — Do not call the agent unnecessarily

Use the documented trigger policy.

### Rule 4 — Agent must use tools

Do not build a generic chatbot.

The Investigation Agent must call deterministic evidence tools.

### Rule 5 — No hallucinated evidence

If a tool does not provide information, the agent must say it is unavailable.

### Rule 6 — Keep scoring deterministic

Given identical input and configuration, deterministic scoring should return identical results.

### Rule 7 — Frontend is not the intelligence engine

Environmental calculations belong in backend services.

### Rule 8 — Avoid unnecessary AWS services

Prefer the documented serverless architecture.

### Rule 9 — Test every phase

Do not proceed to the next phase if the current phase's tests fail.

### Rule 10 — Keep documentation updated

If implementation differs from the design, update the relevant document.

## Agent implementation order

```text
schemas
 ↓
sample data
 ↓
preprocessing
 ↓
features
 ↓
scores
 ↓
events
 ↓
impact
 ↓
AWS pipeline
 ↓
agent tools
 ↓
agent
 ↓
API
 ↓
frontend
 ↓
integration
```

## Definition of done

A feature is done only when:

- implementation exists
- tests exist
- errors are handled
- documentation is updated
- no secrets are committed
- behavior is reproducible

## Source-of-truth hierarchy

When documents conflict:

1. `docs/REQUIREMENTS.md` for hackathon constraints
2. `docs/DATA_SOURCES.md` for source/provenance
3. `docs/SYSTEM_DESIGN.md` for behavior
4. `docs/AWS_ARCHITECTURE.md` for AWS deployment
5. `docs/IMPLEMENTATION_PLAN.md` for execution order
6. code comments and implementation details

If a requirement is unclear, do not silently invent a critical behavior.

## Completion gates

Do not mark a phase complete until its acceptance criteria and tests pass.

Do not optimize or polish the frontend while P0 backend acceptance criteria remain incomplete.
