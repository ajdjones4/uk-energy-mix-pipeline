import argparse
import datetime
import logging
import sys
from pathlib import Path
from time import perf_counter

import requests

from uk_energy_mix.ingest.config import ROOT_DIR

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/intensity/date"
HEADERS = {"Accept": "application/json"}

logger = logging.getLogger(__name__)


def file_path(dt: datetime.date) -> Path:
    """Generate the file path based on the data source and given date"""
    filepath = ROOT_DIR / "data" / "raw" / SOURCE_NAME / f"{dt}.json"
    return filepath


def fetch(source: str, dt: datetime.date, headers: dict | None = None) -> str:
    """Make the API call, return the json as raw text"""
    logger.info("Fetching data from: %s/%s", source, dt)
    start = perf_counter()
    response = requests.get(f"{source}/{dt}", headers=headers, timeout=10)
    end = perf_counter()
    elapsed = end - start
    response.raise_for_status()
    logger.info("Fetched %s chars in %.2fs", len(response.text), elapsed)
    return response.text


def write(data: str, filepath: Path) -> None:
    """Create parent directory if necessary and write text to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(data)
    logger.info("Written %s chars to %s", len(data), filepath)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        nargs="?",
        type=datetime.date.fromisoformat,
        default=datetime.date.today(),
    )
    args = parser.parse_args()
    dt = args.date
    logger.info("Fetching carbon intensity data for %s", dt)
    try:
        r = fetch(SOURCE_URL, dt, HEADERS)
        target = file_path(dt)
        write(r, target)
    except Exception:
        logger.exception("Ingestion failed for %s", dt)
        sys.exit(1)
