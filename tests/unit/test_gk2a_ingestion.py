from datetime import timezone

import pytest

from backend.ingestion.gk2a_historical import DatasetRecordError, iter_gk2a_hotspots


FILENAME = "GK2-AMI_FireHotspotsData_2025_10-11_Punjab_India_v1.txt"
METADATA = f"""FILE_NAME = {FILENAME}
YEAR = 2025
MONTHS = October (10) & November (11)
REGION = Punjab, India
SATELLITE = GEOKOMPSAT-2A
SENSOR = Advanced Meteorological Imager (AMI)
"""

SOURCE = METADATA + """DOI: 10.5281/zenodo.20084790
FORMAT: 1=Year 2=Month 3=Date 4=Hour 5=Minutes 6=Longitude (deg.) 7=Latitude (deg.) 8=Brightness Temperature Difference Ref. 9=Brightness Temperature [0.38 micron] 10=Brightness Temperature [11.2 micron] 11=Confidence_Flag
2025 10 01 13 00 74.3756 30.1837 7.3787 304.3759 293.6568 1
"""


def test_gk2a_parser_preserves_source_values_and_converts_ist_to_utc(tmp_path):
    path = tmp_path / FILENAME
    path.write_text(SOURCE, encoding="utf-8")

    record, = iter_gk2a_hotspots(path, lambda lat, lon: "grid-v1-test")

    assert record.source == "GK2A_AMI"
    assert record.observed_at_utc.isoformat() == "2025-10-01T07:30:00+00:00"
    assert record.observed_at_utc.tzinfo == timezone.utc
    assert record.latitude == 30.1837
    assert record.longitude == 74.3756
    assert record.grid_id == "grid-v1-test"
    assert record.brightness_temperature_difference_ref == 7.3787
    assert record.brightness_temperature_038_micron_k == 304.3759
    assert record.brightness_temperature_112_micron_k == 293.6568
    assert record.confidence is None
    assert record.confidence_flag == 1
    assert record.source_version == "zenodo:20084790:v1"


def test_gk2a_parser_rejects_malformed_record_instead_of_skipping(tmp_path):
    path = tmp_path / FILENAME
    path.write_text(SOURCE.replace("2025 10 01 13 00 74.3756 30.1837 7.3787 304.3759 293.6568 1", "2025 10 invalid"), encoding="utf-8")

    with pytest.raises(DatasetRecordError, match="expected 11 fields"):
        list(iter_gk2a_hotspots(path, lambda lat, lon: "grid"))


def test_gk2a_parser_requires_publisher_format_line(tmp_path):
    path = tmp_path / FILENAME
    path.write_text(METADATA, encoding="utf-8")

    with pytest.raises(DatasetRecordError, match="missing publisher FORMAT"):
        list(iter_gk2a_hotspots(path, lambda lat, lon: "grid"))


def test_gk2a_parser_rejects_mislabeled_region(tmp_path):
    path = tmp_path / FILENAME
    path.write_text(SOURCE.replace("REGION = Punjab, India", "REGION = Haryana, India"), encoding="utf-8")

    with pytest.raises(DatasetRecordError, match="REGION does not match"):
        list(iter_gk2a_hotspots(path, lambda lat, lon: "grid"))


def test_gk2a_parser_rejects_points_outside_study_envelope(tmp_path):
    path = tmp_path / FILENAME
    path.write_text(SOURCE.replace("74.3756 30.1837", "10.0000 10.0000"), encoding="utf-8")

    with pytest.raises(DatasetRecordError, match="study envelope"):
        list(iter_gk2a_hotspots(path, lambda lat, lon: "grid"))
