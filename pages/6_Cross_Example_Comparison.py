import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Cross-Example Comparison", layout="wide")

st.title("Cross-Example Comparison")
st.caption(
    "Comparison of the five examples based on absolute savings and percentage improvements."
)

# Helper functions


def percentage_reduction(baseline_value, improved_value):
    if baseline_value == 0:
        return 0
    return ((baseline_value - improved_value) / baseline_value) * 100


def calculate_savings(example_name, baseline_name, improved_name, baseline, improved):
    return {
        "Example": example_name,
        "Baseline strategy": baseline_name,
        "Improved strategy": improved_name,

        # Absolute values
        "Baseline cost (EUR)": baseline["cost"],
        "Improved cost (EUR)": improved["cost"],
        "Cost saved (EUR)": baseline["cost"] - improved["cost"],

        "Baseline DQ waste (EUR)": baseline["dq_waste"],
        "Improved DQ waste (EUR)": improved["dq_waste"],
        "DQ waste reduced (EUR)": baseline["dq_waste"] - improved["dq_waste"],

        "Baseline time (min)": baseline["time_min"],
        "Improved time (min)": improved["time_min"],
        "Time saved (min)": baseline["time_min"] - improved["time_min"],

        "Baseline latency (sec)": baseline["latency_sec"],
        "Improved latency (sec)": improved["latency_sec"],
        "Latency reduced (sec)": baseline["latency_sec"] - improved["latency_sec"],

        "Baseline CO2 (kg)": baseline["co2"],
        "Improved CO2 (kg)": improved["co2"],
        "CO2 saved (kg)": baseline["co2"] - improved["co2"],

        # Percentage improvements
        "Cost reduction (%)": percentage_reduction(baseline["cost"], improved["cost"]),
        "DQ waste reduction (%)": percentage_reduction(baseline["dq_waste"], improved["dq_waste"]),
        "Time reduction (%)": percentage_reduction(baseline["time_min"], improved["time_min"]),
        "Latency reduction (%)": percentage_reduction(baseline["latency_sec"], improved["latency_sec"]),
        "CO2 reduction (%)": percentage_reduction(baseline["co2"], improved["co2"]),
    }



# Sidebar


st.sidebar.header("Cross-comparison settings")

st.sidebar.markdown(
    """
The values below are based on the default parameters used in each example page.
The comparison uses one baseline strategy and one improved strategy for each example.
"""
)

show_absolute_values = st.sidebar.checkbox("Show absolute values table", value=True)
show_percentage_values = st.sidebar.checkbox("Show percentage improvement table", value=True)
show_strategy_overview = st.sidebar.checkbox("Show strategy overview", value=True)
show_spider_charts = st.sidebar.checkbox("Show spider diagrams", value=True)



# Example 1: Progressive Visualization
# Baseline: Bulk
# Improved: Progressive


# Default parameters from Example 1
dataset_size_1 = 51305
dirty_data_percent_1 = 10
assessment_cost_per_row_1 = 0.01
improvement_cost_per_row_1 = 0.0003
effectiveness_1 = 0.90
rows_per_hour_1 = 100000
co2_per_hour_1 = 0.0064
iterations_1 = 10
selection_overhead_factor_1 = 1.1

error_rate_1 = dirty_data_percent_1 / 100


def example_1_strategy(perc, is_progressive):
    processed_rows = dataset_size_1 * perc

    if is_progressive:
        tuples_per_iteration = processed_rows / iterations_1
        selection_overhead = selection_overhead_factor_1
    else:
        tuples_per_iteration = processed_rows
        selection_overhead = 1.0

    time_hours = (processed_rows / rows_per_hour_1) * selection_overhead
    time_min = time_hours * 60

    if is_progressive:
        latency_sec = (tuples_per_iteration / rows_per_hour_1) * 3600 * selection_overhead
    else:
        latency_sec = (processed_rows / rows_per_hour_1) * 3600

    assessment_cost = dataset_size_1 * perc * assessment_cost_per_row_1
    improvement_cost = dataset_size_1 * perc * error_rate_1 * improvement_cost_per_row_1
    dq_waste = dataset_size_1 * perc * error_rate_1 * improvement_cost_per_row_1 * (1 - effectiveness_1)
    total_cost = assessment_cost + improvement_cost
    co2 = time_hours * co2_per_hour_1

    return {
        "cost": total_cost,
        "dq_waste": dq_waste,
        "time_min": time_min,
        "latency_sec": latency_sec,
        "co2": co2,
    }


