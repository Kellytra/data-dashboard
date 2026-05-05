import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Progressive Visualization", layout="wide")

st.title("Example 1: Progressive Visualization")
st.caption("A dashboard comparing bulk processing with progressive processing based on sustainability and data quality trade-offs.")

# Sidebar inputs
st.sidebar.header("Input parameters")

dataset_size = st.sidebar.slider(
    "Dataset size (rows)",
    min_value=1000,
    max_value=100000,
    value=51305,
    step=1000
)

dirty_data_percent = st.sidebar.slider(
    "Percentage of data considered (%)",
    min_value=0,
    max_value=100,
    value=10,
    step=10
)

assessment_cost_per_row = st.sidebar.number_input(
    "Assessment cost per row (€)",
    min_value=0.00001,
    value=0.01,
    step=0.001,
    format="%.5f"
)

improvement_cost_per_row = st.sidebar.number_input(
    "Improvement cost per row (€)",
    min_value=0.00001,
    value=0.0003,
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

rows_per_hour = st.sidebar.number_input(
    "Processing speed (rows/hour)",
    min_value=1000,
    value=100000,
    step=1000
)

co2_per_hour = st.sidebar.number_input(
    "CO₂ per compute hour (kg)",
    min_value=0.0,
    value=0.0064,
    step=0.0001,
    format="%.5f"
)

iterations = st.sidebar.slider(
    "Number of progressive iterations",
    min_value=1,
    max_value=20,
    value=10,
    step=1
)

selection_overhead_factor = st.sidebar.slider(
    "Selection overhead (progressive)",
    min_value=1.0,
    max_value=2.0,
    value=1.1,
    step=0.05
)

bulk_human_work = st.sidebar.number_input(
    "Bulk human work (min)",
    min_value=0.0,
    value=20.0,
    step=1.0
)

progressive_human_work = st.sidebar.number_input(
    "Progressive human work (min)",
    min_value=0.0,
    value=10.0,
    step=1.0
)

# Model values
error_rate = dirty_data_percent / 100

bulk_perc = 1.0
progressive_perc = error_rate


def calculate_strategy(strategy_name, perc, human_work, is_progressive):
    processed_rows = dataset_size * perc

    if is_progressive:
        number_of_iterations = iterations
        tuples_per_iteration = processed_rows / iterations
        selection_overhead = selection_overhead_factor
    else:
        number_of_iterations = 1
        tuples_per_iteration = processed_rows
        selection_overhead = 1.0

    # Total processing time
    time_hours = (processed_rows / rows_per_hour) * selection_overhead
    time_minutes = time_hours * 60

    # Latency to first update
    # Bulk: first update comes after all rows are processed
    # Progressive: first update comes after the first increment/batch is processed
    if is_progressive:
        latency_seconds = (tuples_per_iteration / rows_per_hour) * 3600 * selection_overhead
    else:
        latency_seconds = (processed_rows / rows_per_hour) * 3600

    # Formula 1: DQImprovement = N × perc × e × p
    quality_improvement = dataset_size * perc * error_rate * effectiveness

    # Optional interpretation as final quality percentage
    initial_quality = 1 - error_rate
    quality_gain = perc * error_rate * effectiveness
    final_quality = min(initial_quality + quality_gain, 1.0)

    # Formula 2: DQAssessmentCost = N × perc × ac
    assessment_cost = dataset_size * perc * assessment_cost_per_row

    # Formula 3: DQImprovementCost = N × perc × e × c
    improvement_cost = dataset_size * perc * error_rate * improvement_cost_per_row

    # Formula 4: DQWaste = N × perc × e × c × (1 - p)
    dq_waste = dataset_size * perc * error_rate * improvement_cost_per_row * (1 - effectiveness)

    total_cost = assessment_cost + improvement_cost

    # Environmental impact
    co2 = time_hours * co2_per_hour

    return {
        "Processed rows": processed_rows,
        "Percentage processed (%)": perc * 100,
        "Iterations": number_of_iterations,
        "Tuples per iteration": tuples_per_iteration,
        "Quality improvement": quality_improvement,
        "Final quality (%)": final_quality * 100,
        "Assessment cost (€)": assessment_cost,
        "Improvement cost (€)": improvement_cost,
        "DQ waste (€)": dq_waste,
        "Total cost (€)": total_cost,
        "CO₂ (kg)": co2,
        "Time (min)": time_minutes,
        "Latency to first update (sec)": latency_seconds,
        "Human work (min)": human_work,
        "Effectiveness (%)": effectiveness * 100,
        "Selection overhead factor": selection_overhead,
    }


bulk = calculate_strategy(
    strategy_name="Bulk",
    perc=bulk_perc,
    human_work=bulk_human_work,
    is_progressive=False
)

progressive = calculate_strategy(
    strategy_name="Progressive",
    perc=progressive_perc,
    human_work=progressive_human_work,
    is_progressive=True
)

# DataFrame
df = pd.DataFrame({
    "Bulk": bulk,
    "Progressive": progressive
}).T

# Main result cards
st.subheader("Main comparison")

col1, col2, col3, col4 = st.columns(4)

cost_saved = bulk["Total cost (€)"] - progressive["Total cost (€)"]
co2_saved = bulk["CO₂ (kg)"] - progressive["CO₂ (kg)"]
time_saved = bulk["Time (min)"] - progressive["Time (min)"]
rows_avoided = bulk["Processed rows"] - progressive["Processed rows"]

col1.metric("Cost saved", f"€{cost_saved:.2f}")
col2.metric("CO₂ saved", f"{co2_saved:.5f} kg")
col3.metric("Time saved", f"{time_saved:.2f} min")
col4.metric("Rows avoided", f"{rows_avoided:,.0f}")

# Raw values table
st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Spider chart
st.subheader("Spider diagram")

spider_df = pd.DataFrame(index=df.index)

spider_df["Total cost"] = df["Total cost (€)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Time"] = df["Time (min)"]
spider_df["Latency"] = df["Latency to first update (sec)"]
spider_df["Human work"] = df["Human work (min)"]
spider_df["DQ waste"] = df["DQ waste (€)"]
spider_df["Quality improvement"] = df["Quality improvement"]

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
    st.write("""
    This dashboard compares two strategies:

    **Bulk processing** processes the entire dataset.  
    Therefore, `perc = 1.0`.

    **Progressive processing** processes only the dirty or relevant part of the dataset first.  
    Therefore, `perc = error rate`.

    The progressive strategy is divided into multiple iterations. Each iteration processes an increment containing multiple tuples, not just one row at a time.

    The formulas used are:

    - **Quality improvement** = dataset size × percentage processed × error rate × effectiveness
    - **Assessment cost** = dataset size × percentage processed × assessment cost per row
    - **Improvement cost** = dataset size × percentage processed × error rate × improvement cost per row
    - **DQ waste** = dataset size × percentage processed × error rate × improvement cost per row × (1 - effectiveness)

    The same effectiveness value is used for both Bulk and Progressive.

    Latency is calculated as:

    - **Bulk latency** = time needed to process all considered rows
    - **Progressive latency** = time needed to process the first increment

    The spider diagram is not inverted.  
    This means that values closer to the center are lower, while values farther from the center are higher.
    """)