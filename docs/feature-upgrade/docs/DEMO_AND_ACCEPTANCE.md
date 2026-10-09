# Demo + Acceptance

## 3-minute demo

0:00–0:20 Landing/problem.

0:20–0:50 Monitoring + Blind Spot Map.

0:50–1:15 Select high-priority event.

1:15–1:45 Show exposure corridor.

1:45–2:20 Run Investigation Agent and show evidence/uncertainty/recommendation.

2:20–2:40 Replay timeline.

2:40–3:00 AWS architecture and impact.

## Definition of done

- [x] Blind Spot Map surfaces only persisted layer records and an explicit unavailable state
- [x] Sensor comparison returns source-backed records when present; current replay has no FIRMS match set
- [x] Exposure calculation is event-scoped and source/assumption labeled; availability depends on weather and population response
- [x] Action Center deterministically buckets scored records; unscored replay events remain in “More evidence needed”
- [x] Investigation uses Strands with DeepSeek V3.2 through Bedrock Mantle; one deployed event flow succeeded
- [x] Evidence packet is assembled by the application and bound to one requested event
- [x] Agent report has application-side schema and evidence-ID validation
- [x] Missing evidence remains explicitly unavailable and is not treated as negative evidence
- [x] CloudWatch logs capture API and worker execution; the verified worker invocation completed without errors
- [x] Replay uses persisted historical timestamps and is labeled as replay
- [x] Human outcome append-only persistence is implemented; protected write deployment is pending
- [x] Frontend loading, error, empty, and partial-availability states exist
- [x] Responsive layouts are implemented; browser visual acceptance is still pending
- [x] Unit tests and production builds pass locally (see `docs/CHECKLIST.md` for dated counts)
- [x] Public repository
- [ ] <=3 minute video
- [ ] AWS usage is visible in the video

### Remaining release gates

- Reviewer JWT routes deployed and anonymous-write rejection verified.
- Reviewer-account outcome submission verified end to end.
- Browser visual/keyboard review at desktop and mobile widths.
- Independent FIRMS reference data, attached coverage records, and score-ready
  replay rows; without these, sensor-gap and automatic-qualification demos
  remain unavailable by design.
- Live external-source validation, broader agent evaluations, integration and
  failure-path tests, security/cost review, and public demo recording.
