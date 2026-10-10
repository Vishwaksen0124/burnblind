# Production data quality audit: 250 replay events

Audit date: 2026-10-10  
Environment: production, AWS `us-east-2`  
Scope: 250 candidate events and their 762 evidence records. The audit did not
invoke the investigation agent or a model.

## Findings and corrections

| Area | Audit result | Action |
| --- | --- | --- |
| Event projections | All 250 claimed `environmental_analysis=COMPLETE`; 248 had stale unavailable sensor comparison projections despite four stored comparisons. | Refreshed all 250 projections from their existing evidence records. |
| Blind-spot scores | Two events showed score `0` even though there was no valid sensor coverage input. Both alleged coverage rows were actually positive detections. | Set blind-spot and monitoring-coverage status to `UNAVAILABLE` for all 250. Marked those two coverage artifacts invalid while preserving their records and corresponding `SENSOR_OBSERVATION` evidence. No score is shown as zero. |
| Sensor comparisons | Four stored comparisons were source-matched. Two comparison reports repeated identical match pairs (6 rows/3 unique and 2 rows/1 unique). | Deduplicated by source evidence ID pair. Four distinct comparisons remain, with 3, 1, 1, and 1 unique matches. All report `AGREEMENT`; agreement is not confirmation. |
| Population exposure | All 250 estimates were sourced from WorldPop Global2 and had valid positive values, event-time context, and screening corridor geometry. All 250 also contained the contradictory limitation that exposure was unavailable. | Removed only that obsolete limitation from the 250 source-derived records and refreshed event projections. Retained limitations describing modeled population, screening geometry, and lack of smoke/health-impact prediction. |
| Weather | All 250 estimates were sourced from Open-Meteo ERA5. The audit found the saved sample consistently represents the archive's hourly value preceding event time; values and provenance were present and in valid ranges. | Preserved existing records and their estimate attribution; no new weather calls were made. |
| Deterministic score inputs | Fire-likelihood and uncertainty inputs were present in the replay records; blindness, independent observation-gap/coverage quality inputs, and final priority inputs were missing for most/all events. | Did not invent scores or recalculate unrelated score fields. Blindness is explicitly unavailable until valid normalized coverage inputs exist. |

## Production corrections

- Commit `da7808a` fixed the code path that synthesized a zero blindness score
  from any quality-valid coverage row.
- Commit `645e64a` deployed projection hydration, comparison deduplication,
  and corridor limitation corrections through Backend CI/CD. Backend and
  Dashboard CI/CD workflows succeeded for that commit.
- A one-time idempotent DynamoDB repair refreshed the 250 event summaries,
  corrected all 250 exposure limitations, deduplicated the four comparison
  records, and invalidated the two positive-detection-as-coverage artifacts.
- No investigation queue messages, Strands agent calls, Bedrock model calls,
  external weather lookups, or WorldPop requests were made during the repair.

## Post-repair verification

- Events: 250; blindness status `UNAVAILABLE`: 250; zero-valued blindness
  scores: 0.
- Exposure evidence: 250; obsolete unavailable limitation: 0.
- Valid sensor comparisons: 4; unique match-pair counts: 3, 1, 1, 1.
- Invalid coverage artifacts: 2; both remain available as audit records, are
  marked `INVALID_OBSERVATION_MISLABELED_AS_COVERAGE`, and retain
  `detection_present=true`.
- Live map API: blind spots `UNAVAILABLE` with 0 items; sensor comparison
  `AVAILABLE` with 4 items; exposure `AVAILABLE` with 250 items.
- Two live event environmental-analysis responses returned HTTP 200 and
  correctly showed blind spot unavailable, source-matched comparison, and
  WorldPop estimated exposure with no obsolete limitation.
- Automated validation before deployment: 115 unit tests passed; SAM lint
  validation and build succeeded. Backend CI/CD deployment and API smoke checks
  succeeded.

## Interpretation and remaining limits

The 250 corridor estimates are modeled counts of population inside a
directional screening corridor. They are not observed affected people, smoke
concentration, or health impact. Weather is a reanalysis estimate, not a local
station reading. Cross-sensor agreement indicates matched supplied
observations; it does not prove a fire. Blindness scores remain unavailable
because source-backed sensor coverage and normalized observability inputs are
not present. The replay still needs genuine coverage-quality inputs before the
product can calculate and display blind-spot scores.
