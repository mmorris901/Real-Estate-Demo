import pandas as pd
import pytest

from housing_analyzer import clean


def test_tidy_zillow_reshapes_to_long_and_drops_country(raw_home_values):
    tidy = clean.tidy_zillow(raw_home_values, "home_value")

    assert set(tidy.columns) == {"region_id", "region", "state", "size_rank", "date", "home_value"}
    assert "United States" not in tidy["region"].values
    # 24 months for Boomtown + 23 for Flatville (one NaN month dropped)
    assert len(tidy) == 47
    assert tidy["date"].min() == pd.Timestamp("2019-01-01")  # normalized to month start


def test_tidy_zillow_rejects_non_zillow_input():
    with pytest.raises(ValueError, match="date columns"):
        clean.tidy_zillow(pd.DataFrame({"a": [1]}), "home_value")


def test_tidy_mortgage_rates_monthly_decimal(raw_rates):
    rates = clean.tidy_mortgage_rates(raw_rates)

    assert list(rates.columns) == ["date", "mortgage_rate"]
    assert len(rates) == 24
    assert rates["mortgage_rate"].eq(0.06).all()


def test_tidy_mortgage_rates_accepts_fred_format():
    raw = pd.DataFrame({"observation_date": ["2020-01-02"], "MORTGAGE30US": ["3.7"]})
    rates = clean.tidy_mortgage_rates(raw)
    assert rates["mortgage_rate"].tolist() == [pytest.approx(0.037)]


def test_tidy_mortgage_rates_handles_legacy_header_and_missing():
    raw = pd.DataFrame({"DATE": ["2020-01-02", "2020-01-09"], "MORTGAGE30US": ["3.5", "."]})
    rates = clean.tidy_mortgage_rates(raw)
    assert rates["mortgage_rate"].tolist() == [0.035]


def test_build_market_table_left_joins(raw_home_values, raw_rents, raw_rates):
    hv = clean.tidy_zillow(raw_home_values, "home_value")
    rents = clean.tidy_zillow(raw_rents, "rent")
    market = clean.build_market_table(hv, rents, clean.tidy_mortgage_rates(raw_rates))

    assert len(market) == len(hv)
    assert market[["rent", "mortgage_rate"]].notna().all().all()
