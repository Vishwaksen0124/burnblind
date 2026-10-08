"""Spatial identifiers for the Punjab/Haryana MVP study area."""

from dataclasses import dataclass
import math

from pyproj import Transformer


@dataclass(frozen=True, slots=True)
class GridSpec:
    """A fixed-size metric grid in UTM zone 43N (EPSG:32643).

    The study geography lies around the zone's central meridian. Projecting
    before indexing keeps cell dimensions in meters instead of treating
    latitude/longitude degrees as distances.
    """

    cell_size_m: int = 5_000
    version: str = "grid-v1"

    def __post_init__(self) -> None:
        if isinstance(self.cell_size_m, bool) or not isinstance(self.cell_size_m, int) or self.cell_size_m <= 0:
            raise ValueError("cell_size_m must be a positive integer")
        if not self.version or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in self.version):
            raise ValueError("version must be a non-empty safe identifier")

    def cell_id(self, latitude: float, longitude: float) -> str:
        if not math.isfinite(latitude) or not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not math.isfinite(longitude) or not -180 <= longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        easting, northing = _TO_UTM43.transform(longitude, latitude)
        col = math.floor(easting / self.cell_size_m)
        row = math.floor(northing / self.cell_size_m)
        return f"{self.version}-utm43n-{self.cell_size_m}m-{col}-{row}"


_TO_UTM43 = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
