import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Agentic RAG", layout="wide")

st.title("Example 4: Cleaning and Enrichment of Dynamic Data")
st.caption(
    "Comparison between static retrieval with pre-cleaning and progressive retrieval with on-demand cleaning."
)

st.sidebar.header("Agentic RAG Parameters")

# Input parameters
candidate_tables = st.sidebar.slider(
    "Number of candidate tables",
    min_value=50,
    max_value=1000,
    value=500,
    step=50
)

rows_per_table = st.sidebar.slider(
    "Average rows per table",
    min_value=50,
    max_value=1000,
    value=400,
    step=50
)

relevant_tables_percent = st.sidebar.slider(
    "Relevant tables per query (%)",
    min_value=0,
    max_value=100,
    value=10,
    step=5
)

entity_resolution_cost = st.sidebar.number_input(
    "Entity resolution cost per row (€)",
    min_value=0.0001,
    value=0.01,
    step=0.001,
    format="%.5f"
)

api_enrichment_cost = st.sidebar.number_input(
    "API enrichment cost per row (€)",
    min_value=0.0001,
    value=0.0005,
    step=0.0001,
    format="%.5f"
)

imputation_cost = st.sidebar.number_input(
    "Missing value imputation cost per row (€)",
    min_value=0.0001,
    value=0.002,
    step=0.0005,
    format="%.5f"
)

unit_time_per_row = st.sidebar.number_input(
    "Unit time per row (sec)",
    min_value=0.0001,
    value=0.024,
    step=0.001,
    format="%.4f"
)

co2_per_compute_minute = st.sidebar.number_input(
    "CO₂ per compute minute (kg)",
    min_value=0.0,
    value=0.0001,
    step=0.00001,
    format="%.5f"
)

progressive_passes = st.sidebar.slider(
    "Progressive cleaning passes",
    min_value=1,
    max_value=10,
    value=3,
    step=1
)

first_result_latency_sec = st.sidebar.number_input(
    "Initial partial result latency (sec)",
    min_value=0.1,
    value=1.5,
    step=0.5,
    format="%.1f"
)

# Model values
relevant_rate = relevant_tables_percent / 100
cost_per_row = entity_resolution_cost + api_enrichment_cost + imputation_cost

static_tables_cleaned = candidate_tables
progressive_tables_cleaned = candidate_tables * relevant_rate

static_rows_processed = static_tables_cleaned * rows_per_table
progressive_rows_processed = progressive_tables_cleaned * rows_per_table


def calculate_strategy(strategy_name, tables_cleaned, rows_processed):
    cleaning_cost = rows_processed * cost_per_row
    processing_time_sec = rows_processed * unit_time_per_row
    processing_time_min = processing_time_sec / 60
    co2 = processing_time_min * co2_per_compute_minute

    if strategy_name == "Static Retrieval":
        dq_waste = cleaning_cost * (1 - relevant_rate)
        latency_sec = processing_time_sec
        passes = 1
    else:
        dq_waste = 0
        latency_sec = first_result_latency_sec
        passes = progressive_passes

    return {
        "Tables cleaned": tables_cleaned,
        "Rows processed": rows_processed,
        "Cleaning cost (€)": cleaning_cost,
        "DQ waste (€)": dq_waste,
        "Processing time (min)": processing_time_min,
        "Latency to first result (sec)": latency_sec,
        "CO₂ (kg)": co2,
        "Progressive passes": passes,
    }


static = calculate_strategy(
    "Static Retrieval",
    static_tables_cleaned,
    static_rows_processed
)

progressive = calculate_strategy(
    "Progressive Retrieval",
    progressive_tables_cleaned,
    progressive_rows_processed
)

df = pd.DataFrame({
    "Static Retrieval with Pre-cleaning": static,
    "Progressive Retrieval with On-demand Cleaning": progressive
}).T

# Main comparison
st.subheader("Main comparison")

cost_saved = static["Cleaning cost (€)"] - progressive["Cleaning cost (€)"]
waste_reduced = static["DQ waste (€)"] - progressive["DQ waste (€)"]
rows_avoided = static["Rows processed"] - progressive["Rows processed"]
co2_saved = static["CO₂ (kg)"] - progressive["CO₂ (kg)"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cost saved", f"€{cost_saved:,.2f}")
col2.metric("DQ waste reduced", f"€{waste_reduced:,.2f}")
col3.metric("Rows avoided", f"{rows_avoided:,.0f}")
col4.metric("CO₂ saved", f"{co2_saved:.5f} kg")

# Raw values
st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Bar chart
st.subheader("Cost and DQ waste comparison")

bar_fig = go.Figure()

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Cleaning cost (€)"],
    name="Cleaning cost (€)",
    marker_color="#4C78A8"
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ waste (€)"],
    name="DQ waste (€)",
    marker_color="#F58518"
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
spider_df["Processing time"] = df["Processing time (min)"]
spider_df["Latency"] = df["Latency to first result (sec)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Rows processed"] = df["Rows processed"]


def normalize(value, max_value):
    if max_value == 0:
        return 0
    return value / max_value * 100


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

### Static Retrieval with Pre-cleaning

Static retrieval pre-cleans and standardizes all candidate tables before indexing.

- All candidate tables are cleaned.
- The cleaned tables are then available for retrieval.
- This gives consistent quality, but may clean many tables that are not needed for a specific query.


### Progressive Retrieval with On-demand Cleaning

Progressive retrieval retrieves and cleans only the tables needed for the current query.

- Only query-relevant tables are cleaned.
- Cleaning happens progressively over multiple passes.
- The system can return partial results early and refine them as more data is retrieved and cleaned.

---

## CORE FORMULAS

### Rows processed

`Rows processed = tables cleaned × rows per table`


### Cleaning cost

`Cleaning cost = rows processed × (entity resolution cost + API enrichment cost + imputation cost)`

This corresponds to the cost of applying the preparation operations.


### DQ waste

For the static approach:

`DQ waste = cleaning cost × (1 - relevant tables per query)`

This represents the cost of cleaning tables that are not used for the final query result.

For the progressive approach:

`DQ waste = 0`

This is a simplifying assumption: the agent retrieves and cleans only tables that are relevant to the query.

---

## LATENCY MODEL

### Static latency

`Latency = rows processed × unit time per row`

The static strategy must clean all candidate tables before results are available.


### Progressive latency

`Latency = initial partial result latency`

The progressive strategy can return an early partial result before all passes have completed.

---

## CO₂ MODEL

`CO₂ = processing time × CO₂ per compute minute`

CO₂ emissions are assumed to be proportional to processing time.

---

## SHARED ASSUMPTIONS

- The same cleaning costs are used for both strategies.
- The same unit time per row is used for both strategies.
- Only a percentage of candidate tables is relevant for each query.
- Progressive retrieval is modeled as multiple cleaning passes.
- The progressive strategy is assumed to minimize DQ waste by cleaning only what is needed.

---

## SPIDER DIAGRAM INTERPRETATION

The spider diagram is **not inverted**.

- Values closer to the center represent lower values.
- Values farther from the center represent higher values.
""")


