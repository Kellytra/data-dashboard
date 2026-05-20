import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Pairwise vs Reconciliation", layout="wide")

st.title("Example 3: Pairwise-based vs Reconciliation-based")
st.caption(
    "A dashboard comparing pairwise-based and reconciliation-based enrichment for linking city names to coordinates."
)

# ------------------------------------------------------------
# Sidebar inputs
# ------------------------------------------------------------

st.sidebar.header("Pairwise vs Reconciliation Parameters")

number_of_cities = st.sidebar.number_input(
    "Number of distinct city values",
    min_value=1,
    value=6419,
    step=100
)

top_k_candidates = st.sidebar.slider(
    "Top-k candidates for pairwise matching",
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

# ------------------------------------------------------------
# Model assumptions
# ------------------------------------------------------------

# In the paper example:
# perc = 1 because all distinct city values must be enriched.
# error/enrichment need = 1 because all cities need coordinates.
perc = 1.0
enrichment_need = 1.0


def calculate_strategy(strategy_name, is_pairwise):
    records_enriched = number_of_cities * perc

    if is_pairwise:
        operations = number_of_cities * top_k_candidates
        effectiveness = pairwise_effectiveness
        processing_cost = pairwise_cost_per_comparison

        improvement_cost = operations * pairwise_cost_per_comparison
        latency_sec = operations * pairwise_time_per_comparison
        
        manual_work_min = number_of_countries * manual_minutes_per_country
        assessment_cost = (manual_work_min / 60) * hourly_labour_cost

    else:
        operations = number_of_cities
        effectiveness = reconciliation_effectiveness
        processing_cost = reconciliation_cost_per_lookup

        improvement_cost = operations * top_k_candidates *reconciliation_cost_per_lookup
        latency_sec = operations * reconciliation_time_per_lookup
        

        manual_work_min = 0
        assessment_cost = 0

    time_min = latency_sec / 60
    co2 = time_min * co2_per_minute

    # DQ improvement:
    # Since every city should be enriched, the improvement depends on how many cities
    # the method successfully links to coordinates.
    dq_improvement = number_of_cities * effectiveness

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

# ------------------------------------------------------------
# Main result cards
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# Raw values table
# ------------------------------------------------------------

st.subheader("Raw values")
st.dataframe(df.round(4), use_container_width=True)

# ------------------------------------------------------------
# Bar chart
# ------------------------------------------------------------

st.subheader("Cost comparison")

bar_fig = go.Figure()

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Improvement cost (€)"],
    name="Improvement cost (€)",
    text=df["Improvement cost (€)"].round(2),
    textposition="outside",
    marker_color="#F58518"
))

# bar_fig.add_trace(go.Bar(
#     x=df.index,
#     y=df["Total cost (€)"],
#     name="Total cost (€)",
#     text=df["Total cost (€)"].round(2),
#     textposition="outside",
#     marker_color="#E45756"
# ))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ improvement"],
    name="DQ improvement",
    text=df["DQ improvement"].round(2),
    textposition="outside",
    marker_color="#4C78A8"
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ waste (€)"],
    name="DQ waste (€)",
    text=df["DQ waste (€)"].round(2),
    textposition="outside",
    marker_color="#54A24B"
))

bar_fig.update_layout(
    barmode="group",
    title="Improvement cost, DQ improvement and DQ waste",
    yaxis_title="€",
    height=450
)

st.plotly_chart(bar_fig, use_container_width=True)

# ------------------------------------------------------------
# Spider chart / Trade-off radar chart
# ------------------------------------------------------------

# ------------------------------------------------------------
# Trade-off spider chart
# ------------------------------------------------------------

st.subheader("Trade-off spider diagram")

tradeoff_df = pd.DataFrame(index=df.index)

# Raw values used for the trade-off dimensions
tradeoff_df["Quality score"] = df["DQ improvement"]
tradeoff_df["Cost efficiency"] = df["Improvement cost (€)"]
tradeoff_df["Waste efficiency"] = df["DQ waste (€)"]
tradeoff_df["Time efficiency"] = df["Time (min)"]
tradeoff_df["CO₂ efficiency"] = df["CO₂ (kg)"]
tradeoff_df["Low human work"] = df["Human work (min)"]


def normalize_higher_is_better(value, max_value):
    if max_value == 0:
        return 0
    return value / max_value * 100


