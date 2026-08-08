from uk_energy_mix.ingest.config import ROOT_DIR
from pathlib import Path
import requests
import datetime

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/intensity/date"


def file_path(dt: datetime.date) -> Path:
    """Generate the file path based on the data source and given date"""
    filepath = ROOT_DIR / "data" / "raw" / SOURCE_NAME / f"{dt}.json"
    return filepath


def fetch(source: str, dt: datetime.date, headers: dict | None = None) -> str:
    """Make the API call, return the json as raw text"""
    response = requests.get(f"{source}/{dt}", headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def write(data: str, filepath: Path) -> None:
    """Create parent directory if necessary and write text to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(data)

if __name__ == "__main__":
    date = "2026-08-07"
    header = {
        'Accept': 'application/json'
    }
    write(fetch(SOURCE_URL, date, header), file_path(date))