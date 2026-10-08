# BurnBlind Frontend Implementation Specification

## Purpose

Build the BurnBlind frontend as a **serious environmental intelligence and satellite-monitoring application**, not as a generic AI dashboard and not as a raw database viewer.

The frontend must present only information that helps a human understand:

1. What environmental events are being observed?
2. Where are they?
3. Which events are potentially important?
4. Why are they important?
5. What evidence supports the event?
6. Which events require investigation?
7. What did the Investigation Agent conclude?

The frontend must be clean, deliberate, readable, and visually consistent.

---

# 1. Current Frontend Problems

The current implementation looks like an unfinished internal data viewer.

Problems visible in the current screen:

- Too much empty space around the actual product content.
- The page looks like a table/database rather than an environmental monitoring product.
- "Candidate clusters", "Scored events", etc. are shown even when the underlying data is unavailable.
- The dashboard displays `0`, `—`, or "pending" states prominently instead of presenting useful information.
- The map is not visually focused on the intended Punjab/Haryana monitoring region.
- The event queue is too dense and difficult to scan.
- Event IDs are exposed as the primary visual information.
- There is not enough distinction between:
  - candidate detection
  - scored event
  - high-priority event
  - investigation
- The UI does not clearly communicate why an event matters.
- The current screen looks like a developer/debug interface.
- There is too much implementation terminology visible to the user.
- The page hierarchy is weak.
- The visual design does not yet feel like a polished satellite/environmental operations center.
- Empty/unavailable backend features should not dominate the UI.
- Data should never be displayed merely because it exists in the database.

The new frontend must solve these problems.

---

# 2. Core Frontend Principle

## Show the decision-relevant information, not the database.

Do NOT automatically render every field returned by the backend.

For example, do not show:

```text
event_id
grid_id
processing_version
raw_source_id
internal_state
worker_id
queue_message_id
```

unless the user is inside a technical/debugging/documentation view.

Instead show:

```text
Potential fire
High monitoring blind spot
Fire likelihood: High
Population exposure: 12,400
Sensor disagreement detected
Observed: 16:04 UTC
Investigation required
```

The UI should answer:

> "What should I pay attention to?"

not:

> "What fields exist in DynamoDB?"

---

# 3. Product Visual Direction

The design should feel like:

- environmental intelligence
- satellite monitoring
- wildfire operations center
- geospatial analytics
- technical but polished
- serious and trustworthy

It should NOT feel like:

- generic SaaS admin dashboard
- ChatGPT clone
- AI startup landing page
- crypto dashboard
- generic analytics template
- developer console
- database explorer

## Visual language

Use:

- very dark charcoal / near-black background
- warm off-white text
- muted grey secondary text
- orange / amber for thermal signals
- red only for genuinely high-risk conditions
- restrained green for healthy/normal status
- thin borders
- subtle panel separation
- compact technical typography
- map as a major visual element
- subtle grid/coordinate styling where useful

Avoid:

- purple AI gradients
- blue/purple neon
- excessive glassmorphism
- giant rounded cards
- excessive shadows
- huge glowing effects
- robot illustrations
- decorative AI imagery
- unnecessary animations

---

# 4. Global Layout

Desktop is the primary target.

Use a consistent application shell:

```text
┌──────────────────────────────────────────────────────────────┐
│ BurnBlind       Monitoring    Investigations    Docs    ...  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                     PAGE CONTENT                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Do not create excessive vertical whitespace.

Maximum content width should be approximately:

```text
1400px – 1600px
```

depending on viewport.

The content should feel dense enough for an operations application while remaining readable.

---

# 5. Navigation

Navigation should be minimal.

Primary:

```text
BURNBLIND

Monitoring
Investigations
How it works
Data & methodology
```

Optional:

```text
Replay: 2025
```

The current data mode must always be obvious:

```text
HISTORICAL REPLAY · 2025
```

or

```text
LIVE MONITORING
```

Never imply live monitoring when replay data is being used.

---

# 6. Screen 1 — Monitoring Dashboard

This is the primary application screen.

## Header

Show:

```text
ENVIRONMENTAL MONITORING

