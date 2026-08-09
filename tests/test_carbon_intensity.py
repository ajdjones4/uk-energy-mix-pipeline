import pytest
import datetime
from uk_energy_mix.ingest import carbon_intensity
CONTENT = "Hello World"


def test_path():
    date = datetime.date.fromisoformat("2026-08-07")
    assert str(carbon_intensity.file_path(date)).endswith("data/raw/carbon_intensity/2026-08-07.json")

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

#check that...
def test_fetch():
    pass
