import datetime
from pathlib import Path
from time import sleep

import requests

from uk_energy_mix.ingest.config import ROOT_DIR

SOURCE_NAME = "neso"
SOURCE_URL = "https://api.neso.energy/api/3/action/datastore_search_sql"
DATASETS = {
    "historic-generation-mix": {
        "resource_id": "f93d1835-75bc-43e5-84ad-12472b180a98",
        "datecol": "DATETIME",
    },
    "historic-demand-data": {
        "resource_id": "8a4a771c-3929-4e56-93ad-cdf13219dea5",
        "datecol": "SETTLEMENT_DATE",
    },
    "demand-data-update": {
        "resource_id": "177f6fa4-ae49-4182-81ea-0c6b35f26ca6",
        "datecol": "SETTLEMENT_DATE",
    },
}


def file_path(
    snapshot_date: datetime.date, data_date: datetime.date, dataset: str
) -> Path:
    """Generate the file path based on the data source and snapshot date"""
    filepath = (
        ROOT_DIR
        / "data"
        / "raw"
        / SOURCE_NAME
        / f"{dataset}"
        / f"{data_date}"
        / f"{snapshot_date}.json"
    )
    return filepath


def build_query(resource_id: str, date_col: str, dt: datetime.date) -> str:
    """Build the SQL query to retrieve desired data from CKAN API"""
    dateafter = dt + datetime.timedelta(days=1)
    sql_query = (f'''SELECT * FROM "{resource_id}" ''' 
                 f'''WHERE "{date_col}" >= '{dt}' ''' 
                 f'''AND "{date_col}" < '{dateafter}' ''')
    return sql_query

def fetch(source: str, headers: dict | None = None, params: dict | None = None) -> str:
    """Make the API call, return the json as raw text"""
    response = requests.get(source, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.text


def write(data: str, filepath: Path) -> None:
    """Create parent directory if necessary and write text to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(data)


data_date = datetime.date(2026, 10, 25)

if __name__ == "__main__":
    for name, cfg in DATASETS.items():
        snapshot_date = datetime.datetime.now(datetime.UTC)
        path = file_path(snapshot_date, data_date, name)
        sql_query = build_query(cfg["resource_id"], cfg["datecol"], data_date)
        params = {"sql": sql_query}
        r = fetch(SOURCE_URL, params=params)
        write(r, path)
        sleep(30)
