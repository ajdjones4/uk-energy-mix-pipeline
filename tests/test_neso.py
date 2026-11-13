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
GOOD_PAYLOAD = (FIXTURES / "generation_mix_2026-10-25.json").read_text(encoding="utf-8")
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
    responses.add(responses.GET, SOURCE, body=GOOD_PAYLOAD, status=200)
    assert neso.fetch(SOURCE) == GOOD_PAYLOAD
    assert len(responses.calls) == 1

@responses.activate
def test_429_retries_200():
    responses.add(responses.GET, SOURCE, status=429)
    responses.add(responses.GET, SOURCE, body=GOOD_PAYLOAD, status=200)
    assert neso.fetch(SOURCE) == GOOD_PAYLOAD
    assert len(responses.calls) == 2