def normalize_lower_is_better(value, max_value):
    if max_value == 0:
        return 100
    return (1 - value / max_value) * 100


radar_df = pd.DataFrame(index=tradeoff_df.index)

# Higher is better
radar_df["Quality score"] = tradeoff_df["Quality score"].apply(
    lambda x: normalize_higher_is_better(x, tradeoff_df["Quality score"].max())
)

# Lower is better, therefore inverted
radar_df["Cost efficiency"] = tradeoff_df["Cost efficiency"].apply(
    lambda x: normalize_lower_is_better(x, tradeoff_df["Cost efficiency"].max())
)

radar_df["Waste efficiency"] = tradeoff_df["Waste efficiency"].apply(
    lambda x: normalize_lower_is_better(x, tradeoff_df["Waste efficiency"].max())
)

radar_df["Time efficiency"] = tradeoff_df["Time efficiency"].apply(
    lambda x: normalize_lower_is_better(x, tradeoff_df["Time efficiency"].max())
)

radar_df["CO₂ efficiency"] = tradeoff_df["CO₂ efficiency"].apply(
    lambda x: normalize_lower_is_better(x, tradeoff_df["CO₂ efficiency"].max())
)

radar_df["Low human work"] = tradeoff_df["Low human work"].apply(
    lambda x: normalize_lower_is_better(x, tradeoff_df["Low human work"].max())
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
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),
    showlegend=True,
    title="Normalized trade-off comparison: higher values are better",
    height=550
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Explanation
# ------------------------------------------------------------

