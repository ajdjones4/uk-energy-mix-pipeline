import datetime
from pathlib import Path

import pytest
import requests
import responses

from uk_energy_mix.ingest import carbon_intensity

CONTENT = "Hello World"
dt = datetime.date.fromisoformat("2026-08-07")
source = carbon_intensity.SOURCE_URL
fpath = Path(__file__).parent / "fixtures" / "intensity_day.json"
fixture = fpath.read_text(encoding="utf-8")


def test_path():
    assert str(carbon_intensity.file_path(dt)).endswith(
        "data/raw/carbon_intensity/2026-08-07.json"
    )


def test_write_creates_missing_parent_directories(tmp_path):
    d = tmp_path / "one" / "two" / "three" / "four.json"
    carbon_intensity.write(CONTENT, d)
    assert d.read_text(encoding="utf-8") == CONTENT


def test_write_idempotency(tmp_path):
    d = tmp_path / "test.json"
    carbon_intensity.write(CONTENT, d)
    carbon_intensity.write("overwrite", d)
    assert d.read_text(encoding="utf-8") == "overwrite"
    assert len(list(d.parent.iterdir())) == 1


@responses.activate
def test_fetch_returns_body():
    responses.add(responses.GET, f"{source}/{dt}", body=fixture, status=200)
    assert carbon_intensity.fetch(source, dt) == fixture


@responses.activate
def test_fetch_constructs_correct_url():
    responses.add(responses.GET, f"{source}/{dt}", body=fixture, status=200)
    carbon_intensity.fetch(source, dt)
    assert (
        responses.calls[0].request.url
        == "https://api.carbonintensity.org.uk/intensity/date/2026-08-07"
    )


@responses.activate
def test_fetch_raises_on_404():
    responses.add(responses.GET, f"{source}/{dt}", status=404)
    with pytest.raises(requests.HTTPError):
        carbon_intensity.fetch(source, dt)


@responses.activate
def test_fetch_timeout():
    responses.add(responses.GET, f"{source}/{dt}", body=requests.Timeout())
    with pytest.raises(requests.Timeout):
        carbon_intensity.fetch(source, dt)
