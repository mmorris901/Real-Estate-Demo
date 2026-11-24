import math

import pandas as pd
import pytest

from housing_analyzer import analysis, clean


@pytest.fixture
def market(raw_home_values, raw_rents, raw_rates):
    hv = clean.tidy_zillow(raw_home_values, "home_value")
    rents = clean.tidy_zillow(raw_rents, "rent")
    rates = clean.tidy_mortgage_rates(raw_rates)
    return analysis.add_metrics(clean.build_market_table(hv, rents, rates))


def test_monthly_payment_matches_known_value():
    # $400k home, 20% down -> $320k loan at 6% for 30 years = $1,918.56/month
    assert analysis.monthly_payment(400_000, 0.06) == pytest.approx(1918.56, abs=0.01)


def test_monthly_payment_zero_rate():
    assert analysis.monthly_payment(360_000, 0.0) == pytest.approx(288_000 / 360)


def test_monthly_payment_series_keeps_index():
    prices = pd.Series([400_000, 200_000], index=[10, 20])
    result = analysis.monthly_payment(prices, pd.Series([0.06, 0.06], index=[10, 20]))
    assert list(result.index) == [10, 20]
    assert result[20] == pytest.approx(result[10] / 2)


def test_cagr():
    assert analysis.cagr(100, 200, 1) == pytest.approx(1.0)
    assert analysis.cagr(100, 121, 2) == pytest.approx(0.10)
    assert math.isnan(analysis.cagr(0, 100, 5))


def test_add_metrics(market):
    boom = market[market["region"] == "Boomtown, TX"].set_index("date")
    assert boom["yoy_change"].iloc[:12].isna().all()  # no prior year yet
    # Doubling over 23 months -> 12-month growth of 2**(12/23) - 1
    assert boom["yoy_change"].iloc[-1] == pytest.approx(2 ** (12 / 23) - 1)

    flat = market[market["region"] == "Flatville, OH"]
    assert flat["price_to_rent"].iloc[0] == pytest.approx(200_000 / 24_000)


def test_latest_snapshot_and_rank(market):
    snap = analysis.latest_snapshot(market, years_back=1, top_n=None)
    assert set(snap["region"]) == {"Boomtown, TX", "Flatville, OH"}

    top = analysis.rank(snap, "growth_1y", n=1)
    assert top.loc[0, "region"] == "Boomtown, TX"
    flat = snap.set_index("region").loc["Flatville, OH"]
    assert flat["growth_1y"] == pytest.approx(0.0)


def test_national_trend(market):
    trend = analysis.national_trend(market)
    assert len(trend) == 24
    assert trend["mortgage_rate"].eq(0.06).all()