Monitoring overview

Detect potential environmental events across Punjab and Haryana,
identify monitoring blind spots, and prioritize events for investigation.
```

On the right:

```text
DATA WINDOW
30 Nov 2025 · 16:00
```

If this is replay data:

```text
HISTORICAL REPLAY · 2025
```

Do not call it "live".

---

# 7. Dashboard KPI Section

Use 3–4 compact KPI blocks.

Only show metrics that have valid values.

Recommended:

```text
CANDIDATE EVENTS
124

Potential detections in current window
```

```text
HIGH PRIORITY
8

Require investigation
```

```text
MONITORING BLINDNESS
17%

Events with elevated observability gaps
```

```text
POPULATION EXPOSURE
42.8K

Estimated people potentially affected
```

If a metric cannot currently be calculated, DO NOT make it a prominent KPI.

Instead either:

- omit it
- or show a subtle "Not available" state

Never show:

```text
0
—
Pending
Trigger policy not available
```

as the primary dashboard experience.

---

# 8. Main Dashboard Layout

Use a two-column layout.

```text
┌──────────────────────────────────────┬─────────────────────────┐
│                                      │                         │
│              MAP                     │      EVENT QUEUE        │
│                                      │                         │
│                                      │                         │
│                                      │                         │
│                                      │                         │
└──────────────────────────────────────┴─────────────────────────┘
```

Recommended ratio:

```text
Map: 68–72%
Event panel: 28–32%
```

The map must dominate the screen.

---

# 9. Map

The map is the most important dashboard element.

## Geographic scope

The primary monitoring area is:

```text
Punjab + Haryana
```

The initial map viewport should automatically fit the Punjab/Haryana region.

Do not start the map somewhere unrelated to the target geography.

## Map elements

Show:

- Punjab/Haryana boundary
- major geographic context
- event markers
- optional thermal density/heat layer
- optional monitoring coverage layer
- map legend
- timestamp/source

Do not overload the map with every possible GIS layer.

## Marker hierarchy

Use different visual treatments:

### Candidate

Small orange marker.

### Moderate priority

Amber marker with slightly stronger visual weight.

### High priority

Red/orange marker with a restrained pulse or ring.

### Investigating

Distinct outline/status indicator.

### Confirmed

Only use a "confirmed" style when the system actually has confirmation.

Never imply confirmation merely because a satellite detection exists.

---

# 10. Map Interaction

Clicking an event marker must open a concise event summary.

Example:

```text
EVENT  #BL-1042

Potential fire event

Punjab · Patiala
16:04 UTC

Fire likelihood       HIGH
Monitoring blind spot HIGH
Exposure              12.4K

Sensor disagreement detected

[View investigation]
```

The map should not open a giant modal containing every database field.

---

# 11. Event Queue

The right-side event queue should NOT be a raw list of event IDs.

Current bad pattern:

```text
evt_22d2f3ae...
grid-v1-utm43n...
GK2A_AMI
1 DETECTIONS
```

Replace it with:

```text
HIGH PRIORITY

Patiala
Potential fire
16:04 UTC

Fire likelihood: High
Blindness: High
Exposure: 12.4K
```

Each event row should have:

- location
- event type
- timestamp
- priority
- one or two important evidence indicators

Event ID can appear subtly inside the detail view.

---

# 12. Event Filters

Keep filters simple.

Recommended:

```text
All
High priority
Potential fire
High blindness
Investigating
```

Optional:

```text
Date
District
```

Do not create 15 filters.

The purpose is fast triage.

---

# 13. Event Detail

Clicking an event should open a dedicated detail page or large detail drawer.

Structure:

```text
EVENT OVERVIEW
↓
LOCATION + TIME
↓
KEY SCORES
↓
MAP
↓
EVIDENCE
↓
IMPACT
↓
INVESTIGATION
```

---

# 14. Event Overview

Example:

```text
Potential fire event

Patiala, Punjab
30 Nov 2025 · 16:04 UTC

HIGH PRIORITY
```

Then show four key metrics:

```text
Fire likelihood
HIGH

