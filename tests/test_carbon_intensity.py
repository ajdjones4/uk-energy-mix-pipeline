import datetime
import json
from pathlib import Path

import pytest
import requests
import responses
from tenacity import wait_none

from uk_energy_mix.exceptions import PayloadValidationError
from uk_energy_mix.ingest import carbon_intensity

start_date = datetime.date.fromisoformat("2026-08-07")
end_date = datetime.date.fromisoformat("2026-08-07")
source = carbon_intensity.SOURCE_URL
url = f"{source}/2026-08-07T00:00Z/2026-08-08T00:00Z"
FIXTURES = Path(__file__).parent / "fixtures" / "carbon_intensity"
GOOD_PAYLOAD = (FIXTURES / "range_2026-08-07_2026-08-07.json").read_text(encoding="utf-8")
BAD_PAYLOAD = (FIXTURES / "intensity_day_truncated.json").read_text(encoding="utf-8")
carbon_intensity.fetch.retry.wait = wait_none()

@responses.activate
def test_fetch_returns_body():
    responses.add(responses.GET, url, body=GOOD_PAYLOAD, status=200)
    assert carbon_intensity.fetch(url) == GOOD_PAYLOAD


@responses.activate
def test_fetch_raises_on_404():
    responses.add(responses.GET, url, status=404)
    with pytest.raises(requests.HTTPError):
        carbon_intensity.fetch(url)
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_timeout():
    responses.add(responses.GET, url, body=requests.Timeout())
    with pytest.raises(requests.Timeout):
        carbon_intensity.fetch(url)
    assert len(responses.calls) == 3


@responses.activate
def test_fetch_retries_503():
    responses.add(responses.GET, url, status=503)
    with pytest.raises(requests.HTTPError):
        carbon_intensity.fetch(url)
    assert len(responses.calls) == 3


def test_validation_pass():
    assert carbon_intensity.validate(GOOD_PAYLOAD) == 48


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        (BAD_PAYLOAD, PayloadValidationError),
        ("[]", PayloadValidationError),
        ('{"foo": []}', PayloadValidationError),
        (json.dumps({"data": [{}] * 12}), PayloadValidationError),
    ],
)
def test_validation_raises(test_input, expected):
    with pytest.raises(expected):
        carbon_intensity.validate(test_input)

def test_build_source():
    assert carbon_intensity.build_url(source, 
                                      start_date, 
                                      end_date) == "https://api.carbonintensity.org.uk/intensity/2026-08-07T00:00Z/2026-08-08T00:00Z"