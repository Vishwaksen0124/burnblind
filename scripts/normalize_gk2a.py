"""Normalize one downloaded GK2A source file to canonical JSON Lines."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Support running this repository utility directly without requiring an
# editable package installation first.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.ingestion.gk2a_historical import iter_gk2a_hotspots
from backend.processing.spatial import GridSpec
from backend.ingestion.normalization import write_fire_observations


def normalize_file(input_path: Path, output_path: Path) -> int:
    grid = GridSpec()
    return write_fire_observations(iter_gk2a_hotspots(input_path, grid.cell_id), output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Publisher-format GK2A `.txt` file")
    parser.add_argument("--output", type=Path, help="Output JSONL path; defaults beside input under processed/gk2a")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"input file does not exist: {args.input}")

    output = args.output or Path("data/processed/gk2a") / f"{args.input.stem}.jsonl"
    count = normalize_file(args.input, output)
    print(f"normalized {count} records -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
