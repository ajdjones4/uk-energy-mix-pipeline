import pytest
import datetime
import uk_energy_mix.ingest.carbon_intensity as carbon
from uk_energy_mix.ingest.config import ROOT_DIR
CONTENT = "Hello World"


def test_path():
    date = datetime.date.fromisoformat("2026-08-07")
    assert carbon.file_path(date) == ROOT_DIR / "data" / "raw" / carbon.SOURCE_NAME / "2026-08-07.json"

def test_write(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.txt"
    carbon.write(CONTENT, p)
    assert p.read_text(encoding="utf-8") == CONTENT

#check that...
def test_fetch():
    pass
