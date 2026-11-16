import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from time import perf_counter

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from uk_energy_mix.ingest.config import ROOT_DIR
from uk_energy_mix.ingest import http

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/intensity/date"
HEADERS = {"Accept": "application/json"}

logger = logging.getLogger(__name__)


def file_path(dt: datetime.date) -> Path:
    """Generate the file path based on the data source and given date"""
    filepath = ROOT_DIR / "data" / "raw" / SOURCE_NAME / f"{dt}.json"
    return filepath

def build_url(source: str, dt: datetime.date) -> str:
    url = f"{source}/{dt}"
    return url

fetch = retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=30),
    retry=retry_if_exception(http.is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)(http.fetch)


def validate(text: str) -> int:
    """Check that what we fetch is what we want before we write it to a file"""
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TypeError(f"Fetched object is of type {type(payload).__name__}")
    if "data" not in payload:
        raise ValueError(f"Fetched object has keys {list(payload)}")
    count = len(payload["data"])
    if count not in {46, 48, 50}:
        raise ValueError(f"Fetched object is of length {count}")
    return count


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
        t0 = perf_counter()
        url = build_url(SOURCE_URL, dt)
        r = fetch(url, HEADERS)
        count = validate(r)
        target = file_path(dt)
        write(r, target)
        t_end = perf_counter()
        elapsed = t_end - t0
        logger.info("Successfully fetched and wrote %s records from %s in %.2fs",
                    count,
                    url,
                    elapsed)
    except Exception:
        logger.exception("Ingestion failed for %s", dt)
        sys.exit(1)