example_1_baseline = example_1_strategy(perc=1.0, is_progressive=False)
example_1_improved = example_1_strategy(perc=error_rate_1, is_progressive=True)


# Example 2: Reconciliation-based Data Enrichment
# Baseline: Pairwise-based
# Improved: Reconciliation-based


dataset_size_2 = 6419
candidates_per_record_2 = 50
pairwise_effectiveness_2 = 0.90
reconciliation_effectiveness_2 = 0.95
pairwise_cost_per_comparison_2 = 0.00005
reconciliation_cost_per_lookup_2 = 0.00010
pairwise_time_per_comparison_2 = 0.0100
reconciliation_time_per_lookup_2 = 0.0200
co2_per_minute_2 = 0.0001
number_of_countries_2 = 3
manual_minutes_per_country_2 = 40.0
hourly_labour_cost_2 = 60.0


def example_2_strategy(is_pairwise):
    if is_pairwise:
        operations = dataset_size_2 * candidates_per_record_2
        effectiveness = pairwise_effectiveness_2
        improvement_cost = operations * pairwise_cost_per_comparison_2
        latency_sec = operations * pairwise_time_per_comparison_2

        manual_work_min = number_of_countries_2 * manual_minutes_per_country_2
        assessment_cost = (manual_work_min / 60) * hourly_labour_cost_2
    else:
        operations = dataset_size_2
        effectiveness = reconciliation_effectiveness_2
        improvement_cost = operations * candidates_per_record_2 * reconciliation_cost_per_lookup_2
        latency_sec = operations * reconciliation_time_per_lookup_2
        assessment_cost = 0

    time_min = latency_sec / 60
    co2 = time_min * co2_per_minute_2
    dq_waste = improvement_cost * (1 - effectiveness)
    total_cost = assessment_cost + improvement_cost

    return {
        "cost": total_cost,
        "dq_waste": dq_waste,
        "time_min": time_min,
        "latency_sec": latency_sec,
        "co2": co2,
    }


example_2_baseline = example_2_strategy(is_pairwise=True)
example_2_improved = example_2_strategy(is_pairwise=False)


# Example 3: Cleaning on Demand
# Baseline: Full Cleaning
# Improved: On-Demand Cleaning


dataset_size_3 = 200000
query_relevant_percent_3 = 15
matching_cost_per_record_3 = 0.01
enrichment_cost_per_record_3 = 0.0005
effectiveness_3 = 0.90
unit_time_per_record_3 = 0.012
co2_per_minute_3 = 0.0001

query_relevant_rate_3 = query_relevant_percent_3 / 100
error_rate_3 = query_relevant_rate_3
unit_cleaning_cost_3 = matching_cost_per_record_3 + enrichment_cost_per_record_3


def example_3_strategy(perc):
    records_cleaned = dataset_size_3 * perc
    cleaning_cost = records_cleaned * unit_cleaning_cost_3
    latency_sec = records_cleaned * unit_time_per_record_3
    time_min = latency_sec / 60
    co2 = time_min * co2_per_minute_3

    dq_waste = (
        dataset_size_3
        * perc
        * error_rate_3
        * enrichment_cost_per_record_3
        * (1 - effectiveness_3)
    )

    return {
        "cost": cleaning_cost,
        "dq_waste": dq_waste,
        "time_min": time_min,
        "latency_sec": latency_sec,
        "co2": co2,
    }