Monitoring blindness
HIGH

Potential exposure
12.4K

Urgency
HIGH
```

Scores should be visual but restrained.

Do not turn every metric into a giant gauge.

---

# 15. Evidence Section

This is extremely important.

The user must understand WHY the event received its priority.

Example:

```text
WHY THIS EVENT MATTERS

✓ Thermal anomaly detected
✓ Historical fire activity is elevated in this grid
✓ Independent sensor evidence differs
⚠ Monitoring coverage is limited during this observation window
✓ Downwind population exposure is significant
```

Each evidence item should indicate its type:

```text
OBSERVED
DERIVED
HISTORICAL
ESTIMATED
```

This distinction is important for scientific honesty.

---

# 16. Sensor Comparison

If multiple sensors are available, show a compact comparison.

Example:

```text
SENSOR COMPARISON

GK2A
Potential thermal signal
16:00 UTC

VIIRS
No matching detection
15:54 UTC

STATUS
CROSS-SENSOR DISAGREEMENT
```

Do not state:

```text
VIIRS missed the fire
```

unless there is actual evidence proving that.

Use:

```text
Cross-sensor disagreement
```

or:

```text
Independent observation unavailable
```

---

# 17. Historical Context

Show only useful historical information.

Example:

```text
HISTORICAL CONTEXT

This grid has elevated fire activity during
the Oct–Nov post-monsoon period.

Past detections
18

Typical seasonal level
Moderate

Historical risk
HIGH
```

Do not show raw historical tables unless the user asks for detailed methodology.

---

# 18. Impact / Exposure

Keep this focused.

Example:

```text
POTENTIAL IMPACT

Estimated downwind population
12,400

Wind
NW · 18 km/h

Exposure direction
SE

Exposure confidence
Moderate
```

Clearly label estimates as estimates.

---

# 19. Investigation Agent Screen

This should be a major feature of the product.

The Investigation Agent is NOT a chatbot.

Do not build:

```text
Chat with BurnBlind
```

Instead create an investigation report.

Example:

```text
INVESTIGATION

Event BL-1042
Patiala, Punjab

STATUS
REVIEW REQUIRED
```

Then:

```text
INVESTIGATION SUMMARY

Multiple evidence sources indicate a potential
thermal event. Monitoring coverage is limited,
and independent sensor evidence is inconsistent.

Human verification is recommended.
```

---

# 20. Investigation Evidence

Show the tools/evidence used:

```text
EVIDENCE REVIEWED

Satellite observations        ✓
Historical fire context       ✓
Weather conditions            ✓
Sensor comparison             ✓
Population exposure           ✓
```

Clicking one can expand its supporting information.

The UI should show evidence and conclusions.

Do NOT expose chain-of-thought.

Do not display:

```text
The model thought...
Step 1...
Step 2...
```

Instead show:

```text
Evidence
Conclusion
Uncertainty
Recommendation
```

---

# 21. Investigation Recommendation

Use explicit recommendation states:

```text
HUMAN VERIFICATION RECOMMENDED
```

or:

```text
LOW PRIORITY — NO FURTHER ACTION
```

or:

```text
INSUFFICIENT EVIDENCE
```

Never allow the UI to imply autonomous emergency response.

---

# 22. Investigation Status

Use:

```text
NOT INVESTIGATED
QUEUED
INVESTIGATING
REVIEW REQUIRED
CONFIRMED
DISMISSED
```

Do not show an "AI confidence" number unless the backend actually defines and calibrates it.

If confidence exists, label it accurately.

---

# 23. How It Works Page

This page should explain the complete system visually.

Use six steps:

```text
01  OBSERVE
Satellite and environmental observations

↓

02  FIND BLIND SPOTS
Identify monitoring gaps and uncertainty

↓

03  DETECT
Find potential environmental events

↓

04  ASSESS IMPACT
Estimate downwind exposure

↓

05  PRIORITIZE
Rank events by evidence, blindness and impact

↓

