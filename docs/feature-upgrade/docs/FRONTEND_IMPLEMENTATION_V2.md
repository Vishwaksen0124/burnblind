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

## Implemented route and interaction map

| View | User action | Data/work performed | Honest unavailable state |
| --- | --- | --- | --- |
| Product landing | Open monitoring, methodology, or workflow | Loads replay summary and persisted candidate events; uses the attributed NASA Earth Observatory image in `frontend/public/images/` | Replay load error is stated; the preview is labeled historical rather than a current incident feed |
| Monitoring | Search/filter candidates, select a map marker, switch a layer | Reads Action Center, summary, event details, investigation state, review outcomes, comparison, and exposure separately | Blind-spot/comparison/exposure layers state which attached records are missing; no synthetic heatmap or score is substituted |
| Event detail | Inspect evidence, request investigation, record outcome | Requests exactly the selected `event_id`; report and append-only outcome reload from API | Missing evidence stays unavailable; reviewer writes require invited Cognito sign-in |
| Investigations | Browse and paginate reports | Reads persisted investigation records with status, summary, cited evidence count, application-owned timestamps and model metadata | Empty, loading, retryable error, queued, failed, and completed states are distinct |
| Replay | Play, pause, step, scrub, change speed, select an event | Pages persisted events, sorts by observation time, then reveals records up to the selected timestamp | Empty and API-error states do not imply there were no fires |
| How it works | Follow inputs, outputs, and current readiness | Describes the seven application stages and per-stage input/output | Stages whose source data are missing are marked incomplete, not presented as operational |
| Data & methodology | Inspect source limits, agent contract, and terms | Documents source provenance, evidence packet inputs, JSON report ownership, and operational flow | Source limitations and model advisory boundary stay visible |

## Visual composition and responsive behavior

The landing content uses a wider 1,760 px editorial measure on large screens
to reduce unused side gutters while keeping text readable. It pairs an
attributed satellite image with a dark earth-and-heat palette, thin map-like
rules, source/date annotations, and a restrained orange accent. The monitoring
view prioritizes the map and queue, then uses loaded observations for UTC-day
and source summaries; these are descriptive counts, not risk metrics. No
decorative values are fabricated to fill space. Small screens collapse the
story, source, map, and review layouts into a single column.

The navigation and event-detail tabs support keyboard focus. Reduced-motion
preferences disable nonessential animation. Every network-backed region has a
loading, error, empty, or partial-availability message.

## States

Every data component needs:
- loading
- empty
- error
- partial-data

Historical/demo data must be clearly labelled.

## Visual direction

Dark charcoal base, warm off-white text, orange thermal accent, amber medium priority, restrained red high priority, thin borders, map-first layout, technical typography. Avoid generic AI gradients, robot imagery, excessive glassmorphism and giant rounded cards.
