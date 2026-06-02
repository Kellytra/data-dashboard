import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Pairwise vs Reconciliation", layout="wide")

st.title("Example 2: Pairwise-based vs Reconciliation-based")
st.caption(
    "A dashboard comparing pairwise-based and reconciliation-based enrichment for linking city names to coordinates."
)

st.sidebar.header("Pairwise vs Reconciliation Parameters")


dataset_size = st.sidebar.number_input(
    "Dataset size (records)",
    min_value=1,
    value=6419,
    step=100
)

candidates_per_record = st.sidebar.slider(
    "Candidate matches per record",
    min_value=1,
    max_value=100,
    value=50,
    step=1
)

st.sidebar.markdown("---")

st.sidebar.subheader("Method effectiveness")

pairwise_effectiveness = st.sidebar.slider(
    "Pairwise effectiveness (%)",
    min_value=1,
    max_value=100,
    value=90,
    step=1
) / 100

reconciliation_effectiveness = st.sidebar.slider(
    "Reconciliation effectiveness (%)",
    min_value=1,
    max_value=100,
    value=95,
    step=1
) / 100

st.sidebar.markdown("---")

st.sidebar.subheader("Processing cost")

pairwise_cost_per_comparison = st.sidebar.number_input(
    "Pairwise cost per comparison (€)",
    min_value=0.000001,
    value=0.00005,
    step=0.00001,
    format="%.6f"
)

reconciliation_cost_per_lookup = st.sidebar.number_input(
    "Reconciliation cost per lookup (€)",
    min_value=0.000001,
    value=0.00010,
    step=0.00001,
    format="%.6f"
)

st.sidebar.markdown("---")

st.sidebar.subheader("Processing time")

pairwise_time_per_comparison = st.sidebar.number_input(
    "Pairwise time per comparison (sec)",
    min_value=0.0001,
    value=0.0100,
    step=0.001,
    format="%.4f"
)

