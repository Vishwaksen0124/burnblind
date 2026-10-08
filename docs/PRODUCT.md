# BurnBlind — Product Specification

## 1. Product statement

> BurnBlind helps environmental operators identify where satellite fire monitoring may be incomplete, investigate potential events using multiple evidence sources, and prioritize the events that deserve human attention.

## 2. Problem

Environmental monitoring systems use sensors with different spatial resolution, revisit intervals, viewing geometry, cloud sensitivity, and thermal characteristics.

This creates situations where:

- one sensor observes an anomaly while another does not,
- a location has not recently been observed by a high-resolution sensor,
- a potential fire occurs during a temporal observation gap,
- historical patterns indicate elevated risk,
- the potential event may affect a large population.

The problem is therefore not simply "detect fires."

The problem is:

> **Which potential events are poorly observed, how credible are they, how much could they matter, and which ones should humans investigate first?**

## 3. Product outcome

For every candidate event, BurnBlind should provide:

- location
- timestamp
- monitoring blindness
- fire likelihood
- evidence quality
- potential exposure
- priority
- investigation status
- investigation recommendation

## 4. User workflow

```text
Open dashboard
    ↓
See current events
    ↓
Filter by priority
    ↓
Open event
    ↓
Review evidence
    ↓
Request / view investigation
    ↓
Read agent recommendation
    ↓
Human decides next action
```

## 5. MVP product features

### Dashboard

- event map
- priority markers
- filters
- event list
- summary statistics
- event detail

### Investigation

- evidence timeline
- satellite observations
- historical context
- weather
- exposure
- sensor disagreement
- agent recommendation
- confidence
- contradictions

### Documentation

- problem
- methodology
- architecture
- AWS stack
- agent design
- limitations

## 6. Non-goals

- emergency dispatch
- autonomous emergency decisions
- nationwide operational service
- precise atmospheric dispersion simulation
- proving ground truth from satellite disagreement alone
