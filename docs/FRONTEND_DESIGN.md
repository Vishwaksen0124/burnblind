# BurnBlind — Frontend Design System

## 1. Design goal

The frontend should look like a serious environmental monitoring product, not a generic AI-generated dashboard.

Visual inspiration:

> thermal maps + wildfire operations center + satellite monitoring console

## 2. Theme

### Heat / thermal intelligence

Use:

- near-black / charcoal foundation
- warm orange
- amber
- red for critical states
- yellow for warning
- muted neutral text
- restrained white

Avoid making the entire interface red/orange. Heat colors should communicate meaning.

## 3. Avoid generic AI UI

Do NOT use:

- purple/blue "AI" gradients
- excessive glassmorphism
- robot illustrations
- giant chatbot UI
- meaningless glowing cards
- excessive rounded cards
- decorative AI text
- fake terminal animations

## 4. Typography

Use one strong display/system font and one readable body font if needed.

Prefer:

- compact headings
- technical labels
- clear numeric hierarchy
- high information density
- generous whitespace where it improves readability

## 5. Pages

### Product

Hero:

```text
BURNBLIND

See where environmental monitoring
may be going blind.

Detect. Investigate. Prioritize.
```

Then:

- problem
- solution
- pipeline
- impact

### How it works

Show:

```text
OBSERVE
  ↓
BLIND SPOT
  ↓
VERIFY
  ↓
IMPACT
  ↓
PRIORITIZE
  ↓
INVESTIGATE
```

### Monitoring dashboard

Map-first.

Layout:

```text
┌────────────────────────────────────────────┐
│ BURNBLIND       LIVE MONITORING     ● LIVE │
├───────────────┬────────────────────────────┤
│ FILTERS       │                            │
│               │            MAP             │
│ Priority      │                            │
│ Time          │       🔴                   │
│ Region        │                  🟠        │
│               │                            │
├───────────────┴────────────────────────────┤
│ EVENTS                                      │
│ #102  HIGH    Blindness 79%    Priority 91 │
│ #103  MEDIUM  Blindness 52%    Priority 64 │
└────────────────────────────────────────────┘
```

### Event investigation

Make the evidence the hero.

Show:

- event metadata
- score breakdown
- evidence timeline
- sensor comparison
- historical pattern
- weather
- exposure
- agent conclusion

## 6. Heat-map language

Use color semantically:

```text
low       → neutral
moderate  → yellow/amber
high      → orange
critical  → red
```

Do not use color as the only signal. Add labels/icons.

## 7. Motion

Use restrained motion:

- event pulse
- map transitions
- investigation status
- loading states

Do not animate every card.

## 8. Frontend architecture

Suggested:

```text
frontend/
├── app/
├── components/
│   ├── map/
│   ├── events/
│   ├── investigation/
│   ├── charts/
│   └── layout/
├── lib/
│   ├── api/
│   └── formatting/
└── styles/
```

The frontend consumes APIs. It does not calculate environmental scores.

## 9. Information hierarchy

The dashboard must answer, in order:

1. Where is the event?
2. How urgent is it?
3. Why is it important?
4. What evidence supports it?
5. What is uncertain?
6. What did the Investigation Agent recommend?

Do not force users to open five cards to understand the event.

## 10. Source transparency

Display source/time metadata for major evidence:

```text
GK2A · 17:20 IST
FIRMS · 14:03 IST
Weather · 17:00 IST
WorldPop · 2021 estimate
```

This makes the product visibly trustworthy.

## 11. Accessibility

- keyboard navigation
- readable contrast
- labels in addition to color
- map markers with accessible summaries
- visible focus states
- reduced-motion support

## 12. Demo mode

If using a deterministic fixture:

```text
DEMO / REPLAY
```

must be visible.

Never make replay data look like a live feed.

## 13. Responsive priorities

Desktop is primary for the hackathon dashboard.

Mobile should still support:

- event list
- event detail
- investigation summary

The full map experience may be simplified on small screens.

## 14. Map implementation

Use an established web map library such as MapLibre GL JS or Leaflet.

The implementation must document the actual tile/basemap provider and follow that provider's usage/license rules.

Event geometry owned by BurnBlind should be supplied as GeoJSON from the backend/API.

Do not make the map dependent on a paid provider for the core demo unless access is already secured.
