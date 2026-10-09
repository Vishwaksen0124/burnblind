from datetime import date
from urllib.error import URLError

import pytest

from backend.ingestion.firms_api import FirmsApiError, fetch_standard_processing


CSV = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"
    "30.9,75.85,330.44,0.40,0.37,2025-10-01,1030,N20,VIIRS,n,2.0,295.66,2.24,D\n"
)
MAP_KEY = "0123456789abcdef0123456789abcdef"


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return CSV.encode()[:size]


def test_firms_api_records_are_normalized_and_have_deterministic_ids():
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return Response()

    first = fetch_standard_processing(MAP_KEY, date(2025, 10, 1), date(2025, 10, 1), opener=opener)
    second = fetch_standard_processing(MAP_KEY, date(2025, 10, 1), date(2025, 10, 1), opener=opener)

    assert len(first) == 1
    assert first[0].source == "NASA_FIRMS"
    assert first[0].fire_id == second[0].fire_id
    assert first[0].grid_id.startswith("grid-v1-utm43n")
    assert "VIIRS_SNPP_SP" in requests[0].full_url
    assert requests[0].full_url.endswith("/1/2025-10-01")


def test_firms_api_rejects_large_range_and_sanitizes_transport_errors():
    with pytest.raises(ValueError, match="five days"):
        fetch_standard_processing(MAP_KEY, date(2025, 10, 1), date(2025, 10, 6))

    def failing_opener(request, timeout):
        raise URLError(request.full_url)

    with pytest.raises(FirmsApiError) as error:
        fetch_standard_processing(MAP_KEY, date(2025, 10, 1), date(2025, 10, 1), opener=failing_opener)
    assert MAP_KEY not in str(error.value)
