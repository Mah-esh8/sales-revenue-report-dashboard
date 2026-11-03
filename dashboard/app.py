"""Streamlit + Plotly dashboard backed by MySQL.

Run from the project root:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent / "etl"))
from db_connection import get_engine  # noqa: E402

st.set_page_config(page_title="Sales & Revenue Dashboard", layout="wide")


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    engine = get_engine()
    try:
        df = pd.read_sql("SELECT * FROM sales_data", engine)
    finally:
        engine.dispose()
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


st.title("📊 Sales & Revenue Analysis Dashboard")

try:
    df = load_data()
except Exception as e:
    st.error(
        "Couldn't connect to MySQL. Check that the database is running, "
        "the .env file contains the correct credentials, and the ETL steps are complete. "
        "\\n\\nDetails: " + str(e)
    )
    st.stop()

if df.empty:
    st.warning("Connected to MySQL, but sales_data has no rows yet. Run the ETL load step first.")
    st.stop()

st.sidebar.header("Filters")
regions = st.sidebar.multiselect(
    "Region", sorted(df["region"].unique()), default=list(df["region"].unique())
)
products = st.sidebar.multiselect(
    "Product", sorted(df["product"].unique()), default=list(df["product"].unique())
)
date_min, date_max = df["order_date"].min().date(), df["order_date"].max().date()
date_range = st.sidebar.date_input("Order date range", (date_min, date_max))

filtered = df[df["region"].isin(regions) & df["product"].isin(products)]
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start = pd.Timestamp(date_range[0])
    # Exclusive next-day boundary includes every row on the selected end date.
    end_exclusive = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
    filtered = filtered[
        (filtered["order_date"] >= start) & (filtered["order_date"] < end_exclusive)
    ]
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    selected_day = pd.Timestamp(date_range[0])
    filtered = filtered[
        (filtered["order_date"] >= selected_day)
        & (filtered["order_date"] < selected_day + pd.Timedelta(days=1))
    ]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"₹{filtered['total_sales'].sum():,.0f}")
col2.metric("Total Orders", f"{len(filtered):,}")
col3.metric("Units Sold", f"{int(filtered['quantity'].sum()):,}")
avg_order = filtered["total_sales"].mean() if len(filtered) else 0
col4.metric("Avg Order Value", f"₹{avg_order:,.0f}")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Revenue by Region")
    region_rev = filtered.groupby("region", as_index=False)["total_sales"].sum()
    fig = px.bar(region_rev, x="region", y="total_sales", color="region", text_auto=".2s")
    fig.update_layout(showlegend=False, yaxis_title="Revenue", xaxis_title="Region")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by Product")
    product_rev = filtered.groupby("product", as_index=False)["total_sales"].sum()
    fig = px.pie(product_rev, names="product", values="total_sales", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Monthly Revenue Trend")
monthly = (
    filtered.set_index("order_date")
    .resample("MS")["total_sales"]
    .sum()
    .reset_index()
)
fig = px.line(monthly, x="order_date", y="total_sales", markers=True)
fig.update_layout(yaxis_title="Revenue", xaxis_title="Month")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Sales Rep Leaderboard")
leaderboard = (
    filtered.groupby("sales_rep", as_index=False)
    .agg(orders=("order_id", "count"), revenue=("total_sales", "sum"))
    .sort_values("revenue", ascending=False)
)
st.dataframe(leaderboard, use_container_width=True, hide_index=True)

with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