example_3_baseline = example_3_strategy(perc=1.0)
example_3_improved = example_3_strategy(perc=query_relevant_rate_3)



# Example 4: Cleaning and Enrichment of Dynamic Data
# Baseline: Static Retrieval with Pre-cleaning
# Improved: Progressive Retrieval with On-demand Cleaning


candidate_tables_4 = 500
rows_per_table_4 = 400
relevant_tables_percent_4 = 10
entity_resolution_cost_4 = 0.01
api_enrichment_cost_4 = 0.0005
imputation_cost_4 = 0.002
cleaning_effectiveness_4 = 0.90
unit_time_per_row_4 = 0.024
co2_per_compute_minute_4 = 0.0001
progressive_passes_4 = 3

relevant_rate_4 = relevant_tables_percent_4 / 100
cost_per_row_4 = entity_resolution_cost_4 + api_enrichment_cost_4 + imputation_cost_4


def example_4_strategy(tables_cleaned, is_progressive):
    rows_processed = tables_cleaned * rows_per_table_4
    cleaning_cost = rows_processed * cost_per_row_4
    dq_waste = cleaning_cost * (1 - cleaning_effectiveness_4)

    processing_time_sec = rows_processed * unit_time_per_row_4
    time_min = processing_time_sec / 60
    co2 = time_min * co2_per_compute_minute_4

    if is_progressive:
        rows_per_pass = rows_processed / progressive_passes_4
        latency_sec = rows_per_pass * unit_time_per_row_4
    else:
        latency_sec = processing_time_sec

    return {
        "cost": cleaning_cost,
        "dq_waste": dq_waste,
        "time_min": time_min,
        "latency_sec": latency_sec,
        "co2": co2,
    }


example_4_baseline = example_4_strategy(
    tables_cleaned=candidate_tables_4,
    is_progressive=False
)

example_4_improved = example_4_strategy(
    tables_cleaned=candidate_tables_4 * relevant_rate_4,
    is_progressive=True
)



# Example 5: Data Preparation Pipelines Improvement
# Baseline: Complete pipeline
# Improved: Partial pipeline


dataset_size_5 = 200000
problematic_records_percent_5 = 20
cost_per_row_5 = 0.002
complete_effectiveness_5 = 0.8937
partial_effectiveness_5 = 0.8943
unit_time_per_row_5 = 0.002
energy_per_row_5 = 0.00005
co2_per_kwh_5 = 0.2

problematic_rows_5 = dataset_size_5 * problematic_records_percent_5 / 100


def example_5_strategy(improvement_steps, effectiveness):
    dq_improvement_cost = problematic_rows_5 * cost_per_row_5 * improvement_steps
    dq_waste = dq_improvement_cost * (1 - effectiveness)

    processing_time_sec = problematic_rows_5 * unit_time_per_row_5 * improvement_steps
    time_min = processing_time_sec / 60
    latency_sec = processing_time_sec

    energy_use = problematic_rows_5 * energy_per_row_5 * improvement_steps
    co2 = energy_use * co2_per_kwh_5

    return {
        "cost": dq_improvement_cost,
        "dq_waste": dq_waste,
        "time_min": time_min,
        "latency_sec": latency_sec,
        "co2": co2,
    }


example_5_baseline = example_5_strategy(
    improvement_steps=2,
    effectiveness=complete_effectiveness_5
)

example_5_improved = example_5_strategy(
    improvement_steps=1,
    effectiveness=partial_effectiveness_5
)


# Combined comparison data


