# Potential Exposure / Impact Corridor

## MVP

Estimate potential downwind population exposure using:

- event location
- historical/reanalysis wind
- configurable directional corridor
- population raster

This is an exposure estimate, NOT a smoke concentration/AQI forecast.

## Calculation

1. Obtain wind at event time.
2. Convert direction to downwind bearing.
3. Build a configurable wedge/corridor.
4. Intersect with population raster.
5. Aggregate population.
6. Store method and limitations.

## Output

```json
{
  "population_estimate": 12400,
  "corridor_area_km2": 38.2,
  "wind_direction_deg": 135,
  "wind_speed_kmh": 18,
  "method": "DIRECTIONAL_CORRIDOR",
  "confidence": "MEDIUM",
  "limitations": [
    "Not a dispersion model",
    "Population grid is approximately 1 km",
    "Wind is reanalysis data"
  ]
}
```

## Advanced

HYSPLIT can model atmospheric trajectories and dispersion, including wildfire smoke. Treat this as a later phase because it adds meteorological inputs, emissions assumptions and validation requirements.

## Tests

- cardinal wind directions
- zero/low wind
- missing weather
- no population
- corridor outside raster
- invalid coordinates
- population aggregation
