import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, date

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Footfall Analytics Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Footfall Analytics Dashboard")
st.write("Interactive BI dashboard built on cleaned & imputed data.")

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("notebooks/data/processed/footfall_clean.csv")
    df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
    return df

df = load_data()

# Load other CSVs
store_summary = pd.read_csv("notebooks/data/processed/store_summary.csv")
daily_summary = pd.read_csv("notebooks/data/processed/daily_summary.csv")

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------
st.sidebar.header("Filters")

min_date = df['invoice_date'].min().date()
max_date = df['invoice_date'].max().date()

date_input = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date)
)

# ✅ Handle empty input
if not date_input:
    start_date = df['invoice_date'].min()
    end_date   = df['invoice_date'].max()
elif isinstance(date_input, tuple):
    start_date = pd.to_datetime(date_input[0])
    end_date   = pd.to_datetime(date_input[1])
else:
    start_date = pd.to_datetime(date_input)
    end_date   = pd.to_datetime(date_input)

filtered = df[(df['invoice_date'] >= start_date) & (df['invoice_date'] <= end_date)]

stores = st.sidebar.multiselect(
    "Select Stores",
    options=sorted(df['invoice_associate_name'].unique()),
    default=sorted(df['invoice_associate_name'].unique())
)

filtered = filtered[filtered['invoice_associate_name'].isin(stores)]

# ---------------------------------------------------
# GUARD: If empty, show warning BUT continue
# ---------------------------------------------------
if filtered.empty:
    st.warning("No data available for this filter selection. Showing portfolio-level high-level metrics instead.")

    # ✅ fallback portfolio metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Footfall", f"{df['cy_imputed'].sum():,}")
    col2.metric("Avg Daily Footfall", f"{df.groupby('invoice_date')['cy_imputed'].mean().mean():.1f}")
    col3.metric("Unique Stores", df['invoice_associate_name'].nunique())
    st.stop()

# ---------------------------------------------------
# TOP METRICS
# ---------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Footfall", f"{filtered['cy_imputed'].sum():,}")
col2.metric("Avg Daily Footfall", f"{filtered.groupby('invoice_date')['cy_imputed'].mean().mean():.1f}")
col3.metric("Unique Stores", filtered['invoice_associate_name'].nunique())

st.markdown("---")

# ---------------------------------------------------
# VISUAL 1 — STORE RANKING
# ---------------------------------------------------
st.subheader("Store Ranking by Total Footfall")

store_totals = (
    filtered.groupby('invoice_associate_name')['cy_imputed']
    .sum()
    .sort_values(ascending=True)
)

fig, ax = plt.subplots(figsize=(11, 6))
store_totals.plot(kind='barh', ax=ax, color='steelblue')
ax.set_ylabel("")
ax.set_xlabel("Total Footfall")
st.pyplot(fig)

st.markdown("---")

# ---------------------------------------------------
# VISUAL 2 — DAILY TREND
# ---------------------------------------------------
st.subheader("Daily Footfall Trend")

daily = filtered.groupby('invoice_date')['cy_imputed'].sum()

fig, ax = plt.subplots(figsize=(12, 4))
daily.plot(ax=ax, color='purple')
ax.set_ylabel("Footfall")
ax.set_xlabel("")
st.pyplot(fig)

st.markdown("---")

# ---------------------------------------------------
# VISUAL 3 — WEEKDAY PATTERN
# ---------------------------------------------------
st.subheader("Average Footfall by Weekday")

order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

weekday = (
    filtered.groupby('weekday')['cy_imputed'].mean()
    .reindex(order)
)

fig, ax = plt.subplots(figsize=(8, 4))
weekday.plot(kind='bar', ax=ax, color='orange')
ax.set_ylabel("Avg Footfall")
ax.set_xlabel("")
st.pyplot(fig)

st.markdown("---")

# ---------------------------------------------------
# STORE DRILLDOWN TABLE
# ---------------------------------------------------
st.subheader("Store Drilldown Data")

st.dataframe(
    filtered[['invoice_date','invoice_associate_name','cy_imputed','store_segment']]
    .sort_values('invoice_date'),
    use_container_width=True
)

st.markdown("---")

# ---------------------------------------------------
# ALL DOWNLOAD BUTTONS
# ---------------------------------------------------
st.subheader("Download Data")

# 1) Filtered data
csv_filtered = filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download Filtered Footfall Data",
    data=csv_filtered,
    file_name="footfall_filtered.csv",
    mime="text/csv"
)

# 2) Store Summary
csv_store = store_summary.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download Store Summary",
    data=csv_store,
    file_name="store_summary.csv",
    mime="text/csv"
)

# 3) Daily Summary
csv_daily = daily_summary.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download Daily Summary",
    data=csv_daily,
    file_name="daily_summary.csv",
    mime="text/csv"
)
