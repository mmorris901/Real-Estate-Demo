"""End-to-end pipeline: download -> clean -> merge -> metrics -> processed CSVs."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from housing_analyzer import analysis, clean, fetch
from housing_analyzer.config import PROCESSED_DIR

log = logging.getLogger(__name__)

MARKET_FILE = "market_monthly.csv"


def run(force_download: bool = False, out_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Build the processed monthly market table and save it to ``out_dir``."""
    paths = fetch.fetch_all(force=force_download)

    home_values = clean.tidy_zillow(pd.read_csv(paths["home_values"]), "home_value")
    rents = clean.tidy_zillow(pd.read_csv(paths["rents"]), "rent")
    rates = clean.tidy_mortgage_rates(pd.read_csv(paths["mortgage_rates"]))
    log.info("Home values: %d rows, rents: %d rows, rates: %d months",
             len(home_values), len(rents), len(rates))

    market = analysis.add_metrics(clean.build_market_table(home_values, rents, rates))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / MARKET_FILE
    market.to_csv(out_path, index=False)
    log.info("Wrote %s (%d rows, %d metros)", out_path, len(market), market["region_id"].nunique())
    return market


def load(out_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Load the processed market table, building it first if it doesn't exist yet."""
    path = out_dir / MARKET_FILE
    if not path.exists():
        return run(out_dir=out_dir)
    return pd.read_csv(path, parse_dates=["date"])
