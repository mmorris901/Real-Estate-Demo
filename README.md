# U.S. Housing Market Analyzer

A Python data pipeline and interactive dashboard that tracks home prices, rents, and
affordability across U.S. metro areas, using public data from **Zillow** and the
**Freddie Mac**.

<!-- Add a screenshot of the dashboard here: ![Dashboard](docs/dashboard.png) -->

## What it does

- **Downloads** Zillow's Home Value Index (ZHVI), Observed Rent Index (ZORI), and Freddie Mac's
  weekly 30-year mortgage rate, caching files locally.
- **Cleans and reshapes** Zillow's wide format (one column per month, 300+ columns) into a tidy
  long table, and resamples weekly mortgage rates into monthly averages.
- **Computes metrics** for ~900 metros, month by month:
  - Year-over-year and multi-year price growth (incl. CAGR)
  - Price-to-rent ratio (home value ÷ annual rent)
  - Estimated monthly mortgage payment (20% down, 30-year fixed)
- **Visualizes** results in a Streamlit dashboard with Plotly charts: metro comparisons,
  growth rankings, buy-vs-rent cost trends, and a downloadable data table.

## Tech stack

Python 3.10+ · pandas · NumPy · Plotly · Streamlit · requests · pytest · ruff · GitHub Actions

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

housing-analyzer build      # download + process the data (~1 minute)
housing-analyzer summary    # print top/bottom metros in the terminal
streamlit run app.py        # open the interactive dashboard
```

Run the tests:

```bash
pytest -v
```

## Project structure

```
src/housing_analyzer/
  config.py     # data source URLs, paths, mortgage assumptions
  fetch.py      # cached downloads with atomic writes
  clean.py      # wide -> long reshaping, rate resampling, joins
  analysis.py   # growth, CAGR, price-to-rent, mortgage payments, rankings
  charts.py     # Plotly figure builders
  pipeline.py   # end-to-end build -> data/processed/market_monthly.csv
  cli.py        # `housing-analyzer build | summary`
app.py          # Streamlit dashboard
tests/          # pytest suite using synthetic fixtures (no network needed)
```

## Methodology notes

- **Home values** use ZHVI for all homes (single-family + condo), mid-tier, smoothed and
  seasonally adjusted. **Rents** use ZORI (all homes, smoothed); rent data begins in 2015.
- **Monthly payment** covers principal and interest only. It excludes property tax, insurance,
  and HOA fees, so true ownership costs are higher.
- **Price-to-rent** above ~20 generally suggests renting is cheaper than buying in that market.

## Data sources

- Zillow Research: <https://www.zillow.com/research/data/>
- Freddie Mac Primary Mortgage Market Survey (30-year fixed rate, weekly since 1971):
  <https://www.freddiemac.com/pmms>
