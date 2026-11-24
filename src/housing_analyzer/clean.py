"""Turn Zillow's wide CSVs and FRED's weekly series into tidy, monthly, analysis-ready tables."""

from __future__ import annotations

import re

import pandas as pd

ID_COLUMNS = ["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"]
DATE_COLUMN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def tidy_zillow(raw: pd.DataFrame, value_name: str) -> pd.DataFrame:
    """Reshape a Zillow wide table (one column per month) into long format.

    Returns columns: region_id, region, state, size_rank, date, <value_name>.
    Only metro areas are kept (the national "country" row is dropped).
    """
    date_cols = [c for c in raw.columns if DATE_COLUMN.match(str(c))]
    if not date_cols:
        raise ValueError("No monthly date columns found; is this a Zillow wide CSV?")

    missing = [c for c in ID_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Missing expected Zillow columns: {missing}")

    df = raw[raw["RegionType"].str.lower() == "msa"]
    long = df.melt(id_vars=ID_COLUMNS, value_vars=date_cols, var_name="date", value_name=value_name)
    long = long.dropna(subset=[value_name])
    long["date"] = pd.to_datetime(long["date"]).dt.to_period("M").dt.to_timestamp()

    long = long.rename(
        columns={
            "RegionID": "region_id",
            "RegionName": "region",
            "StateName": "state",
            "SizeRank": "size_rank",
        }
    ).drop(columns="RegionType")
    return long.sort_values(["region_id", "date"]).reset_index(drop=True)


def tidy_mortgage_rates(raw: pd.DataFrame) -> pd.DataFrame:
    """Convert the weekly 30-year rate to a monthly average, as a decimal (6.5% -> 0.065).

    Accepts Freddie Mac's PMMS export (``date``, ``pmms30``) or FRED's MORTGAGE30US export
    (``observation_date`` or ``DATE``, ``MORTGAGE30US``).
    """
    if "pmms30" in raw.columns:
        df = raw.rename(columns={"pmms30": "rate_pct"})[["date", "rate_pct"]]
        df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    else:
        date_col = "observation_date" if "observation_date" in raw.columns else "DATE"
        df = raw.rename(columns={date_col: "date", "MORTGAGE30US": "rate_pct"})
        df["date"] = pd.to_datetime(df["date"])
    # FRED uses "." for missing values in some exports.
    df["rate_pct"] = pd.to_numeric(df["rate_pct"], errors="coerce")
    df = df.dropna(subset=["rate_pct"])

    monthly = (
        df.set_index("date")["rate_pct"]
        .resample("MS")
        .mean()
        .div(100)
        .rename("mortgage_rate")
        .reset_index()
    )
    return monthly


def build_market_table(
    home_values: pd.DataFrame, rents: pd.DataFrame, rates: pd.DataFrame
) -> pd.DataFrame:
    """Join tidy home values, rents, and mortgage rates into one monthly table per metro.

    Home values drive the table (left join): rents start later (2015) and may be missing.
    """
    rent_cols = rents[["region_id", "date", "rent"]]
    merged = home_values.merge(rent_cols, on=["region_id", "date"], how="left")
    merged = merged.merge(rates, on="date", how="left")
    return merged.sort_values(["region_id", "date"]).reset_index(drop=True)