comparison_rows = [
    calculate_savings(
        "Example 1: Progressive Visualization",
        "Bulk",
        "Progressive",
        example_1_baseline,
        example_1_improved,
    ),
    calculate_savings(
        "Example 2: Reconciliation-based Data Enrichment",
        "Pairwise-based",
        "Reconciliation-based",
        example_2_baseline,
        example_2_improved,
    ),
    calculate_savings(
        "Example 3: Cleaning on Demand",
        "Full Cleaning",
        "On-Demand Cleaning",
        example_3_baseline,
        example_3_improved,
    ),
    calculate_savings(
        "Example 4: Cleaning and Enrichment of Dynamic Data",
        "Static Retrieval with Pre-cleaning",
        "Progressive Retrieval with On-demand Cleaning",
        example_4_baseline,
        example_4_improved,
    ),
    calculate_savings(
        "Example 5: Data Preparation Pipelines Improvement",
        "Complete pipeline",
        "Partial pipeline",
        example_5_baseline,
        example_5_improved,
    ),
]

comparison_df = pd.DataFrame(comparison_rows)


# Page content

st.subheader("Strategy overview")

strategy_overview = comparison_df[
    ["Example", "Baseline strategy", "Improved strategy"]
]

if show_strategy_overview:
    st.dataframe(strategy_overview, use_container_width=True, hide_index=True)

st.markdown(
    """
The comparison uses the first strategy in each example as the baseline and the second strategy as the improved alternative.
The percentage improvements show how much the improved strategy reduces cost, waste, time, latency, and CO2 compared with its own baseline.
"""
)

# KPI cards


st.subheader("Average percentage improvements across examples")

