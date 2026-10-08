# Data Contracts V2

## Event

```typescript
type Event = {
  id: string
  location: { lat: number; lon: number; district?: string; state: string }
  timestamp: string
  sourceMode: "LIVE" | "HISTORICAL" | "DEMO"
  fireLikelihood?: number
  monitoringBlindness?: number
  exposureEstimate?: number
  priorityScore?: number
  priorityBand: "LOW" | "MEDIUM" | "HIGH"
  status: string
}
```

## Evidence

```typescript
type EvidenceItem = {
  id: string
  type: "OBSERVED" | "DERIVED" | "HISTORICAL" | "ESTIMATED"
  source: string
  observedAt?: string
  finding: string
  quality?: "HIGH" | "MEDIUM" | "LOW"
  provenanceId: string
}
```

## Investigation

```typescript
type Investigation = {
  eventId: string
  status: string
  summary: string
  evidence: EvidenceItem[]
  contradictions: string[]
  uncertainties: string[]
  missingEvidence: string[]
  recommendation:
    | "HUMAN_VERIFICATION"
    | "LOW_PRIORITY"
    | "INSUFFICIENT_EVIDENCE"
}
```

Keep UI contracts separate from raw S3/DynamoDB schemas.
