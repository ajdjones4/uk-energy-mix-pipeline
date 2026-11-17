import argparse
import datetime
import json
import logging
import sys
from time import perf_counter

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from uk_energy_mix.exceptions import PayloadValidationError
from uk_energy_mix.ingest import http
from uk_energy_mix.log_config import setup_logging
from uk_energy_mix.storage import file_path, write

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/intensity"
DATASET = "national-intensity"
HEADERS = {"Accept": "application/json"}

logger = logging.getLogger(__name__)

def build_url(source: str, 
              start_date: datetime.date, 
              end_date: datetime.date) -> str:
    """Build URL to query REST API. Make end date exclusive and both dates ISO8601."""
    end_date_exclusive = end_date + datetime.timedelta(days=1)
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=datetime.UTC)
    start_date_corrected = start_datetime + datetime.timedelta(minutes=30)
    end_datetime = datetime.datetime.combine(end_date_exclusive, datetime.time.min, tzinfo=datetime.UTC)
    start_date_string = start_date_corrected.strftime('%Y-%m-%dT%H:%MZ')
    end_date_string = end_datetime.strftime('%Y-%m-%dT%H:%MZ')
    url = (f"{source}/{start_date_string}/{end_date_string}")
    return url

fetch = retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=30),
    retry=retry_if_exception(http.is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)(http.fetch)


def validate(text: str) -> int:
    """Validate structure of payload and return number of records"""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as err:
        raise PayloadValidationError(
            "Carbon Intensity payload wasn't valid JSON") from err
    if not isinstance(payload, dict):
        raise PayloadValidationError("Fetched object is of type "
                                    f"{type(payload).__name__}")
    if "data" not in payload:
        raise PayloadValidationError("Fetched object has keys "
                                    f"{list(payload)}")
    count = len(payload["data"])
    if count not in {46, 48, 50}:
        raise PayloadValidationError(f"Fetched object is of length {count}")
    return count


def main(argv: list[str] | None = None) -> int:
    snapshot_date = datetime.datetime.now(datetime.UTC).date()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "date",
        nargs="?",
        type=datetime.date.fromisoformat,
        default=snapshot_date,
    )
    args = parser.parse_args(argv)
    dt = args.date
    logger.info("Fetching carbon intensity data for %s", dt)
    try:
        t0 = perf_counter()
        url = build_url(SOURCE_URL, dt)
        r = fetch(url, HEADERS)
        count = validate(r)
        target = file_path(SOURCE_NAME, snapshot_date, dt, dt, DATASET)
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

