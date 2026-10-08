# Data Pipeline V2

## Sources

### GK2A historical fire dataset
2019–2025 Punjab/Haryana hourly fire/hot-smoke detections for October/November.

### NASA FIRMS
VIIRS/MODIS/Landsat active-fire observations for independent comparison and validation.

### GK2A AWS Open Data
Use for live/near-current satellite processing if implemented.

### Open-Meteo
Historical/reanalysis wind direction and speed.

### WorldPop
Gridded population estimates for aggregate exposure.

## Provenance

Every derived record stores:

- source
- source URL
- coverage period
- source timestamp
- ingestion timestamp
- processing version
- geographic coverage
- attribution/license notes

## Storage

```text
S3
 raw/
 historical/
 processed/
 provenance/
 replay/

DynamoDB
 Events
 Investigations
 ReviewOutcomes
```

S3 stores large/raw/processed objects. DynamoDB stores queryable operational state.
