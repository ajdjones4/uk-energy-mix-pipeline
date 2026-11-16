import datetime
from pathlib import Path

import pytest
import requests
import responses
from tenacity import wait_none

from uk_energy_mix.ingest import neso

SNAPSHOT_DATE = datetime.date.fromisoformat("2026-11-12")
DATE_FROM = datetime.date.fromisoformat("2026-10-25")
DATE_TO = datetime.date.fromisoformat("2026-10-25")
DATASET_NAME = "historic-generation-data"
RESOURCE_ID = "f93d1835-75bc-43e5-84ad-12472b180a98"
DATE_COL = "DATETIME"
QUERY_GEN = """SELECT * FROM "f93d1835-75bc-43e5-84ad-12472b180a98" WHERE "DATETIME" >= '2026-10-25' AND "DATETIME" < '2026-10-26' """
QUERY_DEMAND = """SELECT * FROM "8a4a771c-3929-4e56-93ad-cdf13219dea5" WHERE "SETTLEMENT_DATE" >= '2026-10-25' AND "SETTLEMENT_DATE" < '2026-10-26' """
QUERY_UPDATE = """SELECT * FROM "177f6fa4-ae49-4182-81ea-0c6b35f26ca6" WHERE "SETTLEMENT_DATE" >= '2026-10-25' AND "SETTLEMENT_DATE" < '2026-10-26' """
SOURCE = "https://api.neso.energy/api/3/action/datastore_search_sql"
FIXTURES = Path(__file__).parent / "fixtures" / "neso"
GOOD_GEN_PAYLOAD = (FIXTURES / "generation_mix_2026-10-25.json").read_text(
    encoding="utf-8"
)
GOOD_DEMAND_PAYLOAD = (FIXTURES / "demand_update_2026-10-25.json").read_text(
    encoding="utf-8"
)
EMPTY_DEMAND_PAYLOAD = (FIXTURES / "empty_historic_demand_2026-10-25.json").read_text(
    encoding="utf-8"
)
PAYLOAD_409 = (FIXTURES / "409_demand_update_2026-10-25.json").read_text(
    encoding="utf-8"
)
LONDON = "Europe/London"
UTC = "UTC"
WINDOW = 10
neso.fetch.retry.wait = wait_none()


def test_file_path():
    path = neso.file_path(SNAPSHOT_DATE, DATE_FROM, DATE_TO, DATASET_NAME)
    assert path.parts[-3:] == (
        "historic-generation-data",
        "ingest_date=2026-11-12",
        "2026-10-25_2026-10-25.json",
    )


@pytest.mark.parametrize(
    ("resource_id", "date_col", "expected"),
    [
        ("f93d1835-75bc-43e5-84ad-12472b180a98", "DATETIME", QUERY_GEN),
        ("8a4a771c-3929-4e56-93ad-cdf13219dea5", "SETTLEMENT_DATE", QUERY_DEMAND),
        ("177f6fa4-ae49-4182-81ea-0c6b35f26ca6", "SETTLEMENT_DATE", QUERY_UPDATE),
    ],
    ids=["generation_mix", "demand", "update"],
)
def test_build_query(resource_id, date_col, expected):
    assert neso.build_query(resource_id, date_col, DATE_FROM, DATE_TO) == expected


@responses.activate
def test_fetch_raises_on_404():
    responses.add(responses.GET, SOURCE, status=404)
    with pytest.raises(requests.HTTPError):
        neso.fetch(SOURCE)
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_timeout():
    responses.add(responses.GET, SOURCE, body=requests.Timeout())
    with pytest.raises(requests.Timeout):
        neso.fetch(SOURCE)
    assert len(responses.calls) == 3


@responses.activate
def test_fetch_retries_503():
    responses.add(responses.GET, SOURCE, status=503)
    with pytest.raises(requests.HTTPError):
        neso.fetch(SOURCE)
    assert len(responses.calls) == 3


@responses.activate
def test_fetch_409():
    responses.add(responses.GET, SOURCE, status=409)
    with pytest.raises(requests.HTTPError):
        neso.fetch(SOURCE)
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_returns_body():
    responses.add(responses.GET, SOURCE, body=GOOD_GEN_PAYLOAD, status=200)
    assert neso.fetch(SOURCE) == GOOD_GEN_PAYLOAD
    assert len(responses.calls) == 1


@responses.activate
def test_429_retries_200():
    responses.add(responses.GET, SOURCE, status=429)
    responses.add(responses.GET, SOURCE, body=GOOD_GEN_PAYLOAD, status=200)
    assert neso.fetch(SOURCE) == GOOD_GEN_PAYLOAD
    assert len(responses.calls) == 2


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [(GOOD_GEN_PAYLOAD, 48), (GOOD_DEMAND_PAYLOAD, 50), (EMPTY_DEMAND_PAYLOAD, 0)],
)
def test_validation_pass(test_input, expected):
    assert neso.validate(test_input) == expected


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        ("not json at all", ValueError),
        ("[]", TypeError),
        ('{"help": "https://example"}', ValueError),
        ('{"success": false}', ValueError),
        ('{"success": true}', ValueError),
        ('{"success": true, "result": {}}', ValueError),
        ('{"success": true, "result": {"records": "oops"}}', TypeError),
    ],
)
def test_validation_raises(test_input, expected):
    with pytest.raises(expected):
        neso.validate(test_input)


def test_validate_CKAN_error():
    with pytest.raises(ValueError, match="does not exist"):
        neso.validate(PAYLOAD_409)


@pytest.mark.parametrize(
    ("date_from", "date_to", "timezone", "expected"),
    [
        (datetime.date(2026, 10, 25), datetime.date(2026, 10, 25), LONDON, 50),
        (datetime.date(2026, 10, 25), datetime.date(2026, 10, 25), UTC, 48),
        (datetime.date(2026, 3, 23), datetime.date(2026, 3, 30), LONDON, 382),
        (datetime.date(2026, 3, 23), datetime.date(2026, 3, 30), UTC, 384),
    ],
    ids=[
        "london_oct_change",
        "utc_oct_change",
        "london_march_change_range",
        "utc_march_change_range",
    ],
)
def test_expected_records(date_from, date_to, timezone, expected):
    assert neso.expected_records(date_from, date_to, timezone) == expected


@pytest.mark.parametrize(
    ("window", "start_date", "end_date", "expected"),
    [
        (
            10,
            None,
            datetime.date(2026, 11, 10),
            (datetime.date(2026, 11, 1), datetime.date(2026, 11, 10)),
        ),
        (
            10,
            datetime.date(2026, 11, 10),
            None,
            (datetime.date(2026, 11, 10), datetime.date(2026, 11, 11)),
        ),
        (10, None, None, (datetime.date(2026, 11, 2), datetime.date(2026, 11, 11))),
        (
            10,
            datetime.date(2026, 10, 25),
            datetime.date(2026, 10, 30),
            (datetime.date(2026, 10, 25), datetime.date(2026, 10, 30)),
        ),
        (1, None, None, (datetime.date(2026, 11, 11), datetime.date(2026, 11, 11))),
    ],
    ids=["no-start", "no-end", "no-given-dates", "given-both-dates", "window-length-1"],
)
def test_date_window(window, start_date, end_date, expected):
    assert neso.date_window(SNAPSHOT_DATE, window, start_date, end_date) == expected
