# BurnBlind — File Structure

```text
burnblind/
│
├── README.md
│
├── docs/
│   ├── REQUIREMENTS.md
│   ├── PRODUCT.md
│   ├── PROBLEM.md
│   ├── DATA_SOURCES.md
│   ├── DATA_CONTRACTS.md
│   ├── SCORING.md
│   ├── TOOL_CONTRACTS.md
│   ├── SYSTEM_DESIGN.md
│   ├── ARCHITECTURE.md
│   ├── AWS_ARCHITECTURE.md
│   ├── DATA_ARCHITECTURE.md
│   ├── INVESTIGATION_AGENT.md
│   ├── FRONTEND_DESIGN.md
│   ├── API_SPEC.md
│   ├── CONFIGURATION.md
│   ├── ACCEPTANCE_CRITERIA.md
│   ├── OBSERVABILITY_RUNBOOK.md
│   ├── DECISIONS.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── TESTING.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY.md
│   ├── DEMO.md
│   ├── LIMITATIONS.md
│   └── CHECKLIST.md
│
├── backend/
│   ├── api/
│   ├── ingestion/
│   ├── processing/
│   ├── scoring/
│   ├── impact/
│   ├── agent/
│   └── common/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
│
├── infrastructure/
│   └── sam/
│
├── data/
│   ├── sample/
│   └── schemas/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── agent/
│   └── fixtures/
│
├── scripts/
│
└── .github/
    └── workflows/
```

## Implementation ownership

### backend/

All environmental intelligence and API behavior.

### frontend/

Visualization and user interaction.

### infrastructure/

Infrastructure-as-code and SAM templates.

### data/

Schemas and small development fixtures only. Do not commit large datasets.

### tests/

Automated tests and evaluation cases.

### docs/

Source of truth for architecture and implementation.
