"""Candidate entry point for the BikeMap exercise."""
import argparse
from pathlib import Path


def run(part, ride, out, base_url):
    raise NotImplementedError("Start with the first request in README.md and implement run() in ride.py.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", type=int, choices=range(1, 6))
    parser.add_argument("--ride", type=Path, default=Path("data/canal.geojson"))
    parser.add_argument("--out", type=Path, default=Path("output"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8771")
    args = parser.parse_args()
    try:
        run(args.part, args.ride, args.out, args.base_url)
    except NotImplementedError as exc:
        parser.exit(2, f"{exc}\n")
