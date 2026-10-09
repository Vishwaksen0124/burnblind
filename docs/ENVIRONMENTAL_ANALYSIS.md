# Environmental analysis

Environmental enrichment is attempted for every newly ingested event,
including explicitly labelled historical replay events. It runs independently
from Strands: it does not calculate core scores, call DeepSeek, or create an
investigation report.

## Flow

```text
Event is inserted or replayed
  → DynamoDB stream marks environmental status PROCESSING
  → FIFO SQS environmental queue
  → environmental Lambda reads that event and attached evidence
  → Open-Meteo ERA5 event-time wind
  → geodesic downwind screening corridor
  → WorldPop Global2 population estimate
  → strict comparison of attached independent sensor evidence
  → feature summary and validated score inputs on the event
  → deterministic scoring and prioritization
  → reviewer sees evidence, scores, uncertainty, and reasons
  → reviewer may request the Investigation Agent
  → UI displays sources, estimates, scores, and limitations
```

The environmental worker has no model permissions and is not connected to the
investigation queue. It processes one event per SQS message, has bounded Lambda
concurrency, retries twice, and uses a dead-letter queue. Re-running analysis
reuses successful event-time weather, population, and comparison records rather
than querying static inputs repeatedly.

## Inputs and outputs

Inputs are the selected event identity, timestamp and coordinates, its attached
satellite observations and any attached `SENSOR_COVERAGE` evidence. Event
identity, timestamp and provider metadata remain application-owned.

Outputs are:

- `WEATHER_ESTIMATE`: event-hour wind with Open-Meteo ERA5 source/version and
  timestamp. It is reanalysis, not a local measurement.
- `POPULATION_EXPOSURE_ESTIMATE`: WorldPop population sum inside the supplied
  six-hour, ten-kilometre-wide directional screening corridor, including its
  geometry, source/year/resolution and limitations. This is potential exposure,
  not proof of a fire, smoke concentration, or people currently affected.
- `SENSOR_COMPARISON`: results from the shared spatial/temporal comparison
  rules. A missing second-sensor record remains unavailable; it is never
  converted into a disagreement.
- `blind_spot`: remains unavailable until source-backed acquisition coverage
  and quality measurements exist. A sparse detection archive cannot establish
  satellite coverage or a missed observation.

Analysis state is stored in the Events table. Individual sourced inputs and
derived outputs are stored in the Evidence table. Missing or failed sources
remain explicit and do not become negative evidence. Final score inputs are
written only after the analysis reaches a validated complete state. Results
are projected through
`GET /events/{event_id}/exposure`, `GET /events/{event_id}/sensor-comparison`,
and `GET /events/{event_id}/environmental-analysis`.

## Run for the demo

New events are queued automatically. The UI exposes **Run environmental
analysis** as an authenticated retry/reprocess action for one event. It does
not request an agent investigation. A reviewer decision is required before a
reviewer can request investigation.

For a bounded operator batch using the AWS CLI credential chain:

```bash
export EVENT_TABLE='<deployed Events table name>'
export EVIDENCE_TABLE='<deployed Evidence table name>'
python scripts/enrich_environmental.py --region '<AWS region>' --event-id '<event id>'
```

The batch defaults to one event. `--limit 5` processes at most five replay
events sequentially, while `--all` processes every existing event. Each event
is attempted independently and incomplete source results remain explicit.
Use a pause for provider rate control: WorldPop is an external source, so a
full replay batch can take significant time and should be run only after quota
and cost checks.

## Current replay source limits

The deployed replay archive inspected on 2026-10-09 contains GK2A AMI
observations but no second-sensor records, no source coverage/quality records,
and no per-event exposure estimates. Therefore the real data can support
event-time weather and potential population exposure, while comparison and
blind-spot layers remain unavailable until those specific input datasets are
attached. The UI must preserve these honest unavailable states. Replay rows
that existed before the automatic trigger was deployed require a bounded
replay/enrichment run to enter the same workflow.