with st.expander("Explanation of formulas and assumptions"):
    st.markdown("""
## STRATEGY ASSUMPTIONS

This dashboard compares two approaches for enriching city values with coordinates:

`city name → coordinates`

For example:

`Milano → latitude and longitude`

Both strategies enrich the same number of city values. The difference is how the enrichment is performed.

---

## Pairwise-based approach

Pairwise-based enrichment follows a traditional data integration pipeline.

The user first has to:

- search for external city-coordinate data
- understand and prepare the external dataset
- compare each city with several candidate matches

In this model, each city is compared with the top-k most similar candidates.

Default assumption:

`top-k = 50`

Therefore:

`Operations = number of cities × top-k candidates`

With the default values:

`Operations = 6,419 × 50 = 320,950`

This means pairwise matching performs many comparisons.

---

## Reconciliation-based approach

Reconciliation-based enrichment uses a reconciliation service or API.

Instead of manually comparing each city with many candidates, the method sends the city value to a service or reconciler.

For example:

`city, state → reconciler/API → coordinates`

Conceptually, reconciliation performs one lookup per city.

Therefore:

`Operations = number of cities`

With the default values:

`Operations = 6,419`

This is much fewer than pairwise matching.

However, to stay aligned with the paper's cost values, reconciliation improvement cost is calculated using the same top-k cost basis:

`Improvement cost = number of cities × top-k candidates × cost per lookup`

This means that reconciliation has fewer logical operations, but its cost calculation can still reproduce the values reported in the paper.

---

## CORE FORMULAS

### Records enriched

`Records enriched = number of distinct cities × perc`

In this example:

`perc = 1`

because all city values must be enriched with coordinates.

With the default values:

`Records enriched = 6,419 × 1 = 6,419`

---

### Effectiveness

Effectiveness represents how well the method links city values to the correct coordinates.

In the paper, the quality measures are different:

- Pairwise-based methods use **F1-score**
- Reconciliation-based methods use **Accuracy**

In this dashboard, both are represented as effectiveness percentages to make the comparison easier.

---

### DQ improvement

`DQ improvement = number of cities × effectiveness`

This represents how many city values are successfully enriched.

Example:

`DQ improvement = 6,419 × 0.90 = 5,777.1`

So, with 90% effectiveness, approximately 5,777 city values are successfully linked to coordinates.

Higher DQ improvement is better.

---

### Processing cost

Processing cost represents the cost of one comparison or lookup.

For Pairwise-based methods:

`processing cost = cost per comparison`

For Reconciliation-based methods:

`processing cost = cost per lookup`

To make the value easier to read, the dashboard displays processing cost as:

`Processing cost ×1000`

This follows the same idea as the paper's table, where the cost is shown as:

`c_j,k × 1000`

Example:

If the actual cost per operation is:

`0.000300`

the dashboard displays:

`0.300`

because:

`0.000300 × 1000 = 0.300`

Important:

The `×1000` value is only for display.

The actual improvement cost is still calculated using the unscaled processing cost.

---

### Pairwise improvement cost

For pairwise matching:

`Improvement cost = number of cities × top-k candidates × cost per comparison`

Example:

`Improvement cost = 6,419 × 50 × 0.012125 = 3,891.52`

Pairwise can become expensive because each city is compared with many candidates.

---

### Reconciliation improvement cost

Conceptually, reconciliation performs one lookup per city:

`Operations = number of cities`

However, to reproduce the paper's reported improvement cost values, the dashboard calculates reconciliation improvement cost using:

`Improvement cost = number of cities × top-k candidates × cost per lookup`

Example for a HERE-like method:

`Improvement cost = 6,419 × 50 × 0.000300 = 96.285`

This explains why reconciliation can have:

`Operations = 6,419`

but still have an improvement cost close to:

`96`

---

### Assessment cost

Assessment cost represents manual work before enrichment can happen.

For Pairwise-based methods, this includes searching for, preparing, and assessing external data.

The dashboard calculates assessment cost as:

`Assessment cost = number of countries × manual minutes per country / 60 × labour cost per hour`

Example:

`Assessment cost = 3 × 40 / 60 × €60 = €120`

For Reconciliation-based methods:

`Assessment cost = 0`

because the enrichment is handled by a reconciler or API.

---

### Total cost

`Total cost = improvement cost + assessment cost`

Pairwise methods can have both improvement cost and assessment cost.

Reconciliation-based methods usually have no assessment cost.

---

### DQ waste

`DQ waste = improvement cost × (1 - effectiveness)`

DQ waste represents money spent on enrichment attempts that do not successfully improve the data.

Example:

If:

`Improvement cost = €3,891.52`

and:

`Effectiveness = 87.74% = 0.8774`

then:

`DQ waste = 3,891.52 × (1 - 0.8774)`

`DQ waste ≈ €477`

Lower DQ waste is better.

---

### Time and latency

For Pairwise-based methods:

`Latency = operations × time per comparison`

For Reconciliation-based methods:

`Latency = operations × time per lookup`

The result is converted from seconds to minutes:

`Time in minutes = latency in seconds / 60`

Time and latency are based on logical operations.

---

### CO₂ impact

`CO₂ = processing time × CO₂ per compute minute`

The dashboard assumes that CO₂ emissions are proportional to processing time.

Lower CO₂ is better.

---

### Human work

For Pairwise-based methods:

`Human work = number of countries × manual minutes per country`

For Reconciliation-based methods:

`Human work = 0`

This reflects that pairwise methods require manual data exploration and preparation, while reconciliation-based methods rely on a service or API.

---

## COST COMPARISON CHART

The cost comparison chart shows:

- improvement cost
- DQ improvement
- DQ waste

These metrics show how much the method costs, how much quality improvement it gives, and how much cost is wasted due to imperfect effectiveness.

Assessment cost and total cost are kept in the raw values table for exact comparison.

---

## TRADE-OFF SPIDER DIAGRAM

The spider diagram summarizes the comparison across several dimensions:

- Quality score
- Cost efficiency
- Waste efficiency
- Time efficiency
- CO₂ efficiency
- Low human work

All dimensions are normalized so that:

`Higher values are better`

For metrics where lower is better, the values are inverted.

For example:

`Cost efficiency = 1 - improvement cost / maximum improvement cost`

This means that values farther from the center represent a better outcome.

---

## IMPORTANT MODEL SIMPLIFICATIONS

This dashboard is a simplified model.

The most important simplifications are:

- Pairwise effectiveness and reconciliation effectiveness are shown as percentages, even though the paper uses F1-score for pairwise methods and Accuracy for reconciliation methods.
- Processing cost is displayed as `×1000`, while calculations use the actual unscaled cost.
- Reconciliation has fewer logical operations, but its improvement cost is calculated using the top-k cost basis to match the paper's reported values.
- Time, latency, CO₂, and human work are simplified estimates.

---

## INTERPRETATION

Pairwise-based methods can be useful when no suitable reconciliation API exists, and they can give the user more control.

However, they often require more comparisons, more manual work, higher assessment cost, and higher latency.

Reconciliation-based methods are often more efficient because they use a service or API to resolve entities directly.

They usually require fewer logical operations, less manual work, and no assessment cost.

The best method depends on the balance between quality, cost, waste, time, CO₂, and human involvement.
""")