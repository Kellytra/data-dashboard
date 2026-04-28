import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Bulk vs Progressive", layout="wide")

st.title("Bulk vs Progressive Processing")
st.write("This dashboard compares two data preparation strategies: processing all data at once vs. processing only relevant/dirty data first.")

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

cost_per_row = st.sidebar.number_input(
    "Cost per processed row (€)",
    min_value=0.00001,
    max_value=0.01,
    value=0.0003,
    step=0.0001,
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

# Calculations
dirty_rows = dataset_size * (dirty_data_percent / 100)

bulk_processed = dataset_size
progressive_processed = dirty_rows

bulk = {
    "Processed rows": bulk_processed,
    "Cost (€)": bulk_processed * cost_per_row,
    "CO₂ (kg)": bulk_processed * co2_per_row,
    "Waste": dataset_size - dirty_rows,
    "Human work": 20,
    "Quality": 90,
}

progressive = {
    "Processed rows": progressive_processed,
    "Cost (€)": progressive_processed * cost_per_row,
    "CO₂ (kg)": progressive_processed * co2_per_row,
    "Waste": progressive_processed * 0.1,
    "Human work": 10,
    "Quality": 88,
}

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
    return value / max_value * 100

radar_df = pd.DataFrame(index=df.index)

radar_df["Low cost"] = df["Cost (€)"].apply(lambda x: lower_is_better(x, df["Cost (€)"].max()))
radar_df["Low CO₂"] = df["CO₂ (kg)"].apply(lambda x: lower_is_better(x, df["CO₂ (kg)"].max()))
radar_df["Low waste"] = df["Waste"].apply(lambda x: lower_is_better(x, df["Waste"].max()))
radar_df["Low human work"] = df["Human work"].apply(lambda x: lower_is_better(x, df["Human work"].max()))
radar_df["Quality"] = df["Quality"].apply(lambda x: higher_is_better(x, 100))

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
**Bulk** processes the entire dataset at once. This gives high quality, but also higher cost, CO₂ emissions and waste.

**Progressive** processing only starts with the relevant or dirty part of the dataset. This reduces cost, CO₂ emissions and waste, while keeping quality almost the same.
""")