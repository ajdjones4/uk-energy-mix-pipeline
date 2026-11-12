import datetime
from pathlib import Path

import pytest

from uk_energy_mix.ingest import neso

snapshot_date = datetime.date.fromisoformat("2026-11-12")
data_date = datetime.date.fromisoformat("2026-10-25")
dataset_name = "historic-generation-data"
resource_id = "f93d1835-75bc-43e5-84ad-12472b180a98"
date_col = "DATETIME"
query_gen = '''SELECT * FROM "f93d1835-75bc-43e5-84ad-12472b180a98" WHERE "DATETIME" >= '2026-10-25' AND "DATETIME" < '2026-10-26' '''
query_demand = '''SELECT * FROM "8a4a771c-3929-4e56-93ad-cdf13219dea5" WHERE "SETTLEMENT_DATE" >= '2026-10-25' AND "SETTLEMENT_DATE" < '2026-10-26' '''
query_update = '''SELECT * FROM "177f6fa4-ae49-4182-81ea-0c6b35f26ca6" WHERE "SETTLEMENT_DATE" >= '2026-10-25' AND "SETTLEMENT_DATE" < '2026-10-26' '''
            

def test_file_path():
    path = neso.file_path(snapshot_date, data_date, dataset_name)
    assert path.parts[-3:] == ("historic-generation-data", "2026-10-25", "2026-11-12.json")

@pytest.mark.parametrize(
        ("resource_id", "date_col", "expected"),
        [
            ("f93d1835-75bc-43e5-84ad-12472b180a98", "DATETIME", query_gen),
            ("8a4a771c-3929-4e56-93ad-cdf13219dea5", "SETTLEMENT_DATE", query_demand),
            ("177f6fa4-ae49-4182-81ea-0c6b35f26ca6", "SETTLEMENT_DATE", query_update)
        ], ids=["generation_mix", "demand", "update"]
)
def test_build_query(resource_id, date_col, expected):
    assert neso.build_query(resource_id, date_col, data_date) == expected