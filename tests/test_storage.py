from uk_energy_mix import storage

CONTENT = "Hello World"

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