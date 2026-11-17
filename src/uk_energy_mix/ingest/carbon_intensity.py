import argparse
import datetime
import json
import logging
import sys
from time import perf_counter, sleep

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
from uk_energy_mix.dates import date_window, expected_records, chunk_dates

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/intensity"
DATASET = "national-intensity"
HEADERS = {"Accept": "application/json"}
WINDOW = 1 # day
RATE_LIMIT = 1
UTC = "UTC"

logger = logging.getLogger(__name__)

def build_url(source: str, 
              start_date: datetime.date, 
              end_date: datetime.date) -> str:
    """Build URL to query REST API. Make end date exclusive, start datetime 00:30 and both dates ISO8601."""
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
    return count


def main(argv: list[str] | None = None) -> int:
    snapshot_date = datetime.datetime.now(datetime.UTC).date()
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "--datasets",
            nargs="+",
            default=DATASET,
            help="Optionally select which datasets you would like to fetch. Default is all",
        )
    parser.add_argument(
        "--start",
        type=datetime.date.fromisoformat,
        default=None,
    )
    parser.add_argument(
        "--end",
        type=datetime.date.fromisoformat,
        default=None,
    )
    parser.add_argument(
        "--window",
        type=int,
        default=WINDOW
    )
    args = parser.parse_args(argv)
    dataset = args.datasets
    window = args.window
    if not 0 < window <= 14:
        parser.error("Window must be between 1 and 14 inclusive")
    start_date, end_date = date_window(snapshot_date, window, args.start, args.end)
    if start_date > end_date:
        parser.error("Start date cannot be after end date")
    dates = chunk_dates(start_date, end_date, window)
    failures = []
    for i, (start, end) in enumerate(dates):
        if i > 0:
            sleep(RATE_LIMIT)
        logger.info(
            "Fetching data from %s %s - %s on %s",
            dataset, 
            start, 
            end, 
            snapshot_date
        )
        try:
            t0 = perf_counter()
            url = build_url(SOURCE_URL, start, end)
            r = fetch(url, HEADERS)
            expected_count = expected_records(start, end, UTC)
            count = validate(r)
            if count != expected_count:
                logger.warning(
                    "Expected %s records but fetched %s. From %s, %s - %s",
                    expected_count,
                    count,
                    dataset,
                    start_date,
                    end_date,
                )
            target = file_path(SOURCE_NAME, snapshot_date, start, end, dataset)
            write(r, target)
            t_end = perf_counter()
            elapsed = t_end - t0
            logger.info(
                "Successfully fetched and wrote %s %s records from %s - %s in %.2fs",
                count,
                dataset,
                start_date,
                end_date,
                elapsed,
            )
        except Exception:
            logger.exception("Ingestion failed for %s - %s", start, end)
            failures.append((start, end))
    if failures:
        logger.error("The following datasets failed: %s", failures)
        return 1
    return 0
    

if __name__ == "__main__":
    setup_logging()
    code = main()
    sys.exit(code)

