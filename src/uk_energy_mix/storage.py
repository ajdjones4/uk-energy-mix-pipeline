from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def write(data: str, filepath: Path) -> None:
    """Create parent directory if necessary and write text to file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(data)
    logger.info("Written %s chars to %s", len(data), filepath)