# uk-energy-mix-pipeline

UK Energy Mix Pipeline Portfolio Project. A project building an end-to-end data pipeline ingesting open source UK energy generation, cost, carbon intensity and weather data. Ingested with python, transformed in DuckDB and presented in PowerBI.

## Status

### Done

First Ingestion script (carbon intensity) written in Python with associated tests to fetch JSON data from the NESO Carbon Intensity API. Uses requests to fetch data, retries with tenacity, argparse for CLI interfacing, logging. A bash backfill script to fetch historic data.

### Next

Elexon API
NESO API
DuckDB Transformations
...?
## Data Sources

| Source | Endpoint | Grain | Refresh cadence | Licence |
|NESO Carbon Intensity|api.carbonintensity.org.uk|half hourly|TBD|"Carbon Intensity API" by NESO is licensed under CC BY 4.0|
|  |  |  |  |  |

## Design Notes

### Time and clock changes

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) - handles Python version and dependencies
- Git

Python 3.13 is pinned in `.python-version`; uv will install it if you don't have it.

### Setup

Clone and install:

```bash
git clone https://github.com/ajdjones4/uk-energy-mix-pipeline.git
cd uk-energy-mix-pipeline
uv sync
```

Verify the installation:

```bash
uv run python -c "import uk_energy_mix; print('ok')"
uv run pytest
```

## Usage

Ingest a single day (defaults to today):

```bash
uv run python -m uk_energy_mix.ingest.carbon_intensity 2026-10-25
```

Backfill a date range (end date exclusive, defaults to today):

```bash
./scripts/backfill.sh 2026-10-01 2026-11-01 2>&1 | tee logs/backfill_$(date -I).log
```

Raw responses land in `data/raw/<source>/<date>.json`. Re-running a date overwrites its file, so backfills are idempotent.

## Development

```bash
uv run ruff check . && uv run ruff format .
uv run pytest
```