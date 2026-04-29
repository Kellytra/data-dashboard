import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Bulk vs Progressive", layout="wide")

st.title("Bulk vs Progressive Processing")
st.caption("A simple dashboard comparing bulk processing with progressive processing.")


# Sidebar inputs

st.sidebar.header("Input parameters")

dataset_size = st.sidebar.slider("Dataset size (rows)", 1000, 100000, 51305, step=1000)

dirty_data_percent = st.sidebar.slider("Dirty / relevant data (%)", 1, 100, 10)

assessment_cost_per_row = st.sidebar.number_input("Assessment cost per row (€)", min_value=0.00001, value=0.01, format="%.5f")

improvement_cost_per_row = st.sidebar.number_input("Improvement cost per row (€)", min_value=0.00001, value=0.0003, format="%.5f")

bulk_effectiveness = st.sidebar.slider("Bulk effectiveness (%)", 1, 100, 90) / 100
progressive_effectiveness = st.sidebar.slider("Progressive effectiveness (%)", 1, 100, 88) / 100

rows_per_hour = st.sidebar.number_input("Processing speed (rows/hour)", 1000, value=100000, step=1000)

co2_per_hour = st.sidebar.number_input("CO₂ per compute hour (kg)", min_value=0.0, value=0.0064, format="%.5f")

bulk_human_work = st.sidebar.number_input("Bulk human work (min)", 0.0, value=20.0, step=1.0)
progressive_human_work = st.sidebar.number_input("Progressive human work (min)", 0.0, value=10.0, step=1.0)


# Model values

error_rate = dirty_data_percent / 100

bulk_perc = 1.0
progressive_perc = error_rate


# Calculation function

def calculate_strategy(perc, effectiveness, human_work, first_update_latency):
    processed_rows = dataset_size * perc
    time_hours = processed_rows / rows_per_hour
    time_minutes = time_hours * 60

    # Formula 1: DQImprovement = N × perc × e × p
    quality_improvement = dataset_size * perc * error_rate * effectiveness

    # Formula 2: DQAssessmentCost = N × perc × assessment cost
    assessment_cost = dataset_size * perc * assessment_cost_per_row

    # Formula 3: DQImprovementCost = N × perc × e × improvement cost
    improvement_cost = dataset_size * perc * error_rate * improvement_cost_per_row

    # Formula 4: DQWaste = N × perc × e × improvement cost × (1 - p)
    dq_waste = dataset_size * perc * error_rate * improvement_cost_per_row * (1 - effectiveness)

    total_cost = assessment_cost + improvement_cost
    co2 = time_hours * co2_per_hour

    return {
        "Processed rows": processed_rows,
        "Percentage processed (%)": perc * 100,
        "Quality improvement": quality_improvement,
        "Assessment cost (€)": assessment_cost,
        "Improvement cost (€)": improvement_cost,
        "DQ waste (€)": dq_waste,
        "Total cost (€)": total_cost,
        "CO₂ (kg)": co2,
        "Time (min)": time_minutes,
        "Latency to first update (sec)": first_update_latency,
        "Human work (min)": human_work,
        "Effectiveness (%)": effectiveness * 100,
    }

bulk = calculate_strategy(
    perc=bulk_perc,
    effectiveness=bulk_effectiveness,
    human_work=bulk_human_work,
    first_update_latency=31 * 60
)

progressive = calculate_strategy(
    perc=progressive_perc,
    effectiveness=progressive_effectiveness,
    human_work=progressive_human_work,
    first_update_latency=0.2
)


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


# Table

df = pd.DataFrame({
    "Bulk": bulk,
    "Progressive": progressive
}).T

st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# Spider chart

st.subheader("Spider diagram")

def lower_is_better(value, max_value):
    if max_value == 0:
        return 100
    return 100 - (value / max_value * 100)

def higher_is_better(value, max_value):
    if max_value == 0:
        return 0
    return value / max_value * 100

radar_df = pd.DataFrame(index=df.index)

radar_df["Low cost"] = df["Total cost (€)"].apply(
    lambda x: lower_is_better(x, df["Total cost (€)"].max())
)

radar_df["Low CO₂"] = df["CO₂ (kg)"].apply(
    lambda x: lower_is_better(x, df["CO₂ (kg)"].max())
)

radar_df["Low time"] = df["Time (min)"].apply(
    lambda x: lower_is_better(x, df["Time (min)"].max())
)

radar_df["Low latency"] = df["Latency to first update (sec)"].apply(
    lambda x: lower_is_better(x, df["Latency to first update (sec)"].max())
)

radar_df["Low human work"] = df["Human work (min)"].apply(
    lambda x: lower_is_better(x, df["Human work (min)"].max())
)

radar_df["Quality improvement"] = df["Quality improvement"].apply(
    lambda x: higher_is_better(x, df["Quality improvement"].max())
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
    title="Normalized comparison: Bulk vs Progressive",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Explanation

with st.expander("Explanation of formulas"):
    st.write("""
    This dashboard compares two strategies:

    **Bulk processing** processes the entire dataset.  
    Therefore, `perc = 1.0`.

    **Progressive processing** only processes the dirty or relevant part of the dataset first.  
    Therefore, `perc = error rate`.

    The formulas used are:

    - **Quality improvement** = dataset size × percentage processed × error rate × effectiveness
    - **Assessment cost** = dataset size × percentage processed × assessment cost per row
    - **Improvement cost** = dataset size × percentage processed × error rate × improvement cost per row
    - **DQ waste** = dataset size × percentage processed × error rate × improvement cost per row × (1 - effectiveness)

    In addition, the dashboard includes:

    - processed rows
    - percentage of data processed
    - time
    - latency to first update
    - CO₂ emissions
    - human work
    - total cost
    """)