06  INVESTIGATE
Use the Investigation Agent to cross-check evidence
```

This page should make the product understandable to a judge in under one minute.

---

# 24. Data & Methodology Page

Show:

## Data sources

```text
GK2A
NASA FIRMS / VIIRS
Historical fire dataset
Weather / reanalysis
WorldPop
```

For each:

- what it provides
- time coverage
- geographic coverage
- limitations

## Important terminology

Explain:

```text
Monitoring blind spot
Cross-sensor disagreement
Potential fire event
Estimated exposure
Investigation priority
```

This page is also where limitations and scientific caveats should live.

---

# 25. Analytics Page

Only create an analytics page if the backend has meaningful aggregated data.

Useful charts:

- events by date
- events by district
- high-priority events over time
- blindness distribution
- sensor agreement/disagreement
- investigation outcomes

Do not create charts just to fill the page.

No fake analytics.

---

# 26. Data Availability Rules

This is critical.

The frontend must never invent values.

If data is unavailable:

BAD:

```text
High Priority: 0
Investigations: 0
Exposure: 0
```

GOOD:

```text
Investigation data unavailable
```

or hide the metric entirely.

If using historical replay:

```text
HISTORICAL REPLAY
Source: GK2A historical dataset
Period: Oct–Nov 2025
```

If using mock data during development:

```text
DEMO DATA
```

Never label mock data as live satellite observations.

---

# 27. API Separation

The frontend should consume clean API objects.

Do not couple UI components directly to DynamoDB/S3 structures.

Recommended frontend-facing objects:

```typescript
EventSummary {
  id: string
  location: {
    lat: number
    lon: number
    district?: string
    state: string
  }
  timestamp: string
  priority: "LOW" | "MEDIUM" | "HIGH"
  fireLikelihood?: number
  monitoringBlindness?: number
  exposureEstimate?: number
  status: string
}
```

Investigation:

```typescript
Investigation {
  eventId: string
  status: string
  summary: string
  evidence: EvidenceItem[]
  contradictions: string[]
  missingEvidence: string[]
  recommendation: string
}
```

The frontend should not need to understand internal processing pipelines.

---

# 28. Loading / Error / Empty States

Every data-driven component must have a deliberate state.

## Loading

Use subtle skeletons.

## Empty

Example:

```text
NO HIGH-PRIORITY EVENTS

No events currently require investigation.
```

## Error

Example:

```text
EVENT DATA UNAVAILABLE

We could not load monitoring data.

Retry
```

## Partial data

Example:

```text
Exposure estimate unavailable
```

Do not break the entire page because one data source is unavailable.

---

# 29. Responsive Design

Desktop is primary.

Tablet:

- map remains large
- event queue moves below map if necessary

Mobile:

```text
Header
↓
KPIs
↓
Map
↓
Filters
↓
Events
```

Do not attempt to preserve the desktop two-column layout on a narrow screen.

---

# 30. Component Architecture

Use reusable components.

Suggested:

```text
components/
  layout/
    AppShell
    Header
    Navigation

  dashboard/
    KPIBar
    MonitoringMap
    MapLegend
    EventQueue
    EventCard
    EventFilters

  events/
    EventHeader
    EventScores
    EvidenceList
    SensorComparison
    HistoricalContext
    ExposurePanel

  investigation/
    InvestigationHeader
    InvestigationStatus
    InvestigationSummary
    EvidenceReview
    Recommendation

  shared/
    Badge
    StatusIndicator
    Metric
    EmptyState
    ErrorState
    LoadingState
```

Do not put the entire dashboard into one giant component.

---

# 31. Visual Hierarchy

Every screen should have a clear hierarchy:

```text
WHAT IS HAPPENING?
        ↓
WHERE?
        ↓
HOW IMPORTANT?
        ↓
WHY?
        ↓
