import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Complete vs Partial Pipeline", layout="wide")

st.title("Example 5: Complete Pipeline vs. Partial Pipeline")
st.caption(
    "A comparison between a complete data preparation pipeline and a reduced partial pipeline."
)

# ------------------------------------------------------------
# Sidebar inputs
# ------------------------------------------------------------

st.sidebar.header("Input parameters")

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

partial_effectiveness = st.sidebar.slider(
    "Partial pipeline effectiveness",
    min_value=0.0,
    max_value=1.0,
    value=0.8943,
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

st.sidebar.header("Sustainability parameters")

time_per_row = st.sidebar.number_input(
    "Processing time per row (seconds)",
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

human_work_per_row = st.sidebar.number_input(
    "Human work per row (minutes)",
    min_value=0.00001,
    value=0.01,
    step=0.001,
    format="%.5f"
)

# ------------------------------------------------------------
# Calculations
# ------------------------------------------------------------

problematic_rows = dataset_size * problematic_records_percent / 100

# Complete pipeline:
# Step 1: imputation
# Step 2: outlier detection/correction
complete_steps = 2

# Partial pipeline:
# Step 1: imputation only
partial_steps = 1

complete_dq_improvement = problematic_rows * complete_effectiveness
partial_dq_improvement = problematic_rows * partial_effectiveness

complete_dq_improvement_cost = problematic_rows * cost_per_row * complete_steps
partial_dq_improvement_cost = problematic_rows * cost_per_row * partial_steps

cost_saving = complete_dq_improvement_cost - partial_dq_improvement_cost

if complete_dq_improvement_cost > 0:
    cost_saving_percent = cost_saving / complete_dq_improvement_cost * 100
else:
    cost_saving_percent = 0

complete_time = problematic_rows * time_per_row * complete_steps
partial_time = problematic_rows * time_per_row * partial_steps

complete_energy = problematic_rows * energy_per_row * complete_steps
partial_energy = problematic_rows * energy_per_row * partial_steps

complete_co2 = complete_energy * co2_per_kwh
partial_co2 = partial_energy * co2_per_kwh

complete_human_work = problematic_rows * human_work_per_row * complete_steps
partial_human_work = problematic_rows * human_work_per_row * partial_steps

time_saved = complete_time - partial_time
energy_saved = complete_energy - partial_energy
co2_saved = complete_co2 - partial_co2
human_work_saved = complete_human_work - partial_human_work

# ------------------------------------------------------------
# DataFrame
# ------------------------------------------------------------

df = pd.DataFrame({
    "Pipeline": ["Complete pipeline", "Partial pipeline"],
    "Improved DQ dimensions": [
        "Completeness + Accuracy",
        "Completeness only"
    ],
    "Improvement steps": [complete_steps, partial_steps],
    "Problematic rows": [problematic_rows, problematic_rows],
    "Effectiveness": [complete_effectiveness, partial_effectiveness],
    "DQ improvement": [complete_dq_improvement, partial_dq_improvement],
    "DQ improvement cost (€)": [
        complete_dq_improvement_cost,
        partial_dq_improvement_cost
    ],
    "Processing time (s)": [complete_time, partial_time],
    "Energy use (kWh)": [complete_energy, partial_energy],
    "CO₂ emissions (kg)": [complete_co2, partial_co2],
    "Human work (min)": [complete_human_work, partial_human_work],
})

# ------------------------------------------------------------
# Key metrics
# ------------------------------------------------------------

st.subheader("Key results")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Cost saved",
    f"€{cost_saving:,.2f}",
    f"{cost_saving_percent:.1f}%"
)

col2.metric(
    "Time saved",
    f"{time_saved:,.1f} s"
)

col3.metric(
    "CO₂ saved",
    f"{co2_saved:,.3f} kg"
)

col4.metric(
    "Human work saved",
    f"{human_work_saved:,.1f} min"
)

st.dataframe(df, use_container_width=True)


# ------------------------------------------------------------
# Combined chart: DQ improvement, cost, saving and steps
# ------------------------------------------------------------

st.subheader("Pipeline comparison")

fig_comparison = go.Figure()

fig_comparison.add_trace(go.Bar(
    name="DQ improvement",
    x=["Complete pipeline", "Partial pipeline"],
    y=[complete_dq_improvement, partial_dq_improvement],
    text=[
        round(complete_dq_improvement, 0),
        round(partial_dq_improvement, 0)
    ],
    textposition="auto"
))

fig_comparison.add_trace(go.Bar(
    name="DQ improvement cost (€)",
    x=["Complete pipeline", "Partial pipeline"],
    y=[complete_dq_improvement_cost, partial_dq_improvement_cost],
    text=[
        round(complete_dq_improvement_cost, 2),
        round(partial_dq_improvement_cost, 2)
    ],
    textposition="auto"
))

fig_comparison.add_trace(go.Bar(
    name="Cost saving (€)",
    x=["Complete pipeline", "Partial pipeline"],
    y=[0, cost_saving],
    text=[
        0,
        round(cost_saving, 2)
    ],
    textposition="auto"
))

fig_comparison.add_trace(go.Bar(
    name="Improvement steps",
    x=["Complete pipeline", "Partial pipeline"],
    y=[complete_steps, partial_steps],
    text=[
        complete_steps,
        partial_steps
    ],
    textposition="auto"
))

fig_comparison.update_layout(
    barmode="group",
    xaxis_title="Pipeline",
    yaxis_title="Value"
)

st.plotly_chart(fig_comparison, use_container_width=True)


# ------------------------------------------------------------
# Spider chart
# ------------------------------------------------------------

st.subheader("Spider chart")

spider_metrics = [
    "DQ improvement",
    "DQ improvement cost (€)",
    "Processing time (s)",
    "Energy use (kWh)",
    "CO₂ emissions (kg)",
    "Human work (min)"
]

spider_df = df[["Pipeline"] + spider_metrics].copy()

# Normalize all metrics to make them comparable in one spider chart.
# For each metric, the highest value becomes 100.
for metric in spider_metrics:
    max_value = spider_df[metric].max()

    if max_value > 0:
        spider_df[metric] = spider_df[metric] / max_value * 100
    else:
        spider_df[metric] = 0

fig_spider = go.Figure()

for _, row in spider_df.iterrows():
    fig_spider.add_trace(go.Scatterpolar(
        r=[row[metric] for metric in spider_metrics],
        theta=spider_metrics,
        fill="toself",
        name=row["Pipeline"]
    ))

fig_spider.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),
    showlegend=True
)