avg_cost_reduction = comparison_df["Cost reduction (%)"].mean()
avg_waste_reduction = comparison_df["DQ waste reduction (%)"].mean()
avg_time_reduction = comparison_df["Time reduction (%)"].mean()
avg_co2_reduction = comparison_df["CO2 reduction (%)"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Avg. cost reduction", f"{avg_cost_reduction:.1f}%")
col2.metric("Avg. DQ waste reduction", f"{avg_waste_reduction:.1f}%")
col3.metric("Avg. time reduction", f"{avg_time_reduction:.1f}%")
col4.metric("Avg. CO reduction", f"{avg_co2_reduction:.1f}%")

# Percentage improvement chart

st.subheader("Percentage improvements by example")

percentage_metrics = [
    "Cost reduction (%)",
    "DQ waste reduction (%)",
    "Time reduction (%)",
    "Latency reduction (%)",
    "CO2 reduction (%)",
]

selected_percentage_metrics = st.multiselect(
    "Select percentage metrics to show",
    options=percentage_metrics,
    default=[
        "Cost reduction (%)",
        "DQ waste reduction (%)",
        "Time reduction (%)",
        "CO2 reduction (%)",
    ],
)

percentage_fig = go.Figure()

for metric in selected_percentage_metrics:
    percentage_fig.add_trace(go.Bar(
        x=comparison_df["Example"],
        y=comparison_df[metric],
        name=metric,
        text=comparison_df[metric].round(1),
        textposition="outside",
    ))

percentage_fig.update_layout(
    barmode="group",
    title="Relative reduction compared with each example baseline",
    xaxis_title="Example",
    yaxis_title="Reduction (%)",
    yaxis=dict(range=[0, 110]),
    height=550,
)

st.plotly_chart(percentage_fig, use_container_width=True)




# Tables

if show_percentage_values:
    st.subheader("Percentage improvement table")

    percentage_table = comparison_df[
        [
            "Example",
            "Cost reduction (%)",
            "DQ waste reduction (%)",
            "Time reduction (%)",
            "Latency reduction (%)",
            "CO2 reduction (%)",
        ]
    ].copy()

    st.dataframe(
        percentage_table.round(2),
        use_container_width=True,
        hide_index=True,
    )

if show_absolute_values:
    st.subheader("Absolute savings table")

    absolute_savings_table = comparison_df[
        [
            "Example",
            "Cost saved (EUR)",
            "DQ waste reduced (EUR)",
            "Time saved (min)",
            "Latency reduced (sec)",
            "CO2 saved (kg)",
        ]
    ].copy()

    st.dataframe(
        absolute_savings_table.round(4),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Baseline vs improved absolute values")

    absolute_values_table = comparison_df[
        [
            "Example",
            "Baseline cost (EUR)",
            "Improved cost (EUR)",
            "Baseline DQ waste (EUR)",
            "Improved DQ waste (EUR)",
            "Baseline time (min)",
            "Improved time (min)",
            "Baseline latency (sec)",
            "Improved latency (sec)",
            "Baseline CO2 (kg)",
            "Improved CO2 (kg)",
        ]
    ].copy()

    st.dataframe(
        absolute_values_table.round(4),
        use_container_width=True,
        hide_index=True,
    )



# Spider charts by example


def create_example_spider(row):
    metrics = [
        ("Cost", next(column for column in row.index if column.startswith("Baseline cost")),
         next(column for column in row.index if column.startswith("Improved cost"))),
        ("DQ waste", next(column for column in row.index if column.startswith("Baseline DQ waste")),
         next(column for column in row.index if column.startswith("Improved DQ waste"))),
        ("Time", "Baseline time (min)", "Improved time (min)"),
        ("Latency", "Baseline latency (sec)", "Improved latency (sec)"),
        ("CO2", next(column for column in row.index if column.startswith("Baseline CO")),
         next(column for column in row.index if column.startswith("Improved CO"))),
    ]

    categories = [metric[0] for metric in metrics]
    baseline_values = []
    improved_values = []

    for _, baseline_column, improved_column in metrics:
        max_value = max(row[baseline_column], row[improved_column])

        if max_value == 0:
            baseline_values.append(0)
            improved_values.append(0)
        else:
            baseline_values.append(row[baseline_column] / max_value * 100)
            improved_values.append(row[improved_column] / max_value * 100)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=baseline_values + [baseline_values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=row["Baseline strategy"],
    ))

    fig.add_trace(go.Scatterpolar(
        r=improved_values + [improved_values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=row["Improved strategy"],
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title=row["Example"].replace("Example ", "Ex. "),
        height=300,
        margin=dict(l=15, r=15, t=55, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


if show_spider_charts:
    st.subheader("Spider diagrams by example")

    st.caption(
        "Each spider diagram compares the baseline strategy with the improved strategy "
        "inside the same example. Values are normalized within each example."
    )

    spider_cols = st.columns(5)

    for col, (_, row) in zip(spider_cols, comparison_df.iterrows()):
        col.plotly_chart(create_example_spider(row), use_container_width=True)




# Explanation


with st.expander("Explanation of the cross-example comparison"):
    st.markdown("""
                
The cross-example comparison is based on the default parameter settings from each individual example page. Since the examples model different scenarios, some parameters differ in unit, scale, and interpretation. 
The comparison therefore uses common output metrics and percentage reductions relative to each example's own baseline.

## Purpose

The individual example pages compare strategies within one specific scenario.
This page compares the overall effect of the improved strategy across all five examples.

Because the examples use different input parameters, units, and scales, the cross-example comparison is based mainly on percentage improvements rather than raw values.

---

## Baseline and improved strategies

Each example is converted into a two-strategy comparison:

- The baseline strategy represents the original, complete, or less selective approach.
- The improved strategy represents the progressive, reduced, reconciled, or on-demand approach.

---

## Percentage reduction formula

For each metric, the percentage reduction is calculated as:

`Reduction (%) = (baseline value - improved value) / baseline value × 100`

This is used for:

- Cost reduction
- DQ waste reduction
- Time reduction
- Latency reduction
- CO₂ reduction

---

## Why percentage improvements are used

The examples operate at different scales. Some examples process rows, others process records, candidate matches, tables, or pipeline steps.

Using percentage improvements makes the examples easier to compare because each improved strategy is evaluated relative to its own baseline.

---

## How to interpret the chart

Higher percentage reduction means that the improved strategy reduces that metric more strongly compared with the baseline.

For these metrics, higher reduction is better because lower cost, waste, time, latency, and CO₂ are desirable.

---

## Absolute values

The absolute values are still shown because they provide important context.

For example, two examples may both show a 90% cost reduction, but the actual savings in euros may be very different.
""")
