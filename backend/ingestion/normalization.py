"""Atomic canonical JSONL writers shared by ingestion adapters."""

from pathlib import Path
import json
import tempfile
from typing import Iterable

from backend.common.models import FireObservation
from backend.common.serialization import fire_observation_to_dict


def write_fire_observations(records: Iterable[FireObservation], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as temp:
        temporary_path = Path(temp.name)
        try:
            for record in records:
                temp.write(json.dumps(fire_observation_to_dict(record), separators=(",", ":"), allow_nan=False) + "\n")
                count += 1
            if count == 0:
                raise ValueError("source produced no fire observations")
            temp.flush()
            temporary_path.replace(output_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    return count
