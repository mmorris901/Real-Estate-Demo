"""Central configuration: data sources, file paths, and analysis assumptions."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Public datasets. Zillow publishes these at https://www.zillow.com/research/data/
# Mortgage rates come straight from Freddie Mac's Primary Mortgage Market Survey (the same
# series FRED mirrors as MORTGAGE30US): https://www.freddiemac.com/pmms
SOURCES = {
    "home_values": (
        "https://files.zillowstatic.com/research/public_csvs/zhvi/"
        "Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
    ),
    "rents": (
        "https://files.zillowstatic.com/research/public_csvs/zori/"
        "Metro_zori_uc_sfrcondomfr_sm_month.csv"
    ),
    "mortgage_rates": "https://www.freddiemac.com/pmms/docs/PMMS_history.csv",
}

# Affordability assumptions used for the monthly payment estimate.
DOWN_PAYMENT_PCT = 0.20
LOAN_TERM_YEARS = 30
