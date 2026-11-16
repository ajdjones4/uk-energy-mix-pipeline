from pathlib import Path
import logging
import datetime

from uk_energy_mix.config import ROOT_DIR

logger = logging.getLogger(__name__)

def write(data: str, filepath: Path) -> None:
    """Create parent directory if necessary and write text to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(data)
    logger.info("Written %s chars to %s", len(data), filepath)

def file_path(
    source_name: str,    
    snapshot_date: datetime.date,
    dt_from: datetime.date,
    dt_to: datetime.date,
    dataset: str,
) -> Path:
    """Generate the file path based on the data source and snapshot date"""
    filepath = (
        ROOT_DIR
        / "data"
        / "raw"
        / source_name
        / dataset
        / f"ingest_date={snapshot_date}"
        / f"{dt_from}_{dt_to}.json"
    )
    return filepath