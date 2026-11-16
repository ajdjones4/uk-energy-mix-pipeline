import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from time import gmtime, perf_counter, sleep
from zoneinfo import ZoneInfo

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)

from uk_energy_mix.config import ROOT_DIR
from uk_energy_mix.ingest import http
from uk_energy_mix.storage import write, file_path
from uk_energy_mix.dates import date_window, expected_records

SOURCE_NAME = "neso"
SOURCE_URL = "https://api.neso.energy/api/3/action/datastore_search_sql"
DATASETS = {
    "historic-generation-mix": {
        "resource_id": "f93d1835-75bc-43e5-84ad-12472b180a98",
        "datecol": "DATETIME",
        "date_tz": "UTC",
    },
    "historic-demand-data": {
        "resource_id": "8a4a771c-3929-4e56-93ad-cdf13219dea5",
        "datecol": "SETTLEMENT_DATE",
        "date_tz": "Europe/London",
    },
    "demand-data-update": {
        "resource_id": "177f6fa4-ae49-4182-81ea-0c6b35f26ca6",
        "datecol": "SETTLEMENT_DATE",
        "date_tz": "Europe/London",
    },
}
TRAILING_WINDOW = 35  # days
RATE_LIMIT = 30  # seconds

logger = logging.getLogger(__name__)


def build_query(
    resource_id: str, date_col: str, dt_from: datetime.date, dt_to: datetime.date
) -> str:
    """Build the SQL query to retrieve desired data from CKAN API, end date inclusive"""
    dt_end_exclusive = dt_to + datetime.timedelta(days=1)
    sql_query = (
        f'''SELECT * FROM "{resource_id}" '''
        f'''WHERE "{date_col}" >= '{dt_from}' '''
        f'''AND "{date_col}" < '{dt_end_exclusive}' '''
    )
    return sql_query


fetch = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(RATE_LIMIT),
    retry=retry_if_exception(http.is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)(http.fetch)


def validate(text: str) -> int:
    """Check that the payload is structurally correct before we write it to file.
    Return number of records"""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError("NESO payload wasn't valid JSON") from err
    if not isinstance(payload, dict):
        raise TypeError(f"Fetched object is of type {type(payload).__name__}")
    if "success" not in payload:
        raise ValueError(f"Fetched object has keys {list(payload)}")
    if not payload["success"]:
        error_message = payload.get("error", "no error message returned")
        raise ValueError(f"Payload return failed with error message: {error_message}")
    if "result" not in payload:
        raise ValueError("Payload missing results")
    if "records" not in payload["result"]:
        raise ValueError("Payload results missing records")
    records = payload["result"]["records"]
    if not isinstance(records, list):
        raise TypeError(
            "Returned records object is of type "
            f"{type(records).__name__}, should be list."
        )
    count = len(records)
    return count


def main(argv: list[str] | None = None) -> int:
    """Ingest NESO data to raw layer for given dataset/date range."""
    run_date = datetime.datetime.now(datetime.UTC).date()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=list(DATASETS),
        default=list(DATASETS),
        help="Optionally select which datasets you would like to fetch. Default is all",
    )
    parser.add_argument(
        "--start",
        type=datetime.date.fromisoformat,
        default=None,
        help=(
            "Select the start date of data you want to fetch. "
            f"Defaults to {TRAILING_WINDOW - 1} days before the end date"
        ),
    )
    parser.add_argument(
        "--end",
        type=datetime.date.fromisoformat,
        default=None,
        help=(
            "End date (inclusive) for the data you want to fetch. "
            f"Default is {run_date - datetime.timedelta(days=1)}"
        ),
    )
    args = parser.parse_args(argv)
    datasets = args.datasets
    start_date, end_date = date_window(run_date, TRAILING_WINDOW, args.start, args.end)
    if start_date > end_date:
        parser.error("Start date cannot be after the end date.")
    failures = []
    for i, name in enumerate(datasets):
        cfg = DATASETS[name]
        if i > 0:
            sleep(RATE_LIMIT)
        logger.info(
            "Fetching data from %s %s - %s on %s", name, start_date, end_date, run_date
        )
        try:
            t0 = perf_counter()
            target = file_path(SOURCE_NAME, run_date, start_date, end_date, name)
            sql_query = build_query(
                cfg["resource_id"], cfg["datecol"], start_date, end_date
            )
            params = {"sql": sql_query}
            r = fetch(SOURCE_URL, params=params)
            expected_count = expected_records(start_date, end_date, cfg["date_tz"])
            count = validate(r)
            if count != expected_count:
                logger.warning(
                    "Expected %s records but fetched %s. From %s, %s - %s",
                    expected_count,
                    count,
                    name,
                    start_date,
                    end_date,
                )
            write(r, target)
            t_end = perf_counter()
            elapsed = t_end - t0
            logger.info(
                "Successfully fetched and wrote %s %s records from %s - %s in %.2fs",
                count,
                name,
                start_date,
                end_date,
                elapsed,
            )
        except Exception:
            logger.exception(
                "Ingestion failed for %s in range %s - %s", name, start_date, end_date
            )
            failures.append(name)
    if failures:
        logger.error("The following datasets failed: %s", failures)
        return 1
    return 0


if __name__ == "__main__":
    logging.Formatter.converter = gmtime
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    code = main()
    sys.exit(code)
