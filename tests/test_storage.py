import datetime

from uk_energy_mix import storage

CONTENT = "Hello World"
SNAPSHOT_DATE = datetime.date.fromisoformat("2026-11-12")
DATE_FROM = datetime.date.fromisoformat("2026-10-25")
DATE_TO = datetime.date.fromisoformat("2026-10-25")
SOURCE_NAME = "generic-datasource"
DATASET_NAME = "generic-dataset"

def test_write_creates_missing_parent_directories(tmp_path):
    d = tmp_path / "one" / "two" / "three" / "four.json"
    storage.write(CONTENT, d)
    assert d.read_text(encoding="utf-8") == CONTENT


def test_write_idempotency(tmp_path):
    d = tmp_path / "test.json"
    storage.write(CONTENT, d)
    storage.write("overwrite", d)
    assert d.read_text(encoding="utf-8") == "overwrite"
    assert len(list(d.parent.iterdir())) == 1

def test_file_path():
    path = storage.file_path(SOURCE_NAME, SNAPSHOT_DATE, DATE_FROM, DATE_TO, DATASET_NAME)
    assert path.parts[-4:] == (
        "generic-datasource",
        "generic-dataset",
        "ingest_date=2026-11-12",
        "2026-10-25_2026-10-25.json",
    )