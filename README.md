# uk-energy-mix-pipeline

UK Energy Mix Pipeline Portfolio Project. A project building an end-to-end data pipeline ingesting open source UK energy generation, cost, carbon intensity and weather data. Ingested with Python, transformed in DuckDB and presented in Power BI.

## Status

### Done

First ingestion script (carbon intensity) written in Python with associated tests to fetch JSON data from the NESO Carbon Intensity API. Uses requests to fetch data, retries with tenacity, a validation gate that checks each payload before it is written, argparse for the CLI, and logging. A bash backfill script fetches historic data.

### Next

- Elexon API
- NESO Data Portal API
- DuckDB transformations

## Data Sources

| Source | Endpoint | Grain | Refresh cadence | Licence |
|---|---|---|---|---|
| NESO Carbon Intensity | `api.carbonintensity.org.uk/intensity/date/{date}` | Half-hourly | TBD | "Carbon Intensity API" by NESO, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

## Design Notes

### Time and clock changes

<!-- 46/48/50 periods, UTC storage, 25 Oct 2026 evidence -->

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

## Acknowledgements

This project was built as an example learning project with the help of [Claude](https://claude.ai) (Anthropic). Claude was used to help debug code, provide targetted learning resources and advise on a roadmap and next-steps. All design decisions and implementations are my own.