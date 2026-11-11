#We want to now ingest the generation and demand data from the NESO energy portal. Following what I wrote 
#in the Carbon intensity API ingestion script, will need constants, filepath, fetch, write, validate, main.
#Associated tests
#response handling - dont handle 429 in carbon intensity, will want to in this one
#idempotency might need rethinking
import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from time import perf_counter

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential
)

from uk_energy_mix.ingest.config import ROOT_DIR

SOURCE_NAME = "neso"
SOURCE_URL = ""
HEADERS = {}

def file_path(dt: datetime.date) -> Path:
    """Generate the file path based on the data source and given date"""
    filepath = ROOT_DIR / "data" / "raw" / SOURCE_NAME / f"{dt}.json"
    return filepath

