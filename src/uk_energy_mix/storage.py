import datetime
import logging
from pathlib import Path

from uk_energy_mix.config import ROOT_DIR

logger = logging.getLogger(__name__)

def write(data: str, file_path: Path) -> None:
    """Create parent directory if necessary and write text to file"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(data)
    logger.info("Written %s chars to %s", len(data), file_path)

def file_path(
    source_name: str,    
    snapshot_date: datetime.date,
    start_date: datetime.date,
    end_date: datetime.date,
    dataset: str,
) -> Path:
    """Generate the file path for storing the payload"""
    filepath = (
        ROOT_DIR
        / "data"
        / "raw"
        / source_name
        / dataset
        / f"ingest_date={snapshot_date}"
        / f"{start_date}_{end_date}.json"
    )
    return filepath