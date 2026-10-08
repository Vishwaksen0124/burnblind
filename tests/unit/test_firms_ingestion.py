import pytest

from backend.ingestion.errors import IngestionRecordError
from backend.ingestion.firms import iter_firms_csv


def test_viirs_firms_row_is_normalized_without_reinterpreting_confidence(tmp_path):
    # Synthetic schema fixture only; it is not NASA observation data.
    path = tmp_path / "firms_viirs_fixture.csv"
    path.write_text(
        "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
        "30.9,75.85,330.44,0.40,0.37,2025-10-01,35,N20,VIIRS,n,2.0,295.66,2.24,D\n",
        encoding="utf-8",
    )

    record, = iter_firms_csv(path, lambda lat, lon: "grid-v1-test")

    assert record.source == "NASA_FIRMS"
    assert record.observed_at_utc.isoformat() == "2025-10-01T00:35:00+00:00"
    assert record.source_confidence == "n"
    assert record.confidence is None
    assert record.channel_1_name == "bright_ti4"
    assert record.channel_2_name == "bright_ti5"
    assert record.brightness_temperature_channel_1_k == 330.44
    assert record.frp_mw == 2.24
    assert record.grid_id == "grid-v1-test"


def test_modis_firms_row_uses_product_specific_brightness_columns(tmp_path):
    # Synthetic schema fixture only; it is not NASA observation data.
    path = tmp_path / "firms_modis_fixture.csv"
    path.write_text(
        "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight\n"
        "30.9,75.85,311.65,1.03,1.02,2025-10-01,5,Terra,MODIS,83,6.1,292.65,10.58,N\n",
        encoding="utf-8",
    )

    record, = iter_firms_csv(path, lambda lat, lon: "grid-v1-test")

    assert record.observed_at_utc.isoformat() == "2025-10-01T00:05:00+00:00"
    assert record.source_confidence == "83"
    assert record.channel_1_name == "brightness"
    assert record.channel_2_name == "bright_t31"
    assert record.track_size_km == 1.02


def test_firms_parser_rejects_unknown_schema(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text("latitude,longitude\n30,75\n", encoding="utf-8")

    with pytest.raises(IngestionRecordError, match="missing FIRMS columns"):
        list(iter_firms_csv(path, lambda lat, lon: "grid"))


def test_firms_parser_rejects_invalid_acquisition_time(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text(
        "latitude,longitude,bright_ti4,acq_date,acq_time,satellite,instrument,confidence,version\n"
        "30.9,75.85,330.4,2025-10-01,2360,N20,VIIRS,n,2.0\n",
        encoding="utf-8",
    )

    with pytest.raises(IngestionRecordError, match="invalid FIRMS record"):
        list(iter_firms_csv(path, lambda lat, lon: "grid"))
