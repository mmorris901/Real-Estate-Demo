"""Metrics: price growth, price-to-rent ratios, and mortgage-based affordability."""

from __future__ import annotations

import numpy as np
import pandas as pd

from housing_analyzer.config import DOWN_PAYMENT_PCT, LOAN_TERM_YEARS


def monthly_payment(
    price: pd.Series | float,
    annual_rate: pd.Series | float,
    down_payment_pct: float = DOWN_PAYMENT_PCT,
    years: int = LOAN_TERM_YEARS,
) -> pd.Series | float:
    """Principal + interest payment on a fixed-rate mortgage (standard amortization formula)."""
    principal = np.asarray(price, dtype=float) * (1 - down_payment_pct)
    r = np.asarray(annual_rate, dtype=float) / 12
    n = years * 12
    with np.errstate(divide="ignore", invalid="ignore"):
        payment = np.where(r == 0, principal / n, principal * r / (1 - (1 + r) ** -n))
    if isinstance(price, pd.Series):
        return pd.Series(payment, index=price.index, name="monthly_payment")
    return float(payment)


def add_metrics(market: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns to the monthly market table.

    - yoy_change: home value % change vs. the same month last year
    - price_to_rent: home value / annual rent (higher = renting is relatively cheaper)
    - monthly_payment: estimated P&I payment at that month's 30-year rate
    """
    df = market.sort_values(["region_id", "date"]).copy()
    by_region = df.groupby("region_id")["home_value"]
    df["yoy_change"] = by_region.pct_change(periods=12, fill_method=None)
    df["price_to_rent"] = df["home_value"] / (df["rent"] * 12)
    df["monthly_payment"] = monthly_payment(df["home_value"], df["mortgage_rate"])
    return df


def cagr(start_value: float, end_value: float, years: float) -> float:
    """Compound annual growth rate."""
    if start_value <= 0 or years <= 0:
        return float("nan")
    return (end_value / start_value) ** (1 / years) - 1


def latest_snapshot(df: pd.DataFrame, years_back: int = 5, top_n: int | None = 100) -> pd.DataFrame:
    """One row per metro at the latest month, with growth over ``years_back`` years.

    ``top_n`` limits to the largest metros by Zillow's SizeRank (0 = U.S., 1 = biggest metro).
    """
    latest_date = df["date"].max()
    past_date = latest_date - pd.DateOffset(years=years_back)

    now = df[df["date"] == latest_date].set_index("region_id")
    then = df[df["date"] == past_date].set_index("region_id")["home_value"]

    snap = now[
        ["region", "state", "size_rank", "home_value", "rent", "yoy_change",
         "price_to_rent", "monthly_payment", "mortgage_rate"]
    ].copy()
    snap[f"growth_{years_back}y"] = snap["home_value"] / then - 1
    snap[f"cagr_{years_back}y"] = [
        cagr(then.get(rid, np.nan), val, years_back) for rid, val in snap["home_value"].items()
    ]

    if top_n is not None:
        snap = snap.nsmallest(top_n, "size_rank")
    return snap.reset_index().sort_values("size_rank").reset_index(drop=True)


def rank(snapshot: pd.DataFrame, column: str, n: int = 10, ascending: bool = False) -> pd.DataFrame:
    """Top (or bottom) ``n`` metros by ``column``, ignoring missing values."""
    return (
        snapshot.dropna(subset=[column])
        .sort_values(column, ascending=ascending)
        .head(n)
        .reset_index(drop=True)
    )


def national_trend(df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """Median home value, rent, and payment across the largest metros, by month."""
    big = df[df["size_rank"] <= top_n]
    return (
        big.groupby("date")
        .agg(
            median_home_value=("home_value", "median"),
            median_rent=("rent", "median"),
            median_payment=("monthly_payment", "median"),
            mortgage_rate=("mortgage_rate", "first"),
        )
        .reset_index()
    )
