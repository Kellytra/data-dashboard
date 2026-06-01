import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Cleaning on Demand", layout="wide")

st.title("Example 3: Cleaning on Demand")
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

effectiveness = st.sidebar.slider(
    "Method effectiveness (%)",
    min_value=1,
    max_value=100,
    value=90,
    step=1
) / 100

unit_time_per_record = st.sidebar.number_input(
    "Unit time per record (sec)",
    min_value=0.0001,
    value=0.012,
    step=0.001,
    format="%.4f"
)

co2_per_minute = st.sidebar.number_input(
    "CO₂ per compute minute (kg)",
    min_value=0.0,
    value=0.0001,
    step=0.00001,
    format="%.5f"
)

# Model values
query_relevant_rate = query_relevant_percent / 100

# Simplifying assumption:
# The query-relevant fraction is also used as the error rate approximation.
error_rate = query_relevant_rate

unit_cleaning_cost = matching_cost_per_record + enrichment_cost_per_record

full_perc = 1.0
on_demand_perc = query_relevant_rate


def calculate_cleaning_strategy(perc):
    records_cleaned = dataset_size * perc

    # Cleaning cost
    cleaning_cost = records_cleaned * unit_cleaning_cost

    # Latency and processing time
    latency_sec = records_cleaned * unit_time_per_record
    time_min = latency_sec / 60

    # CO₂ impact
    co2 = time_min * co2_per_minute

    # DQ improvement: N × perc × e × p
    #dq_improvement = dataset_size * perc * error_rate * effectiveness

    # DQ waste: N × perc × e × c × (1 - p)
    # Here, enrichment cost is used as the improvement cost c.
    dq_waste = (
        dataset_size
        * perc
        * error_rate
        * enrichment_cost_per_record
        * (1 - effectiveness)
    )

    return {
        "Records cleaned": records_cleaned,
        "Percentage cleaned (%)": perc * 100,
        "Cleaning cost (€)": cleaning_cost,
        "DQ waste (€)": dq_waste,
        "Time (min)": time_min,
        "CO₂ (kg)": co2,
        "Latency to result (sec)": latency_sec,
        "Effectiveness (%)": effectiveness * 100,
    }


full_cleaning = calculate_cleaning_strategy(full_perc)
on_demand_cleaning = calculate_cleaning_strategy(on_demand_perc)

df = pd.DataFrame({
    "Full Cleaning": full_cleaning,
    "On-Demand Cleaning": on_demand_cleaning
}).T

# Main result cards
st.subheader("Main comparison")

cost_saved = full_cleaning["Cleaning cost (€)"] - on_demand_cleaning["Cleaning cost (€)"]
dq_waste_reduced = full_cleaning["DQ waste (€)"] - on_demand_cleaning["DQ waste (€)"]
time_saved = full_cleaning["Time (min)"] - on_demand_cleaning["Time (min)"]
records_avoided = full_cleaning["Records cleaned"] - on_demand_cleaning["Records cleaned"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cost saved", f"€{cost_saved:,.2f}")
col2.metric("DQ waste reduced", f"€{dq_waste_reduced:,.4f}")
col3.metric("Time saved", f"{time_saved:.2f} min")
col4.metric("Records avoided", f"{records_avoided:,.0f}")

# Raw table
st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Bar chart
st.subheader("Cost and DQ waste comparison")

bar_fig = go.Figure()

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Cleaning cost (€)"],
    name="Cleaning cost (€)",
    marker_color="#2E8B57" 
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ waste (€)"],
    name="DQ waste (€)",
    marker_color="#CD5C5C" 
))

bar_fig.update_layout(
    barmode="group",
    title="Cleaning cost and DQ waste",
    yaxis_title="€",
    height=450
)

st.plotly_chart(bar_fig, use_container_width=True)

# Spider chart
st.subheader("Spider diagram")

spider_df = pd.DataFrame(index=df.index)

spider_df["Cleaning cost"] = df["Cleaning cost (€)"]
spider_df["DQ waste"] = df["DQ waste (€)"]
spider_df["Time"] = df["Time (min)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Latency"] = df["Latency to result (sec)"]
spider_df["Records cleaned"] = df["Records cleaned"]


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
with st.expander("Explanation of formulas and assumptions"):
    st.markdown("""
## STRATEGY ASSUMPTIONS

### Full Cleaning

Full Cleaning processes the entire dataset before the data is used.

- Percentage processed:

    `perc = 1.0`

- The result is only available after all records have been cleaned.


### On-Demand Cleaning

On-Demand Cleaning processes only the records needed for a specific query.

- Percentage processed:

    `perc = query-relevant records`

- The result is available after the query-relevant subset has been cleaned.

---

## CORE FORMULAS

### Records cleaned

`Records cleaned = dataset size × percentage processed`
                
This represents the number of records that are cleaned under each strategy.

### Cleaning cost

`Cleaning cost = records cleaned × (matching cost per record + enrichment cost per record)`

This represents the total cost of applying the cleaning operations.

### DQ waste

`DQ waste = dataset size × percentage processed × error rate × improvement cost × (1 - effectiveness)`

In this example, enrichment cost is used as the improvement cost.

---

## LATENCY MODEL

Latency is calculated by formula instead of being manually assigned.

### Full Cleaning latency

`Latency = unit time per record × dataset size`

Full Cleaning must process the whole dataset before producing the result.

### On-Demand Cleaning latency

`Latency = unit time per record × (dataset size × query-relevant records)`

On-Demand Cleaning only processes the subset needed for the query.

---

## CO₂ MODEL

`CO₂ = processing time × CO₂ per compute minute`

CO₂ emissions are assumed to be proportional to processing time.

---

## SHARED ASSUMPTIONS

- The same effectiveness value is used for both Full Cleaning and On-Demand Cleaning.
- The same matching and enrichment costs are used for both strategies.
- The same unit time per record is used for both strategies.
- Query-relevant records determine the percentage of data processed by On-Demand Cleaning.
- The query-relevant fraction is also used as a simplified approximation of the error rate.
- Reuse potential is not included in this version, since it was not part of the core comparison.
- DQ waste is included as a common metric, using the same structure as in the other examples.

---

## SPIDER DIAGRAM INTERPRETATION

The spider diagram is **not inverted**.

- Values closer to the center represent lower values.
- Values farther from the center represent higher values.

""")