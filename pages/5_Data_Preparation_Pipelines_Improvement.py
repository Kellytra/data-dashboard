import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Data Preparation Pipelines Improvement", layout="wide")

st.title("Example 5: Data Preparation Pipelines Improvement")
st.caption(
    "Comparison between a complete data preparation pipeline and a reduced partial pipeline."
)

st.sidebar.header("Data Preparation Pipelines Improvement Parameters")

dataset_size = st.sidebar.slider(
    "Dataset size (rows)",
    min_value=10_000,
    max_value=500_000,
    value=200_000,
    step=10_000
)

problematic_records_percent = st.sidebar.slider(
    "Missing / ambiguous records (%)",
    min_value=1,
    max_value=100,
    value=20,
    step=1
)

cost_per_row = st.sidebar.number_input(
    "Cleaning cost per row (€)",
    min_value=0.0001,
    value=0.002,
    step=0.0001,
    format="%.4f"
)

complete_effectiveness = st.sidebar.slider(
    "Complete pipeline effectiveness",
    min_value=0.0,
    max_value=1.0,
    value=0.8937,
    step=0.0001,
    format="%.4f"
)

partial_effectiveness = st.sidebar.slider(
    "Partial pipeline effectiveness",
    min_value=0.0,
    max_value=1.0,
    value=0.8943,
    step=0.0001,
    format="%.4f"
)

st.sidebar.header("Sustainability Parameters")

unit_time_per_row = st.sidebar.number_input(
    "Unit time per row (sec)",
    min_value=0.00001,
    value=0.002,
    step=0.0001,
    format="%.5f"
)

energy_per_row = st.sidebar.number_input(
    "Energy use per row (kWh)",
    min_value=0.000001,
    value=0.00005,
    step=0.00001,
    format="%.6f"
)

co2_per_kwh = st.sidebar.number_input(
    "CO₂ per kWh (kg)",
    min_value=0.0001,
    value=0.2,
    step=0.01,
    format="%.4f"
)

# Model values

problematic_rows = dataset_size * problematic_records_percent / 100

complete_steps = 2
partial_steps = 1


def calculate_pipeline(pipeline_name, dq_dimensions, improvement_steps, effectiveness):
    processed_amount = problematic_rows * improvement_steps

    dq_improvement = problematic_rows * effectiveness
    dq_improvement_cost = problematic_rows * cost_per_row * improvement_steps

    # DQ waste represents the part of the improvement cost that does not lead
    # to successful improvement.
    dq_waste = dq_improvement_cost * (1 - effectiveness)

    processing_time_sec = problematic_rows * unit_time_per_row * improvement_steps
    processing_time_min = processing_time_sec / 60

    # Latency = time until the selected pipeline is completed.
    # There are no progressive passes or iterations in this example.
    latency_sec = processing_time_sec

    energy_use = problematic_rows * energy_per_row * improvement_steps
    co2 = energy_use * co2_per_kwh

    return {
        "DQ dimensions improved": dq_dimensions,
        "Improvement steps": improvement_steps,
        "Problematic rows": problematic_rows,
        "Processed amount": processed_amount,
        "Effectiveness": effectiveness,
        "DQ improvement": dq_improvement,
        "DQ improvement cost (€)": dq_improvement_cost,
        "DQ waste (€)": dq_waste,
        "Processing time (sec)": processing_time_sec,
        "Processing time (min)": processing_time_min,
        "Latency to result (sec)": latency_sec,
        "Energy use (kWh)": energy_use,
        "CO₂ (kg)": co2,
    }


complete = calculate_pipeline(
    "Complete pipeline",
    "Completeness + Accuracy",
    complete_steps,
    complete_effectiveness
)

partial = calculate_pipeline(
    "Partial pipeline",
    "Completeness only",
    partial_steps,
    partial_effectiveness
)

df = pd.DataFrame({
    "Complete pipeline": complete,
    "Partial pipeline": partial
}).T

# Main comparison

st.subheader("Main comparison")

cost_saved = complete["DQ improvement cost (€)"] - partial["DQ improvement cost (€)"]
waste_reduced = complete["DQ waste (€)"] - partial["DQ waste (€)"]
time_saved = complete["Processing time (min)"] - partial["Processing time (min)"]
co2_saved = complete["CO₂ (kg)"] - partial["CO₂ (kg)"]
processed_amount_reduced = complete["Processed amount"] - partial["Processed amount"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cost saved", f"€{cost_saved:,.2f}")
col2.metric("CO₂ saved", f"{co2_saved:.5f} kg")
col3.metric("Time saved", f"{time_saved:.2f} min")
col4.metric("Processed amount reduced", f"{processed_amount_reduced:,.0f}")

# Raw values

st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Bar chart

st.subheader("Cost and DQ waste comparison")

bar_fig = go.Figure()

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ improvement cost (€)"],
    name="DQ improvement cost (€)",
    text=df["DQ improvement cost (€)"].round(2),
    textposition="outside",
    marker_color="#2E8B57"
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ waste (€)"],
    name="DQ waste (€)",
    text=df["DQ waste (€)"].round(2),
    textposition="outside",
    marker_color="#CD5C5C"
))

