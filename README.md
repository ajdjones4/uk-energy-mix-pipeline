# uk-energy-mix-pipeline
UK Energy Mix Pipeline Portfolio Project

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
uv run python -c "import energy; print('ok')"
uv run pytest
```