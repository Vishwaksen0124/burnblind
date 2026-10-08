"""Geodesic downwind screening corridor geometry."""

from dataclasses import dataclass
import math

from pyproj import Geod


@dataclass(frozen=True, slots=True)
class CorridorResult:
    geometry: dict | None
    downwind_bearing_degrees: float | None
    distance_km: float
    status: str
    assumptions: tuple[str, ...]


_GEOD = Geod(ellps="WGS84")


def downwind_corridor(
    latitude: float,
    longitude: float,
    wind_speed_m_s: float | None,
    wind_direction_degrees: float | None,
    duration_hours: float,
    width_km: float,
) -> CorridorResult:
    """Build a straight-line screening corridor from meteorological wind.

    Wind direction is the direction wind comes from; the corridor follows the
    opposite bearing. This is advection geometry only, not a smoke-dispersion
    model. Population exposure requires a separate population surface.
    """
    for name, value, low, high in (
        ("latitude", latitude, -90, 90),
        ("longitude", longitude, -180, 180),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be between {low} and {high}")
    if not math.isfinite(duration_hours) or duration_hours <= 0:
        raise ValueError("duration_hours must be finite and positive")
    if not math.isfinite(width_km) or width_km <= 0:
        raise ValueError("width_km must be finite and positive")
    if wind_speed_m_s is None or wind_direction_degrees is None:
        return CorridorResult(
            geometry=None,
            downwind_bearing_degrees=None,
            distance_km=0,
            status="WEATHER_UNAVAILABLE",
            assumptions=("wind context missing", "population exposure unavailable"),
        )
    if (
        isinstance(wind_speed_m_s, bool)
        or not isinstance(wind_speed_m_s, (int, float))
        or not math.isfinite(wind_speed_m_s)
        or wind_speed_m_s < 0
    ):
        raise ValueError("wind_speed_m_s must be finite and non-negative")
    if (
        isinstance(wind_direction_degrees, bool)
        or not isinstance(wind_direction_degrees, (int, float))
        or not math.isfinite(wind_direction_degrees)
        or not 0 <= wind_direction_degrees < 360
    ):
        raise ValueError("wind_direction_degrees must be in [0, 360)")

    bearing = (float(wind_direction_degrees) + 180) % 360
    distance_m = float(wind_speed_m_s) * duration_hours * 3600
    half_width_m = width_km * 500
    if distance_m == 0:
        return CorridorResult(
            geometry=None,
            downwind_bearing_degrees=bearing,
            distance_km=0,
            status="NO_DOWNWIND_DISPLACEMENT",
            assumptions=("wind speed is zero", "population exposure unavailable"),
        )

    end_lon, end_lat, _ = _GEOD.fwd(longitude, latitude, bearing, distance_m)
    start_left_lon, start_left_lat, _ = _GEOD.fwd(longitude, latitude, bearing - 90, half_width_m)
    end_left_lon, end_left_lat, _ = _GEOD.fwd(end_lon, end_lat, bearing - 90, half_width_m)
    end_right_lon, end_right_lat, _ = _GEOD.fwd(end_lon, end_lat, bearing + 90, half_width_m)
    start_right_lon, start_right_lat, _ = _GEOD.fwd(longitude, latitude, bearing + 90, half_width_m)
    ring = [
        [start_left_lon, start_left_lat],
        [end_left_lon, end_left_lat],
        [end_right_lon, end_right_lat],
        [start_right_lon, start_right_lat],
        [start_left_lon, start_left_lat],
    ]
    return CorridorResult(
        geometry={"type": "Polygon", "coordinates": [ring]},
        downwind_bearing_degrees=bearing,
        distance_km=distance_m / 1000,
        status="CORRIDOR_ESTIMATED_POPULATION_UNAVAILABLE",
        assumptions=(
            "wind remains steady for the supplied duration",
            "straight-line advection; no plume rise or atmospheric dispersion",
            "corridor width is a screening assumption",
            "population exposure unavailable until a population surface is supplied",
        ),
    )
