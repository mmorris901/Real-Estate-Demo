"""Small synthetic fixtures shaped like the real Zillow and FRED files."""

import pandas as pd
import pytest


def _zillow_wide(
    values_by_region: dict[str, list[float]], start: str = "2019-01-31"
) -> pd.DataFrame:
    dates = pd.date_range(start, periods=len(next(iter(values_by_region.values()))), freq="ME")
    rows = [
        {"RegionID": 102001, "SizeRank": 0, "RegionName": "United States",
         "RegionType": "country", "StateName": None,
         **{d.strftime("%Y-%m-%d"): 1.0 for d in dates}},
    ]
    for i, (name, values) in enumerate(values_by_region.items(), start=1):
        city, state = name.split(", ")
        rows.append({
            "RegionID": 1000 + i, "SizeRank": i, "RegionName": name,
            "RegionType": "msa", "StateName": state,
            **{d.strftime("%Y-%m-%d"): v for d, v in zip(dates, values, strict=True)},
        })
    return pd.DataFrame(rows)


@pytest.fixture
def raw_home_values() -> pd.DataFrame:
    # 24 months: Boomtown doubles steadily, Flatville stays flat (with one missing month).
    boom = [100_000 * 2 ** (m / 23) for m in range(24)]
    flat = [200_000.0] * 24
    flat[5] = float("nan")
    return _zillow_wide({"Boomtown, TX": boom, "Flatville, OH": flat})


@pytest.fixture
def raw_rents() -> pd.DataFrame:
    return _zillow_wide({"Boomtown, TX": [1_000.0] * 24, "Flatville, OH": [2_000.0] * 24})


@pytest.fixture
def raw_rates() -> pd.DataFrame:
    weeks = pd.date_range("2019-01-03", "2020-12-31", freq="W-THU")
    # Freddie Mac PMMS layout: M/D/YYYY dates, rate in percent.
    return pd.DataFrame({"date": [f"{d.month}/{d.day}/{d.year}" for d in weeks],
                         "pmms30": [6.0] * len(weeks),
                         "pmms15": [5.5] * len(weeks)})
