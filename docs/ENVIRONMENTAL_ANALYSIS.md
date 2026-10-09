# Environmental analysis

Environmental enrichment runs independently from Strands. It does not call
DeepSeek or create an investigation report.

## Flow

```text
Reviewer requests analysis for one candidate
  → authenticated API marks its environmental status PROCESSING
  → FIFO SQS environmental queue
  → environmental Lambda reads that event and attached evidence
  → Open-Meteo ERA5 event-time wind
  → geodesic downwind screening corridor
  → WorldPop Global2 population estimate
  → strict comparison of attached independent sensor evidence
  → feature summary on the event + source records in EvidenceTable
  → UI polls status and displays sources, estimates, and limitations
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
derived outputs are stored in the Evidence table and projected through
`GET /events/{event_id}/exposure`, `GET /events/{event_id}/sensor-comparison`,
and `GET /events/{event_id}/environmental-analysis`.

## Run for the demo

The UI exposes **Run environmental analysis** on an event. It requires an
invited reviewer session and analyzes only that event. This action does not
request an agent investigation.

For a bounded operator batch using the AWS CLI credential chain:

```bash
export EVENT_TABLE='<deployed Events table name>'
export EVIDENCE_TABLE='<deployed Evidence table name>'
python scripts/enrich_environmental.py --region '<AWS region>' --event-id '<event id>'
```

The batch defaults to one event. `--limit 5` processes at most five replay
events sequentially, with a one-second delay between events. WorldPop is an
external asynchronous source, so larger batches can take significant time.

## Current replay source limits

The deployed replay archive inspected on 2026-10-09 contains GK2A AMI
observations but no second-sensor records, no source coverage/quality records,
and no per-event exposure estimates. Therefore the real data can support
event-time weather and potential population exposure, while comparison and
blind-spot layers remain unavailable until those specific input datasets are
attached. The UI must preserve these honest unavailable states.
