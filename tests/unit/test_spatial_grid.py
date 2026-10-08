import pytest

from backend.processing.spatial import GridSpec


def test_metric_grid_is_stable_and_local_points_share_cell():
    grid = GridSpec(cell_size_m=5_000)

    first = grid.cell_id(30.9000, 75.8500)
    nearby = grid.cell_id(30.9010, 75.8510)

    assert first == nearby
    assert first.startswith("grid-v1-utm43n-5000m-")


@pytest.mark.parametrize("latitude,longitude", [(91, 75), (30, 181)])
def test_grid_rejects_out_of_range_coordinates(latitude, longitude):
    with pytest.raises(ValueError):
        GridSpec().cell_id(latitude, longitude)