bar_fig.update_layout(
    barmode="group",
    title="DQ improvement cost and DQ waste",
    yaxis_title="€",
    height=450
)

st.plotly_chart(bar_fig, use_container_width=True)

# Spider chart

st.subheader("Spider diagram")

spider_df = pd.DataFrame(index=df.index)

spider_df["DQ improvement cost"] = df["DQ improvement cost (€)"]
spider_df["DQ waste"] = df["DQ waste (€)"]
spider_df["Processing time"] = df["Processing time (min)"]
spider_df["Latency"] = df["Latency to result (sec)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Processed amount"] = df["Processed amount"]


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

This example compares two alternatives for Step 4 in a data preparation pipeline.

### Complete pipeline

The complete pipeline improves two data quality dimensions:

- **Completeness**: missing or ambiguous values
- **Accuracy**: outliers or incorrect values

`Complete pipeline = imputation + outlier detection/correction`

`complete_steps = 2`

### Partial pipeline

The partial pipeline follows a Reduce strategy and only improves the most important data quality dimension.

In this scenario, completeness is assumed to have the largest impact on the downstream ML task.

`Partial pipeline = imputation only`

`partial_steps = 1`

The purpose is to check whether skipping the less important accuracy step can reduce cost and resource use while keeping almost the same data quality improvement.

---

## CORE FORMULAS

### Problematic rows

`problematic_rows = dataset_size × problematic_records_percent / 100`

With the default values:

`problematic_rows = 200,000 × 20 / 100 = 40,000`

---

### Processed amount

Processed amount represents the number of row-step operations performed.

`processed_amount = problematic_rows × improvement_steps`

For the complete pipeline:

`processed_amount_complete = 40,000 × 2 = 80,000`

For the partial pipeline:

`processed_amount_partial = 40,000 × 1 = 40,000`

---

### DQ improvement

DQ improvement depends on the number of problematic rows and the effectiveness of the pipeline.

`DQ improvement = problematic_rows × effectiveness`

Using the article values:

`DQ improvement_complete = 40,000 × 0.8937 = 35,748`

`DQ improvement_partial = 40,000 × 0.8943 = 35,772`

This shows that the partial pipeline achieves approximately the same DQ improvement as the complete pipeline.

---

### DQ improvement cost

`DQ improvement cost = problematic_rows × cost_per_row × improvement_steps`

Using the default cost:

`DQ improvement cost_complete = 40,000 × 0.002 × 2 = €160`

`DQ improvement cost_partial = 40,000 × 0.002 × 1 = €80`

The partial pipeline is cheaper because it performs only one improvement step.

---

### DQ waste

DQ waste represents the part of the improvement cost that does not lead to successful improvement.

`DQ waste = DQ improvement cost × (1 - effectiveness)`

Lower DQ waste is better.

---

## SUSTAINABILITY FORMULAS

### Processing time

`processing_time = problematic_rows × unit_time_per_row × improvement_steps`

### Latency

In Example 5, latency is modeled as the time until the selected pipeline is finished.

There are no progressive passes or iterations in this example. The prepared data is only ready when the chosen pipeline has completed its improvement steps.

`latency = processing_time`

`processing_time = problematic_rows × unit_time_per_row × improvement_steps`

For the complete pipeline:

`latency_complete = problematic_rows × unit_time_per_row × 2`

For the partial pipeline:

`latency_partial = problematic_rows × unit_time_per_row × 1`

This means that the partial pipeline has lower latency because it performs fewer improvement steps.

### Energy use and CO₂

`energy_use = problematic_rows × energy_per_row × improvement_steps`

`CO₂ = energy_use × CO₂_per_kWh`

The partial pipeline has lower time, latency, energy use and CO₂ because it performs fewer improvement steps.

---

## SPIDER DIAGRAM INTERPRETATION

The spider diagram uses normalized values because the metrics have different units and scales.

`normalized_value = value / max_value_for_that_metric × 100`

The spider diagram is **not inverted**:

- Values closer to the center are lower.
- Values farther from the center are higher.
- For cost, waste, time, latency, CO₂ and processed amount, lower values are better.

---

## INTERPRETATION

With the default values from the article:

- Complete pipeline: `DQ improvement = 35,748`, `cost = €160`
- Partial pipeline: `DQ improvement = 35,772`, `cost = €80`

The partial pipeline achieves approximately the same DQ improvement as the complete pipeline, but at half the cost.

The main conclusion is that when one data quality dimension has much higher impact on the downstream task, it can be more sustainable to improve only that dimension instead of running the complete pipeline.
""")
