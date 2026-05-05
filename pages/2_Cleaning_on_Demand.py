import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Cleaning on Demand", layout="wide")

st.title("Example 2: Cleaning on Demand")
st.caption(
    "Comparison between full offline cleaning and on-demand cleaning based on the paper."
)

st.sidebar.header("Cleaning on Demand Parameters")

# Input parameters
dataset_size = st.sidebar.slider(
    "Dataset size (records)",
    min_value=10000,
    max_value=500000,
    value=200000,
    step=10000
)

query_relevant_percent = st.sidebar.slider(
    "Query-relevant records (%)",
    min_value=0,
    max_value=100,
    value=15,
    step=5
)

matching_cost_per_record = st.sidebar.number_input(
    "Matching cost per record (€)",
    min_value=0.0001,
    value=0.01,
    step=0.001,
    format="%.5f"
)

enrichment_cost_per_record = st.sidebar.number_input(
    "Enrichment cost per record (€)",
    min_value=0.0001,
    value=0.0005,
    step=0.0001,
    format="%.5f"
)

rows_per_minute = st.sidebar.number_input(
    "Cleaning speed (records/min)",
    min_value=100,
    value=5000,
    step=100
)

co2_per_minute = st.sidebar.number_input(
    "CO₂ per compute minute (kg)",
    min_value=0.0,
    value=0.0001,
    step=0.00001,
    format="%.5f"
)

full_latency_min = st.sidebar.number_input(
    "Full cleaning latency before results (min)",
    min_value=0.0,
    value=40.0,
    step=1.0
)

on_demand_first_result_sec = st.sidebar.number_input(
    "On-demand time to first result (sec)",
    min_value=0.0,
    value=2.0,
    step=0.5
)

reuse_factor = st.sidebar.slider(
    "Reuse potential of cleaned data (%)",
    min_value=0,
    max_value=100,
    value=30,
    step=10
)

# Model values
query_relevant_rate = query_relevant_percent / 100
unit_cleaning_cost = matching_cost_per_record + enrichment_cost_per_record

full_records_cleaned = dataset_size
on_demand_records_cleaned = dataset_size * query_relevant_rate


def calculate_cleaning_strategy(strategy_name, records_cleaned, latency_to_first_result_sec):
    cleaning_cost = records_cleaned * unit_cleaning_cost
    time_min = records_cleaned / rows_per_minute
    co2 = time_min * co2_per_minute

    # Waste here means cleaning cost spent on data not needed for the current query.
    if strategy_name == "Full Cleaning":
        wasted_fraction = 1 - query_relevant_rate
        waste = cleaning_cost * wasted_fraction
    else:
        waste = 0

    # Simple usefulness score:
    # Full cleaning has more reuse potential, on-demand is optimized for current query.
    if strategy_name == "Full Cleaning":
        reuse_score = reuse_factor
    else:
        reuse_score = 100 - reuse_factor

    return {
        "Records cleaned": records_cleaned,
        "Percentage cleaned (%)": records_cleaned / dataset_size * 100,
        "Cleaning cost (€)": cleaning_cost,
        "Waste (€)": waste,
        "Time (min)": time_min,
        "CO₂ (kg)": co2,
        "Latency to first result (sec)": latency_to_first_result_sec,
        "Reuse / query-fit score": reuse_score,
    }


full_cleaning = calculate_cleaning_strategy(
    strategy_name="Full Cleaning",
    records_cleaned=full_records_cleaned,
    latency_to_first_result_sec=full_latency_min * 60
)

on_demand_cleaning = calculate_cleaning_strategy(
    strategy_name="On-Demand Cleaning",
    records_cleaned=on_demand_records_cleaned,
    latency_to_first_result_sec=on_demand_first_result_sec
)

df = pd.DataFrame({
    "Full Cleaning": full_cleaning,
    "On-Demand Cleaning": on_demand_cleaning
}).T

# Main result cards
st.subheader("Main comparison")

cost_saved = full_cleaning["Cleaning cost (€)"] - on_demand_cleaning["Cleaning cost (€)"]
waste_avoided = full_cleaning["Waste (€)"] - on_demand_cleaning["Waste (€)"]
time_saved = full_cleaning["Time (min)"] - on_demand_cleaning["Time (min)"]
records_avoided = full_cleaning["Records cleaned"] - on_demand_cleaning["Records cleaned"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cost saved", f"€{cost_saved:,.2f}")
col2.metric("Waste avoided", f"€{waste_avoided:,.2f}")
col3.metric("Time saved", f"{time_saved:.2f} min")
col4.metric("Records avoided", f"{records_avoided:,.0f}")

# Raw table
st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Bar chart
st.subheader("Cost and waste comparison")

bar_fig = go.Figure()

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Cleaning cost (€)"],
    name="Cleaning cost (€)"
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Waste (€)"],
    name="Waste (€)"
))

bar_fig.update_layout(
    barmode="group",
    title="Cleaning cost and waste",
    yaxis_title="€",
    height=450
)

st.plotly_chart(bar_fig, use_container_width=True)

# Spider chart
st.subheader("Spider diagram")

spider_df = pd.DataFrame(index=df.index)

spider_df["Cleaning cost"] = df["Cleaning cost (€)"]
spider_df["Waste"] = df["Waste (€)"]
spider_df["Time"] = df["Time (min)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Latency"] = df["Latency to first result (sec)"]
spider_df["Records cleaned"] = df["Records cleaned"]
spider_df["Reuse / query-fit"] = df["Reuse / query-fit score"]


def normalize(value, max_value):
    if max_value == 0:
        return 0
    return value / max_value * 100

def normalize_log(value, max_value):
    if max_value == 0:
        return 0
    return np.log1p(value) / np.log1p(max_value) * 100

radar_df = pd.DataFrame(index=spider_df.index)

for column in spider_df.columns:
    radar_df[column] = spider_df[column].apply(
        lambda x: normalize(x, spider_df[column].max())
    )



#for column in spider_df.columns:
#    if column == "Latency":
#        radar_df[column] = spider_df[column].apply(
#            lambda x: normalize_log(x, spider_df[column].max())
#        )
#    else:
#        radar_df[column] = spider_df[column].apply(
#            lambda x: normalize(x, spider_df[column].max())
#        )

categories = list(radar_df.columns)

fig = go.Figure()

for strategy in radar_df.index:
    values = radar_df.loc[strategy].tolist()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=strategy
    ))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    title="Normalized comparison: higher values are farther from the center",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Explanation
with st.expander("Explanation of model and assumptions"):
    st.write("""
    This example compares two cleaning strategies:

    **Full Cleaning (Offline/Batch)** cleans the entire dataset before the data is used.
    This gives a complete cleaned dataset, but it can be expensive and may clean many records
    that are not needed for the current query.

    **On-Demand Cleaning** cleans only the records needed to answer a specific query.
    This reduces cost, time, CO₂ emissions and waste when the query only needs a subset of the data.

    In this visualization:

    - **Records cleaned** represents how many tuples are actually processed.
    - **Cleaning cost** is calculated as records cleaned × (matching cost + enrichment cost).
    - **Waste** is the cost of cleaning records that are not relevant to the current query.
    - **Latency** represents how long the user waits before seeing the first result.
    - **Reuse / query-fit score** is a simplified score:
        - Full cleaning gets higher value when reuse potential is high.
        - On-demand cleaning gets higher value when the focus is a narrow one-time query.

    The spider diagram is not inverted:
    values near the center are lower, while values farther out are higher.
    """)