st.plotly_chart(fig_spider, use_container_width=True)

st.info(
    "In the spider chart, all values are normalized from 0 to 100. "
    "A higher value means more of that metric. For cost, time, energy, CO₂ and human work, lower is better. "
    "For DQ improvement, higher is better."
)

# ------------------------------------------------------------
# Explanation
# ------------------------------------------------------------



with st.expander("Explanation of formulas and assumptions"):
    st.markdown("""
This example compares two alternatives for improving data quality in a data preparation pipeline.

The goal is to evaluate whether it is always necessary to run the full pipeline, or whether it can be enough to only improve the most important data quality dimension.

In the article example, the pipeline is used before a machine learning regression task. The regression model predicts the number of impressions based on conditions such as keywords and budget.

The example focuses on Step 4 in the pipeline, where two data quality dimensions can be improved:

- **Completeness**: missing or ambiguous values
- **Accuracy**: outliers or incorrect values

The two pipeline alternatives are:

- **Complete pipeline**: imputation + outlier detection/correction
- **Partial pipeline**: imputation only

This means that the complete pipeline improves two data quality dimensions, while the partial pipeline only improves the most important one.
""")

    st.markdown("""
### Pipeline alternatives

The complete pipeline improves both completeness and accuracy.

**Complete pipeline**

`complete pipeline = completeness improvement + accuracy improvement`

In practice:

`complete pipeline = missing value imputation + outlier detection/correction`

The partial pipeline follows a Reduce strategy. It only improves the data quality dimension that has the highest impact on the downstream machine learning performance.

In this example, completeness is considered more important than accuracy.

**Partial pipeline**

`partial pipeline = completeness improvement only`

In practice:

`partial pipeline = missing value imputation only`

The reason this can be useful is that additional data preparation steps do not always improve the final result. If the extra improvement step has only a small effect on the model performance, the pipeline may use more resources without giving a meaningful benefit.

In some cases, extra cleaning can even make the model performance worse, because the cleaning process may introduce approximate or artificial values.
""")

    st.markdown("""
### Input parameters

The dataset size is:

`dataset_size = 200,000 rows`

The percentage of records with missing or ambiguous values is:

`problematic_records_percent = 20%`

The number of problematic rows is calculated as:

`problematic_rows = dataset_size × problematic_records_percent / 100`

Using the default values from the article:

`problematic_rows = 200,000 × 20 / 100`

`problematic_rows = 40,000 rows`

These are the rows that need data quality improvement.
""")

    st.markdown("""
### Number of improvement steps

The complete pipeline has two improvement steps:

`complete_steps = 2`

because it performs:

1. missing value imputation
2. outlier detection/correction

The partial pipeline has one improvement step:

`partial_steps = 1`

because it performs:

1. missing value imputation

This is the main difference between the two pipelines in this example.
""")

    st.markdown("""
### Effectiveness

Effectiveness represents how much improvement the pipeline gives compared to the full pipeline performance from previous experiments.

The article uses previous experiments to estimate the effectiveness of each pipeline.

The default values from the article are:

`complete_effectiveness = 0.8937`

`partial_effectiveness = 0.8943`

This means that the partial pipeline has slightly higher effectiveness in this specific example.

This may seem surprising, but the article explains that improving more dimensions does not always lead to better performance. If the second improvement step has only a marginal contribution, it can sometimes introduce approximated values and slightly reduce the final model performance.
""")

    st.markdown("""
### DQ improvement

DQ improvement measures how much data quality improvement is achieved by the pipeline.

The general formula is:

`DQ improvement = problematic_rows × effectiveness`

For the complete pipeline:

`DQ improvement complete = problematic_rows × complete_effectiveness`

Using the default values:

`DQ improvement complete = 40,000 × 0.8937`

`DQ improvement complete = 35,748`

For the partial pipeline:

`DQ improvement partial = problematic_rows × partial_effectiveness`

Using the default values:

`DQ improvement partial = 40,000 × 0.8943`

`DQ improvement partial = 35,772`

In this example, the two pipelines achieve almost the same DQ improvement. The partial pipeline is slightly higher because its effectiveness value is slightly higher in the article example.
""")

    st.markdown("""
### DQ improvement cost

DQ improvement cost measures how much it costs to improve the problematic rows.

The cost per row is:

`cost_per_row = €0.002`

The general formula is:

`DQ improvement cost = problematic_rows × cost_per_row × number_of_steps`

For the complete pipeline:

`DQ improvement cost complete = problematic_rows × cost_per_row × complete_steps`

Using the default values:

`DQ improvement cost complete = 40,000 × 0.002 × 2`

`DQ improvement cost complete = €160`

For the partial pipeline:

`DQ improvement cost partial = problematic_rows × cost_per_row × partial_steps`

Using the default values:

`DQ improvement cost partial = 40,000 × 0.002 × 1`

`DQ improvement cost partial = €80`

The partial pipeline is cheaper because it skips the outlier detection/correction step.
""")

    st.markdown("""
### Cost saving

Cost saving measures how much money is saved by using the partial pipeline instead of the complete pipeline.

The formula is:

`cost_saving = complete_dq_improvement_cost - partial_dq_improvement_cost`

Using the default values:

`cost_saving = 160 - 80`

`cost_saving = €80`

The percentage cost saving is:

`cost_saving_percent = cost_saving / complete_dq_improvement_cost × 100`

Using the default values:

`cost_saving_percent = 80 / 160 × 100`

`cost_saving_percent = 50%`

This means that the partial pipeline saves 50% of the DQ improvement cost in this example.
""")

    st.markdown("""
### Processing time

Processing time is included as an additional sustainability indicator.

The time per row describes how long one improvement step takes for one problematic row.

The general formula is:

`processing_time = problematic_rows × time_per_row × number_of_steps`

For the complete pipeline:

`processing_time_complete = problematic_rows × time_per_row × complete_steps`

For the partial pipeline:

`processing_time_partial = problematic_rows × time_per_row × partial_steps`

The time saved is:

`time_saved = processing_time_complete - processing_time_partial`

The partial pipeline usually has lower processing time because it performs fewer improvement steps.
""")

    st.markdown("""
### Energy use

Energy use is also included as a sustainability indicator.

The energy per row describes how much energy one improvement step uses for one problematic row.

The general formula is:

`energy_use = problematic_rows × energy_per_row × number_of_steps`

For the complete pipeline:

`energy_use_complete = problematic_rows × energy_per_row × complete_steps`

For the partial pipeline:

`energy_use_partial = problematic_rows × energy_per_row × partial_steps`

The energy saved is:

`energy_saved = energy_use_complete - energy_use_partial`

The partial pipeline usually uses less energy because it skips one improvement step.
""")

    st.markdown("""
### CO₂ emissions

CO₂ emissions are calculated from the energy use.

The formula is:

`CO₂ emissions = energy_use × CO₂_per_kWh`

For the complete pipeline:

`CO₂_complete = energy_use_complete × CO₂_per_kWh`

For the partial pipeline:

`CO₂_partial = energy_use_partial × CO₂_per_kWh`

The CO₂ saved is:

`CO₂_saved = CO₂_complete - CO₂_partial`

Lower energy use leads to lower CO₂ emissions.
""")

    st.markdown("""
### Human work

Human work is included to estimate how much manual effort is needed in the data preparation process.

The human work per row describes how many minutes of human work are needed for one improvement step on one problematic row.

The general formula is:

`human_work = problematic_rows × human_work_per_row × number_of_steps`

For the complete pipeline:

`human_work_complete = problematic_rows × human_work_per_row × complete_steps`

For the partial pipeline:

`human_work_partial = problematic_rows × human_work_per_row × partial_steps`

The human work saved is:

`human_work_saved = human_work_complete - human_work_partial`

The partial pipeline usually requires less human work because fewer data quality improvement actions are applied.
""")

    st.markdown("""
### Combined chart

The combined chart compares four important values:

- DQ improvement
- DQ improvement cost
- Cost saving
- Improvement steps

These values have very different units and scales. For example, DQ improvement is around 35,000, while the number of improvement steps is only 1 or 2.

Because of this, the chart can be normalized.

The normalization formula is:

`normalized_value = value / max_value_for_that_metric × 100`

This means that the highest value for each metric becomes 100%.

For example, if the complete pipeline has the highest cost:

`complete cost = 160`

`partial cost = 80`

then:

`normalized complete cost = 160 / 160 × 100 = 100%`

`normalized partial cost = 80 / 160 × 100 = 50%`

This makes it easier to compare metrics with different units in the same chart.
""")

    st.markdown("""
### Spider chart

The spider chart compares the two pipelines across several sustainability and data quality indicators:

- DQ improvement
- DQ improvement cost
- Processing time
- Energy use
- CO₂ emissions
- Human work

Since these metrics use different units, the values are normalized before they are shown in the spider chart.

The formula is:

`normalized_value = value / max_value_for_that_metric × 100`

Important:

- For DQ improvement, higher is better.
- For cost, time, energy, CO₂ and human work, lower is better.

Therefore, the spider chart should not be read as “bigger is always better”. It shows how much of each metric each pipeline has compared to the other pipeline.
""")

    st.markdown("""
### Interpretation

With the default values from the article, the complete pipeline gives:

`DQ improvement = 35,748`

`DQ improvement cost = €160`

The partial pipeline gives:

`DQ improvement = 35,772`

`DQ improvement cost = €80`

This shows that the partial pipeline achieves approximately the same DQ improvement as the complete pipeline, but at half the cost.

The reason is that the partial pipeline only improves the most important data quality dimension, completeness, and skips the less important dimension, accuracy.

The main conclusion is:

`If the skipped data quality dimension has only a small impact on the final ML performance, a partial pipeline can reduce cost, time, energy use, CO₂ emissions and human work while keeping almost the same DQ improvement.`

However, this depends on knowing which data quality dimension is most important for the downstream task.

In the article, this is based on a knowledge base from previous experiments. Without this knowledge, skipping a data quality dimension could reduce the quality of the final analysis.
""")