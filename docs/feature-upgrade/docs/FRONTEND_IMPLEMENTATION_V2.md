# Frontend Implementation V2

## Pages

1. Landing
2. Monitoring
3. Event detail
4. Investigations
5. Replay
6. How It Works
7. Data & Methodology
8. Docs
9. Optional Community View

## Monitoring layout

```text
KPI strip
↓
Map + layer controls
↓
Action Center / event queue
```

Map layers:
- events
- blind spots
- sensor disagreement
- exposure

## Event page

```text
Overview
↓
Evidence
↓
Sensor comparison
↓
Historical context
↓
Potential impact
↓
Timeline
↓
Investigation
```

## Investigation

Not a chatbot.

Show:
- status
- summary
- evidence reviewed
- contradictions
- uncertainty
- missing evidence
- recommendation

## Replay

Timeline scrubber + map state.

## UX rule

Show decision-relevant information, not raw database fields.

## States

Every data component needs:
- loading
- empty
- error
- partial-data

Historical/demo data must be clearly labelled.

## Visual direction

Dark charcoal base, warm off-white text, orange thermal accent, amber medium priority, restrained red high priority, thin borders, map-first layout, technical typography. Avoid generic AI gradients, robot imagery, excessive glassmorphism and giant rounded cards.
