"""Interactive dashboard. Run with:  streamlit run app.py"""

import pandas as pd
import streamlit as st

from housing_analyzer import analysis, charts, pipeline

st.set_page_config(page_title="Housing Market Analyzer", layout="wide")


@st.cache_data(show_spinner="Loading housing data...")
def load_data() -> pd.DataFrame:
    return pipeline.load()


df = load_data()
latest = df["date"].max()

# --- Sidebar controls -------------------------------------------------------
st.sidebar.header("Settings")
top_n = st.sidebar.slider("Largest N metros", 25, 300, 100, step=25)
years_back = st.sidebar.select_slider(
    "Time period (years)", [1, 3, 5, 10], value=5,
    help="Sets the date range of the trend charts and the period used for growth rankings. "
         "The headline numbers at the top always compare with one year ago.",
)

snap = analysis.latest_snapshot(df, years_back=years_back, top_n=top_n)
growth_col = f"growth_{years_back}y"
window_start = latest - pd.DateOffset(years=years_back)
period = "past year" if years_back == 1 else f"past {years_back} years"

# --- Header + KPIs ----------------------------------------------------------
st.title("U.S. Housing Market Analyzer")
st.caption(
    f"Zillow Home Value Index, Zillow Observed Rent Index, and Freddie Mac 30-year mortgage "
    f"rates (PMMS). Data through {latest:%B %Y}."
)

trend = analysis.national_trend(df, top_n=top_n)
# Use the latest month where every series has data (sources can lag each other by a month).
kpi = trend.dropna().reset_index(drop=True)
now, year_ago = kpi.iloc[-1], kpi.iloc[-13]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Median home value", f"${now.median_home_value:,.0f}",
          f"{now.median_home_value / year_ago.median_home_value - 1:+.1%} YoY")
c2.metric("Median rent", f"${now.median_rent:,.0f}",
          f"{now.median_rent / year_ago.median_rent - 1:+.1%} YoY")
c3.metric("Est. monthly payment", f"${now.median_payment:,.0f}",
          f"{now.median_payment / year_ago.median_payment - 1:+.1%} YoY", delta_color="inverse")
c4.metric("30-yr mortgage rate", f"{now.mortgage_rate:.2%}",
          f"{(now.mortgage_rate - year_ago.mortgage_rate) * 100:+.2f} pts", delta_color="inverse")

# --- Tabs -------------------------------------------------------------------
tab_trends, tab_rank, tab_afford, tab_data = st.tabs(
    ["Price trends", "Rankings", "Affordability", "Data"]
)

with tab_trends:
    default = snap["region"].head(5).tolist()
    regions = st.multiselect("Compare metros", sorted(snap["region"]), default=default)
    if regions:
        recent = df[df["date"] >= window_start]
        st.plotly_chart(charts.price_history(recent, regions, f"Home values, {period}"),
                        width="stretch")
    else:
        st.info("Pick at least one metro to compare.")

with tab_rank:
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts.growth_bar(
            analysis.rank(snap, growth_col, n=10),
            growth_col, f"Fastest-growing metros, {period}"), width="stretch")
    with right:
        st.plotly_chart(charts.growth_bar(
            analysis.rank(snap, growth_col, n=10, ascending=True),
            growth_col, f"Slowest-growing metros, {period}"), width="stretch")

with tab_afford:
    st.plotly_chart(charts.affordability_trend(trend[trend["date"] >= window_start], period),
                    width="stretch")
    st.plotly_chart(charts.price_vs_rent_scatter(snap), width="stretch")
    st.caption("Payment assumes 20% down and a 30-year fixed loan; excludes taxes and insurance.")

with tab_data:
    st.dataframe(
        snap,
        width="stretch",
        hide_index=True,
        column_config={
            "home_value": st.column_config.NumberColumn("Home value", format="$%d"),
            "rent": st.column_config.NumberColumn("Rent", format="$%d"),
            "monthly_payment": st.column_config.NumberColumn("Payment", format="$%d"),
            "yoy_change": st.column_config.NumberColumn("YoY", format="percent"),
            growth_col: st.column_config.NumberColumn(f"{years_back}y growth", format="percent"),
            "price_to_rent": st.column_config.NumberColumn("Price/rent", format="%.1f"),
        },
    )
    st.download_button("Download CSV", snap.to_csv(index=False), "housing_snapshot.csv")
