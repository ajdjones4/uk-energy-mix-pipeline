import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from time import perf_counter, gmtime

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from uk_energy_mix.config import ROOT_DIR
from uk_energy_mix.ingest import http
from uk_energy_mix.storage import write, file_path
from uk_energy_mix.log_config import setup_logging

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/intensity/date"
DATASET = "national-intensity"
HEADERS = {"Accept": "application/json"}

logger = logging.getLogger(__name__)

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


def main(argv: list[str] | None = None) -> int:
    run_date = datetime.datetime.now(datetime.UTC).date()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        nargs="?",
        type=datetime.date.fromisoformat,
        default=run_date,
    )
    args = parser.parse_args(argv)
    dt = args.date
    logger.info("Fetching carbon intensity data for %s", dt)
    try:
        t0 = perf_counter()
        url = build_url(SOURCE_URL, dt)
        r = fetch(url, HEADERS)
        count = validate(r)
        target = file_path(SOURCE_NAME, run_date, dt, dt, DATASET)
        write(r, target)
        t_end = perf_counter()
        elapsed = t_end - t0
        logger.info("Successfully fetched and wrote %s records from %s in %.2fs",
                    count,
                    url,
                    elapsed)
    except Exception:
        logger.exception("Ingestion failed for %s", dt)
        return 1
    return 0
    

if __name__ == "__main__":
    setup_logging()
    code = main()
    sys.exit(code)

