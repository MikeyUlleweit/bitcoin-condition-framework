# Bitcoin Condition Framework

A research-driven system for classifying Bitcoin's current market environment from real, explainable observations. It is designed to become a trustworthy upstream input to future strategy research; it is not a trading bot or recommendation engine.

## Current capabilities

- Collects real public blockspace data from mempool.space.
- Scores global stablecoin-supply trend from DeFiLlama.
- Scores BTC regime and fixed-universe ETH/SOL rotation from Coinbase candles.
- Scores miner economics from mempool.space hashrate, difficulty, and rewards.
- Scores single-venue leverage risk from Kraken Futures analytics.
- Scores MVRV and active-address context from Coin Metrics Community.
- Preserves provider failures without aborting the complete research run.
- Validates units, source, timing provenance, missing data, and partial coverage.
- Produces standardized category signals with explicit scoring contributions.
- Records point-in-time snapshots with an information cutoff and input lineage.
- Persists snapshots, observations, signals, score contributions, failures, and condition results in SQLite.
- Replays stored signals through the current condition engine.
- Provides a database-backed Streamlit research dashboard.

All six required categories now have transparent provisional public-data scores. Paid or
credentialed metrics are never fabricated: narrower free-data scope, missing components,
coverage, and provisional calibration are shown with each signal.

## Run locally

Create a local virtual environment and install the project:

```bash
python3.12 -m venv venv
venv/bin/python -m pip install -e '.[dev]'
```

Run a live research cycle:

```bash
venv/bin/python -m scripts.run_live_report
```

This performs one live collection run and writes `data/research.sqlite3`.

Start the dashboard:

```bash
venv/bin/python -m streamlit run app.py
```

Then open the local URL printed by Streamlit, normally `http://localhost:8501`.

To use another database path:

```bash
BITCOIN_RESEARCH_DB=/absolute/path/research.sqlite3 \
  venv/bin/python -m streamlit run app.py
```

The dashboard's **Refresh real data** button runs the same production ingestion and persistence pipeline.

## Database

SQLite schema version 1 contains:

| Table | Purpose |
| --- | --- |
| `snapshots` | Canonical versioned snapshot JSON and condition result |
| `observations` | Typed provider observations and timing provenance |
| `signals` | Standardized category outputs and status |
| `score_contributions` | Raw values, normalization, weights, and weighted points |
| `provider_failures` | Provider-specific failure records retained per snapshot |

The canonical JSON stored in `snapshots` supports exact typed reconstruction. Normalized tables support dashboard and research queries.

## Quality checks

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -q
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m ruff check .
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m mypy src
```

Tests requiring live provider access are marked `live` and excluded from the deterministic default suite. Run them explicitly with:

```bash
venv/bin/python -m pytest -m live -o addopts=''
```

## Research limitations

- All weights, normalizations, and condition thresholds are transparent but not yet
  empirically calibrated or backtested.
- Global stablecoin supply does not substitute for ETF flows or institutional market depth.
- Kraken PF_XBTUSD is a single-venue leverage proxy.
- Coinbase BTC/ETH/SOL is a deliberately fixed but narrow rotation universe.
- Coin Metrics Community metrics do not provide holder-cohort realized-cap analysis.
- The condition engine refuses classification whenever fewer than four real categories
  are usable; provider failures remain explicit and are never interpreted as zero.
- No historical regime model has yet been validated for stability, predictive value, or trading utility.
- Accumulating point-in-time history, calibrating thresholds, and evaluating predictive
  stability are prerequisites before using these outputs in algorithm research.

See [CONTEXT.md](./CONTEXT.md) for domain language and [docs/research/provider-raw-data-contracts.md](./docs/research/provider-raw-data-contracts.md) for provider-contract research.
