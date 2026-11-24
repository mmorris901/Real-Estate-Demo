"""Plotly figure builders shared by the dashboard and the static HTML report."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

TEMPLATE = "plotly_white"


def price_history(
    df: pd.DataFrame, regions: list[str], title: str = "Home values over time"
) -> go.Figure:
    """Home value over time for the selected metros."""
    data = df[df["region"].isin(regions)]
    fig = px.line(
        data, x="date", y="home_value", color="region",
        labels={"home_value": "Typical home value ($)", "date": "", "region": "Metro"},
        template=TEMPLATE,
    )
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(title=title, hovermode="x unified")
    return fig


def growth_bar(ranked: pd.DataFrame, column: str, title: str) -> go.Figure:
    """Horizontal bar chart of a percentage metric, keeping rank #1 at the top."""
    data = ranked.iloc[::-1]  # Plotly draws horizontal bars bottom-up.
    fig = px.bar(
        data, x=column, y="region", orientation="h",
        labels={column: "", "region": ""}, template=TEMPLATE, text_auto=".1%",
    )
    fig.update_xaxes(tickformat=".0%")
    fig.update_layout(title=title, height=40 * len(data) + 120)
    return fig


def affordability_trend(trend: pd.DataFrame, period: str = "all years") -> go.Figure:
    """Median monthly payment vs. median rent, with the mortgage rate on a second axis."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=trend["date"], y=trend["median_payment"],
                             name="Median mortgage payment"), secondary_y=False)
    fig.add_trace(go.Scatter(x=trend["date"], y=trend["median_rent"],
                             name="Median rent"), secondary_y=False)
    fig.add_trace(go.Scatter(x=trend["date"], y=trend["mortgage_rate"], name="30-yr rate",
                             line={"dash": "dot"}), secondary_y=True)
    fig.update_yaxes(title_text="Monthly cost ($)", tickprefix="$", tickformat=",.0f",
                     secondary_y=False)
    fig.update_yaxes(title_text="Mortgage rate", tickformat=".1%", secondary_y=True)
    fig.update_layout(title=f"Buying vs. renting: median monthly cost, {period}",
                      template=TEMPLATE, hovermode="x unified")
    return fig


def price_vs_rent_scatter(snapshot: pd.DataFrame) -> go.Figure:
    """Each metro's home value vs. annual rent; dot size shows market size."""
    data = snapshot.dropna(subset=["rent"]).assign(
        annual_rent=lambda d: d["rent"] * 12,
        market_size=lambda d: 1 / d["size_rank"].clip(lower=1),
    )
    fig = px.scatter(
        data, x="annual_rent", y="home_value", size="market_size", color="price_to_rent",
        hover_name="region", color_continuous_scale="Viridis", template=TEMPLATE,
        labels={"annual_rent": "Annual rent ($)", "home_value": "Home value ($)",
                "price_to_rent": "Price-to-rent"},
        hover_data={"market_size": False, "price_to_rent": ":.1f"},
    )
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(title="Home value vs. rent by metro")
    return fig
