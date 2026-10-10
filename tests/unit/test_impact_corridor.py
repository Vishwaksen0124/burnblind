import pytest

from backend.impact.corridor import downwind_corridor


def test_wind_from_west_moves_screening_corridor_eastward():
    result = downwind_corridor(
        latitude=30.9,
        longitude=75.85,
        wind_speed_m_s=2,
        wind_direction_degrees=270,
        duration_hours=1,
        width_km=5,
    )

    assert result.status == "CORRIDOR_GEOMETRY_READY"
    assert result.downwind_bearing_degrees == 90
    assert result.distance_km == pytest.approx(7.2)
    assert result.geometry["type"] == "Polygon"
    ring = result.geometry["coordinates"][0]
    assert ring[0] == ring[-1]
    assert "no plume rise or atmospheric dispersion" in result.assumptions[1]


def test_missing_weather_returns_no_corridor():
    result = downwind_corridor(30.9, 75.85, None, None, 1, 5)

    assert result.geometry is None
    assert result.status == "WEATHER_UNAVAILABLE"


def test_zero_wind_has_no_downwind_displacement():
    result = downwind_corridor(30.9, 75.85, 0, 0, 1, 5)

    assert result.geometry is None
    assert result.status == "NO_DOWNWIND_DISPLACEMENT"


def test_corridor_rejects_invalid_wind_direction():
    with pytest.raises(ValueError, match="wind_direction_degrees"):
        downwind_corridor(30.9, 75.85, 1, 360, 1, 5)
