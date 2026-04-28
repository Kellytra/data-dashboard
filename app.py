import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Bulk vs Progressive", layout="wide")

st.title("Bulk vs Progressive Processing")
st.write(
    "This dashboard compares two data preparation strategies: "
    "processing all data at once vs. processing only relevant/dirty data first."
)

# Sidebar
st.sidebar.header("Input parameters")

dataset_size = st.sidebar.slider(
    "Dataset size (number of rows)",
    min_value=1000,
    max_value=100000,
    value=50000,
    step=1000
)

dirty_data_percent = st.sidebar.slider(
    "Dirty / relevant data (%)",
    min_value=1,
    max_value=100,
    value=10,
    step=1
)

improvement_cost_per_row = st.sidebar.number_input(
    "Improvement cost per row (€)",
    min_value=0.00001,
    max_value=0.01,
    value=0.0003,
    step=0.0001,
    format="%.5f"
)

assessment_cost_per_row = st.sidebar.number_input(
    "Assessment cost per row (€)",
    min_value=0.00001,
    max_value=0.05,
    value=0.01,
    step=0.001,
    format="%.5f"
)

co2_per_row = st.sidebar.number_input(
    "CO₂ per processed row (kg)",
    min_value=0.00000001,
    max_value=0.00001,
    value=0.00000006,
    step=0.00000001,
    format="%.8f"
)

bulk_effectiveness_percent = st.sidebar.slider(
    "Bulk effectiveness (%)",
    min_value=1,
    max_value=100,
    value=90,
    step=1
)

progressive_effectiveness_percent = st.sidebar.slider(
    "Progressive effectiveness (%)",
    min_value=1,
    max_value=100,
    value=88,
    step=1
)

bulk_human_work = st.sidebar.number_input(
    "Bulk human work (minutes)",
    min_value=0,
    max_value=500,
    value=20,
    step=1
)

progressive_human_work = st.sidebar.number_input(
    "Progressive human work (minutes)",
    min_value=0,
    max_value=500,
    value=10,
    step=1
)

# Calculations based on the evaluation model
error_rate = dirty_data_percent / 100

bulk_perc = 1.0
progressive_perc = error_rate

bulk_effectiveness = bulk_effectiveness_percent / 100
progressive_effectiveness = progressive_effectiveness_percent / 100


def calculate_strategy(perc, effectiveness, human_work):
    processed_rows = dataset_size * perc

    # Formula (1): DQImprovement = N * perc * e * p
    quality_improvement = dataset_size * perc * error_rate * effectiveness

    # Formula (2): DQAssessmentCost = N * perc * ac
    assessment_cost = dataset_size * perc * assessment_cost_per_row

    # Formula (3): DQImprovementCost = N * perc * e * c
    improvement_cost = dataset_size * perc * error_rate * improvement_cost_per_row

    # Total cost
    total_cost = assessment_cost + improvement_cost

    # Formula (4): DQWaste = N * perc * e * c * (1 - p)
    dq_waste = dataset_size * perc * error_rate * improvement_cost_per_row * (1 - effectiveness)

    # Environmental impact
    co2 = processed_rows * co2_per_row

    return {
        "Processed rows": processed_rows,
        "Quality improvement": quality_improvement,
        "Assessment cost (€)": assessment_cost,
        "Improvement cost (€)": improvement_cost,
        "Total cost (€)": total_cost,
        "CO₂ (kg)": co2,
        "DQ Waste (€)": dq_waste,
        "Human work (min)": human_work,
        "Effectiveness (%)": effectiveness * 100,
        "Percentage processed (%)": perc * 100,
    }


bulk = calculate_strategy(
    perc=bulk_perc,
    effectiveness=bulk_effectiveness,
    human_work=bulk_human_work
)

progressive = calculate_strategy(
    perc=progressive_perc,
    effectiveness=progressive_effectiveness,
    human_work=progressive_human_work
)

df = pd.DataFrame({
    "Bulk": bulk,
    "Progressive": progressive
}).T

# Normalize values for spider diagram
def lower_is_better(value, max_value):
    if max_value == 0:
        return 100
    return 100 - (value / max_value * 100)


def higher_is_better(value, max_value):
    if max_value == 0:
        return 0
    return value / max_value * 100


radar_df = pd.DataFrame(index=df.index)

radar_df["Low total cost"] = df["Total cost (€)"].apply(
    lambda x: lower_is_better(x, df["Total cost (€)"].max())
)

radar_df["Low CO₂"] = df["CO₂ (kg)"].apply(
    lambda x: lower_is_better(x, df["CO₂ (kg)"].max())
)

radar_df["Low waste"] = df["DQ Waste (€)"].apply(
    lambda x: lower_is_better(x, df["DQ Waste (€)"].max())
)

radar_df["Low human work"] = df["Human work (min)"].apply(
    lambda x: lower_is_better(x, df["Human work (min)"].max())
)

radar_df["Quality improvement"] = df["Quality improvement"].apply(
    lambda x: higher_is_better(x, df["Quality improvement"].max())
)

# Spider diagram
categories = list(radar_df.columns)

fig = go.Figure()

for method in radar_df.index:
    values = radar_df.loc[method].tolist()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=method
    ))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    title="Spider diagram: Bulk vs Progressive"
)

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Raw values")
    st.dataframe(df)

st.subheader("Explanation")
st.write("""
**Bulk** processes the entire dataset. In the model, this means that the percentage of data considered is 100%.

**Progressive** processing only starts with the relevant or dirty part of the dataset. This reduces the percentage of data considered, which can lower assessment cost, improvement cost, CO₂ emissions and waste.

The calculations are based on the evaluation model from the paper:

- Quality improvement = dataset size × percentage processed × error rate × effectiveness
- Assessment cost = dataset size × percentage processed × assessment cost per row
- Improvement cost = dataset size × percentage processed × error rate × improvement cost per row
- DQ waste = dataset size × percentage processed × error rate × improvement cost per row × (1 - effectiveness)
""")