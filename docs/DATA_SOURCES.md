# BurnBlind — Data Sources & Provenance

## 1. Source-of-truth principle

No historical or environmental observation used in the final system should be presented as real unless it has a recorded source.

Every dataset must have:

```text
source_name
source_url
provider
coverage_start
coverage_end
geography
access_method
license_or_usage_notes
download_timestamp
source_version
processing_version
```

## 2. Primary historical baseline — GK2A

Dataset:

**Hourly Fire Detection Dataset of Post-monsoon Stubble Burning in Northwestern India derived from GK2-AMI Geostationary Satellite Observations**

Source:
https://zenodo.org/records/20084790

Pinned implementation release: **v1**, DOI `10.5281/zenodo.20084790`, licensed
CC BY 4.0. The local downloader records each source file's size, checksum,
retrieval timestamp, and URL in `data/raw/gk2a/manifest.json` (the raw directory
is intentionally excluded from Git).

Coverage:
2019–2025, October–November, Punjab and Haryana.

The dataset is derived from GK2A-AMI observations and provides hourly fire/hot-smoke detections. The publisher notes that the observations cover 12:00–18:00 IST and that spatial resolution over northwestern India is approximately 3.8–4.0 km.

Use it for:

- historical fire frequency
- spatial fire density
- seasonal patterns
- time-of-day patterns
- historical context

Important:

This dataset is derived from GK2A and therefore should not be treated as independent ground truth for GK2A itself.

The source text records contain year, month, date, hour, minute, longitude,
latitude, brightness-temperature difference, two brightness temperatures,
and a publisher confidence flag. The release's observations are reported in
IST at hourly times; ingestion converts them to UTC and retains the original
measurements and confidence flag. The numeric confidence flag is not treated
as a calibrated probability. Aggregated values are detection-record counts,
not unique fire counts.

The current local import covers all 14 Punjab/Haryana files for 2019–2025.
Every downloaded file is checked against the checksum published by Zenodo;
every parsed row is checked against its file's embedded year, region, and
October/November coverage metadata and the broad study envelope
`73°–78°E, 27°–33°N`. This envelope is a source-quality check, not an
administrative boundary polygon.
The normalized historical summary is generated locally and excluded from Git.

## 3. Independent reference — NASA FIRMS

Source:
https://firms.modaps.eosdis.nasa.gov/active_fire/

Use historical MODIS/VIIRS active-fire products for:

- independent cross-sensor observations
- validation
- sensor disagreement
- historical comparison

Do not equate a FIRMS non-detection with proof that a GK2A detection is false.

The implemented archive adapter targets standard-processing `MODIS_SP`,
`VIIRS_SNPP_SP`, and `VIIRS_NOAA20_SP` CSV products over a Punjab/Haryana
screening bounding box. NASA requires a free FIRMS MAP_KEY for its area API;
the acquisition script reads it from `FIRMS_MAP_KEY` and does not write it to
logs or manifests. Historical acquisitions are split into requests of at most
five days. Do not use NRT/RT/URT as a substitute for historical standard
products without recording that source distinction.

Account for:

- spatial resolution
- observation timestamp
- viewing geometry
- cloud/quality flags

## 4. Current/near-current GK2A — AWS Open Data

Source:
https://registry.opendata.aws/noaa-gk2a-pds/

AWS dataset:
`arn:aws:s3:::noaa-gk2a-pds`

AWS region:
`us-east-1`

NOAA documents full-disk GK2A updates at 10-minute frequency, with higher-frequency targeted products also available.

AWS CLI access does not require an AWS account for the public dataset:

```bash
aws s3 ls --no-sign-request s3://noaa-gk2a-pds/
```

Use this source only after the historical baseline is working.

## 5. Weather

The MVP needs:

- timestamp
- latitude
- longitude
- wind speed
- wind direction

The selected provider and implemented adapter are documented below.

The MVP adapter uses the Open-Meteo historical archive with the ERA5 model,
requesting 10 m wind speed in m/s and wind direction for the event's UTC hour.
Returned ERA5 values are reanalysis/context, not direct measurements at the
event coordinate. Missing hourly fields remain unavailable in the contract.

## 6. Population/exposure

The MVP needs a population surface that can be spatially intersected with the estimated downwind corridor.

The exact dataset must be selected and documented before implementation.

## 7. Data acquisition order

```text
1. GK2A historical dataset
2. FIRMS historical data
3. weather sample
4. population sample
5. current GK2A AWS data
6. current FIRMS
```

Do not begin with large raw satellite downloads.

## 8. Data quality rules

Reject/quarantine records with:

- invalid coordinates
- invalid timestamps
- impossible measurements
- missing required identifiers

Retain source quality flags when available.

## 9. Reproducibility

Store a manifest such as:

```json
{
  "dataset": "gk2a_historical_fire",
  "source_url": "...",
  "source_version": "v1",
  "downloaded_at": "...",
  "processing_version": "preprocess-v1"
}
```

Never rely on "latest" without recording the actual version/date used.

## 10. Selected weather source — Open-Meteo

For the MVP, use Open-Meteo as the historical/current weather interface when its terms and rate limits fit the implementation.

Historical source:
https://open-meteo.com/en/docs/historical-weather-api

Required variables:
- `wind_speed_10m`
- `wind_direction_10m`

Open-Meteo's historical API provides ERA5/ERA5-Land reanalysis. Historical wind should be described as reanalysis/context, not as a direct observation at the event coordinate.

For live/near-current wind, use the corresponding Open-Meteo forecast/current endpoint if required.

Record:
- API request timestamp
- requested coordinate
- returned model/source
- weather timestamp
- provider/version metadata where available

Do not silently substitute weather from another provider without updating this document.

## 11. Selected population source — WorldPop

For the MVP, use WorldPop population grids.

Preferred India dataset:
https://hub.worldpop.org/geodata/summary?id=73803

WorldPop also provides a population API:
https://api.worldpop.org/v2/

Use population only to estimate exposure within the screening corridor.

WorldPop data is licensed under CC BY 4.0; include attribution in the project documentation and UI/source panel where appropriate.

Important:
- population is an estimate, not a live headcount
- do not expose individual-level information
- aggregate at grid/corridor level
- do not use population data for surveillance or individual targeting

## 12. Geospatial processing stack

The backend should use standard geospatial libraries where needed:

- GeoPandas
- Shapely
- PyProj
- Rasterio
- NumPy/Pandas

Use them only where required.

For the MVP:
- WGS84 / EPSG:4326 for API/storage interchange
- projected calculations where distance/area accuracy requires it
- document CRS transformations

Do not calculate distance/area by treating latitude/longitude degrees as kilometers.

## 13. Data source fallback policy

If an external source is unavailable:

1. do not fabricate data,
2. use a previously downloaded, licensed historical fixture if permitted,
3. clearly label replay/demo mode,
4. reduce confidence when required,
5. keep provenance visible.

A demo fixture must never be presented as live data.
