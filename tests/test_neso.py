import datetime
from pathlib import Path

import pytest
import requests
import responses
from tenacity import wait_none

from uk_energy_mix.ingest import neso
from uk_energy_mix.exceptions import PayloadValidationError

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
        ("not json at all", PayloadValidationError),
        ("[]", PayloadValidationError),
        ('{"help": "https://example"}', PayloadValidationError),
        ('{"success": false}', PayloadValidationError),
        ('{"success": true}', PayloadValidationError),
        ('{"success": true, "result": {}}', PayloadValidationError),
        ('{"success": true, "result": {"records": "oops"}}', PayloadValidationError),
    ],
)
def test_validation_raises(test_input, expected):
    with pytest.raises(expected):
        neso.validate(test_input)


def test_validate_CKAN_error():
    with pytest.raises(PayloadValidationError, match="does not exist"):
        neso.validate(PAYLOAD_409)