WHAT SHOULD I DO?
```

The user should understand an event within seconds.

---

# 32. Typography

Use a strong sans-serif for primary text.

Use a compact monospace/technical font selectively for:

- timestamps
- coordinates
- data source labels
- event IDs
- system metadata

Do not use monospace for the entire interface.

---

# 33. Animation

Use animation only when it communicates state.

Good:

- event marker pulse for high-priority events
- investigation status transition
- subtle map loading

Bad:

- glowing cards
- constant background animation
- spinning AI graphics
- excessive hover animations

Respect reduced-motion preferences.

---

# 34. Accessibility

Required:

- keyboard navigation
- visible focus states
- sufficient contrast
- semantic buttons
- tooltips for unfamiliar icons
- do not rely only on color to indicate priority

For example:

```text
HIGH · red
MEDIUM · amber
LOW · neutral
```

not just colored dots.

---

# 35. What NOT to Build

Do not add:

- chatbot
- AI assistant floating button
- fake notifications
- fake live counters
- fake weather
- fake satellite imagery
- unnecessary user authentication
- profile pages
- settings pages unless required
- billing
- social features
- generic AI landing-page sections
- excessive charts
- unnecessary 3D map
- decorative dashboards
- database/debug screens

Every UI element must support the environmental monitoring workflow.

---

# 36. Primary User Journey

The complete experience should support this flow:

```text
Open BurnBlind
      ↓
See current/replay monitoring window
      ↓
See important events on map
      ↓
Select high-priority event
      ↓
Understand why it is important
      ↓
Review evidence
      ↓
Open investigation
      ↓
Read Investigation Agent findings
      ↓
See uncertainty + recommendation
      ↓
Human decides what to do
```

This is the core product journey.

---

# 37. Demo Journey

The frontend must be optimized for a 3-minute hackathon demo.

Recommended demo:

### 0:00–0:20
Show monitoring overview.

### 0:20–0:50
Select a high-priority event on the map.

### 0:50–1:20
Show:

- fire likelihood
- monitoring blindness
- sensor disagreement
- exposure

### 1:20–2:10
Open Investigation Agent.

Show:

- evidence reviewed
- contradictions
- uncertainty
- recommendation

### 2:10–2:40
Show how the system works / data sources.

### 2:40–3:00
Show AWS architecture and explain why BurnBlind is useful.

The UI must support this journey without unnecessary navigation.

---

# 38. Implementation Rules for Coding Agent

Before coding:

1. Read the BurnBlind repository documentation.
2. Understand the backend data contracts.
3. Understand which fields are actually available.
4. Do not invent missing backend capabilities.
5. Implement the frontend using reusable components.
6. Build the monitoring screen first.
7. Then event details.
8. Then investigation.
9. Then supporting pages.
10. Test every screen.

When backend APIs are unavailable, use typed mock data that follows the exact API schema.

Keep mock data isolated:

```text
src/
  mock/
    events.ts
    investigations.ts
```

Do not scatter hardcoded fake values throughout components.

---

# 39. Definition of Done

The frontend is complete only when:

- [ ] Monitoring dashboard looks polished
- [ ] Punjab/Haryana is the correct default map region
- [ ] Map is the visual centerpiece
- [ ] Event queue is readable
- [ ] Event IDs are not the primary UI
- [ ] Only useful data is displayed
- [ ] No fake scientific claims
- [ ] Replay/live state is explicit
- [ ] Event details are understandable
- [ ] Evidence is clearly separated from derived values
- [ ] Investigation page is not a chatbot
- [ ] Investigation findings are easy to understand
- [ ] Loading states exist
- [ ] Empty states exist
- [ ] Error states exist
- [ ] Responsive layout works
- [ ] Accessibility basics are implemented
- [ ] No unnecessary dashboard elements
- [ ] No generic AI visual language
- [ ] Frontend build succeeds
- [ ] Tests pass
- [ ] API integration points are cleanly separated

---

# 40. Final Instruction to the Coding Agent

Build BurnBlind as if it were a real environmental monitoring product that an analyst could use.

**Do not optimize for showing more data. Optimize for making the important data immediately understandable.**

The frontend should answer:

> **What is happening, where is it happening, how important is it, what evidence supports it, and does it require investigation?**

If a UI element does not help answer one of those questions, do not add it.

The attached reference screenshot should be treated as an example of the current implementation that needs improvement, NOT as the target design. The target is a much more polished, focused, map-first environmental intelligence interface following this specification.
