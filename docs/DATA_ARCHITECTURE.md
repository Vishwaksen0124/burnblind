# BurnBlind — Data Architecture

## 1. Data layers

```text
External Sources
      ↓
Raw Data
      ↓
Normalized Data
      ↓
Feature Data
      ↓
Event Data
      ↓
Investigation Data
```

## 2. Source categories

### Satellite

Potential sources include:

- geostationary observations
- polar-orbiting active-fire products
- other permitted environmental satellite sources

### Historical fires

Used to establish spatial/temporal fire patterns.

### Weather

Used primarily for wind direction/speed and contextual impact.

### Population

Used to estimate potential exposure.

## 3. S3 layout

```text
raw/
processed/
historical/
investigations/
```

Never overwrite raw data as part of preprocessing.

## 4. Spatial representation

Use a common grid for MVP.

Every observation is mapped to:

```text
grid_id
```

This makes cross-sensor comparison and historical aggregation tractable.

## 5. Temporal representation

Store timestamps in UTC internally.

Convert to local time only for:

- historical time-of-day features
- UI display
- operator-facing reports

## 6. Data quality

Every observation should have quality metadata where available.

Examples:

```text
source
timestamp
quality_flag
cloud_flag
processing_version
```

## 7. Provenance

Every derived feature should be traceable to:

- source
- source timestamp
- processing version
- feature version

This is especially important for the Investigation Agent.


## 8. Initial historical data sources

The MVP should use real historical sources rather than invented historical records.

### GK2A historical fire dataset

Use the publicly released **GK2A 2019–2025 Punjab/Haryana fire hotspot dataset** as the primary historical baseline.

Source:
https://zenodo.org/records/20084790

Use it to derive:

- fire frequency by grid
- fire frequency by month/season
- fire frequency by hour
- spatial fire density
- historical event patterns

### NASA FIRMS

Use NASA FIRMS historical MODIS/VIIRS active-fire data as an independent observation/reference source.

Source:
https://firms.modaps.eosdis.nasa.gov/active_fire/

Use it for:

- independent fire observations
- cross-sensor comparison
- historical validation
- sensor disagreement analysis

### NOAA GK2A AWS Open Data

Use the AWS Open Data GK2A dataset for current/near-current geostationary observations when appropriate.

Source:
https://registry.opendata.aws/noaa-gk2a-pds/

This is particularly relevant to the AWS implementation because the system can process an AWS Open Data source directly.

## 9. Historical vs current data

Do not download years of raw satellite imagery as the first implementation step.

### Phase 1

Use:

```text
GK2A historical fire dataset
+
NASA FIRMS historical observations
```

to build the historical baseline and validate the scoring pipeline.

### Phase 2

Add:

```text
GK2A AWS Open Data
+
current/near-current FIRMS
```

for current event processing.

## 10. Data provenance

For every downloaded dataset, record:

```text
source_name
source_url
download_timestamp
coverage_period
geographic_coverage
file_name
processing_version
license/usage_notes
```

Do not commit large raw datasets to Git.

Store development samples under `data/sample/` and production/historical data in S3.