reconciliation_time_per_lookup = st.sidebar.number_input(
    "Reconciliation time per lookup (sec)",
    min_value=0.0001,
    value=0.0200,
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

st.sidebar.markdown("---")

st.sidebar.subheader("Manual assessment work")

number_of_countries = st.sidebar.number_input(
    "Number of countries",
    min_value=1,
    value=3,
    step=1
)

manual_minutes_per_country = st.sidebar.number_input(
    "Manual work per country (min)",
    min_value=0.0,
    value=40.0,
    step=5.0
)

hourly_labour_cost = st.sidebar.number_input(
    "Labour cost per hour (€)",
    min_value=0.0,
    value=60.0,
    step=5.0
)

# Model assumptions

# In the paper example:
# perc = 1 because all distinct city values must be enriched.
# error/enrichment need = 1 because all cities need coordinates.
perc = 1.0
enrichment_need = 1.0


def calculate_strategy(strategy_name, is_pairwise):
    records_enriched = dataset_size * perc

    if is_pairwise:
        operations = dataset_size * candidates_per_record
        effectiveness = pairwise_effectiveness
        processing_cost = pairwise_cost_per_comparison

        improvement_cost = operations * pairwise_cost_per_comparison
        latency_sec = operations * pairwise_time_per_comparison
        
        manual_work_min = number_of_countries * manual_minutes_per_country
        assessment_cost = (manual_work_min / 60) * hourly_labour_cost

    else:
        operations = dataset_size
        effectiveness = reconciliation_effectiveness
        processing_cost = reconciliation_cost_per_lookup

        improvement_cost = operations * candidates_per_record *reconciliation_cost_per_lookup
        latency_sec = operations * reconciliation_time_per_lookup
        

        manual_work_min = 0
        assessment_cost = 0

    time_min = latency_sec / 60
    co2 = time_min * co2_per_minute

    # DQ improvement:
    # Since every city should be enriched, the improvement depends on how many cities
    # the method successfully links to coordinates.
    dq_improvement = dataset_size * effectiveness

    # DQ waste:
    # Cost spent on unsuccessful improvement attempts.
    dq_waste = improvement_cost * (1 - effectiveness)

    total_cost = assessment_cost + improvement_cost

    return {
        "Records enriched": records_enriched,
        "Operations": operations,
        "Effectiveness (%)": effectiveness * 100,
        "Processing cost ×1000 (€)": processing_cost * 1000,
        "Improvement cost (€)": improvement_cost,
        "Assessment cost (€)": assessment_cost,
        "Total cost (€)": total_cost,
        "DQ waste (€)": dq_waste,
        "DQ improvement": dq_improvement,
        "Time (min)": time_min,
        "Latency to result (sec)": latency_sec,
        "CO₂ (kg)": co2,
        "Human work (min)": manual_work_min,
    }


pairwise = calculate_strategy(
    strategy_name="Pairwise-based",
    is_pairwise=True
)

reconciliation = calculate_strategy(
    strategy_name="Reconciliation-based",
    is_pairwise=False
)

df = pd.DataFrame({
    "Pairwise-based": pairwise,
    "Reconciliation-based": reconciliation
}).T

# Main result cards

st.subheader("Main comparison")

cost_saved = pairwise["Total cost (€)"] - reconciliation["Total cost (€)"]
co2_saved = pairwise["CO₂ (kg)"] - reconciliation["CO₂ (kg)"]
time_saved = pairwise["Time (min)"] - reconciliation["Time (min)"]
operations_avoided = pairwise["Operations"] - reconciliation["Operations"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cost saved", f"€{cost_saved:,.2f}")
col2.metric("CO₂ saved", f"{co2_saved:.5f} kg")
col3.metric("Time saved", f"{time_saved:.2f} min")
col4.metric("Operations avoided", f"{operations_avoided:,.0f}")

# Raw values table

st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Normalized bar chart

st.subheader("Normalized comparison")

bar_metrics = [
    "Improvement cost (€)",
    "Total cost (€)",
    "DQ waste (€)",
    "DQ improvement",
    "Time (min)",
    "CO₂ (kg)",
    "Latency to result (sec)"
]

normalized_df = df[bar_metrics].copy()

for column in bar_metrics:
    max_value = normalized_df[column].max()

    if max_value == 0:
        normalized_df[column] = 0
    else:
        normalized_df[column] = normalized_df[column] / max_value * 100

bar_fig = go.Figure()

for metric in bar_metrics:
    bar_fig.add_trace(go.Bar(
        x=normalized_df.index,
        y=normalized_df[metric],
        name=metric,
        text=normalized_df[metric].round(1),
        textposition="outside"
    ))

bar_fig.update_layout(
    barmode="group",
    title="Normalized comparison across cost, quality, time, CO₂ and latency",
    yaxis_title="Normalized value (0-100)",
    height=500
)

st.plotly_chart(bar_fig, use_container_width=True)

st.caption(
    "The bar chart is normalized from 0 to 100. "
    "For each metric, 100 represents the highest value among the compared strategies. "
    "Higher values mean higher raw values, not necessarily better performance."
)


# Spider chart

st.subheader("Spider diagram")

spider_df = pd.DataFrame(index=df.index)

spider_df["Improvement cost"] = df["Improvement cost (€)"]
spider_df["DQ waste"] = df["DQ waste (€)"]
spider_df["Time"] = df["Time (min)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Latency"] = df["Latency to result (sec)"]
spider_df["Operations"] = df["Operations"]


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
    polar=dict(radialaxis=dict(visible=True,range=[0, 100])),
    showlegend=True,
    title="Normalized comparison: higher values are farther from the center",
    height=500
)

st.plotly_chart(fig, use_container_width=True)


# Explanation
with st.expander("Explanation of formulas and assumptions"):
    st.markdown("""
## STRATEGY ASSUMPTIONS

This example compares two ways of enriching city records with coordinates.

### Pairwise-based strategy

Pairwise-based enrichment compares each record with several candidate matches.

`operations = dataset_size * candidates_per_record`

It also includes manual assessment work.

### Reconciliation-based strategy

Reconciliation-based enrichment sends each record to a reconciliation service or API.

`operations = dataset_size`

It does not include manual assessment work.

---

## CORE FORMULAS

### Records enriched

Both strategies enrich all records in this example.

`records_enriched = dataset_size * perc`

`perc = 1`

### Operations

`operations_pairwise = dataset_size * candidates_per_record`

`operations_reconciliation = dataset_size`

Pairwise has more operations because each record is compared with several candidates.

### Effectiveness

Effectiveness represents how often the strategy successfully links a record to the correct coordinates.

For pairwise-based and reconciliation-based enrichment:

`effectiveness = pairwise_effectiveness`

`effectiveness = reconciliation_effectiveness`

### DQ improvement

DQ improvement estimates how many records are successfully enriched.

`DQ improvement = dataset_size * effectiveness`

### Improvement cost

`improvement_cost_pairwise = operations * pairwise_cost_per_comparison`

`improvement_cost_reconciliation = operations * candidates_per_record * reconciliation_cost_per_lookup`

The reconciliation cost still uses `candidates_per_record` to keep the cost basis comparable with the paper values.

### Assessment cost

Pairwise includes manual assessment work.

`manual_work_min = number_of_countries * manual_minutes_per_country`

`assessment_cost = manual_work_min / 60 * hourly_labour_cost`

For reconciliation:

`assessment_cost = 0`

### Total cost

`total_cost = assessment_cost + improvement_cost`

### DQ waste

DQ waste is the cost spent on enrichment attempts that do not succeed.

`DQ waste = improvement_cost * (1 - effectiveness)`

### Time and latency

`latency_pairwise = operations * pairwise_time_per_comparison`

`latency_reconciliation = operations * reconciliation_time_per_lookup`

`time_min = latency / 60`

### CO2 impact

`CO2 = time_min * co2_per_minute`

### Human work

Pairwise includes manual work.

Reconciliation has:

`human_work = 0`

---

## CHARTS

### Normalized bar chart

`normalized_value = value / max_value_for_that_metric * 100`

The chart compares metrics with different units on the same 0-100 scale.

### Spider diagram

The spider diagram also uses normalized raw values.

Values farther from the center are higher, but not necessarily better.

---

## MODEL SIMPLIFICATIONS

- Pairwise and reconciliation effectiveness are treated as comparable percentages.
- Reconciliation has fewer operations, but its cost still uses `candidates_per_record`.
- CO2 is estimated from processing time.
- Manual work is included only for pairwise enrichment.

---

## INTERPRETATION

Pairwise usually has more operations, higher latency, and more manual work.

Reconciliation usually has fewer operations and no manual assessment work.

The best strategy depends on the balance between quality, cost, waste, time, CO2, latency, and human involvement.
""")
