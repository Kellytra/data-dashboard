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
    y=df["Assessment cost (€)"],
    name="Assessment cost (€)",
    marker_color="#4C78A8"
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Improvement cost (€)"],
    name="Improvement cost (€)",
    marker_color="#F58518"
))

bar_fig.add_trace(go.Bar(
    x=df.index,
    y=df["DQ waste (€)"],
    name="DQ waste (€)",
    marker_color="#54A24B"
))

bar_fig.update_layout(
    barmode="group",
    title="Assessment cost, improvement cost and DQ waste",
    yaxis_title="€",
    height=450
)

st.plotly_chart(bar_fig, use_container_width=True)

# ------------------------------------------------------------
# Operations chart
# ------------------------------------------------------------

st.subheader("Operations comparison")

operations_fig = go.Figure()

operations_fig.add_trace(go.Bar(
    x=df.index,
    y=df["Operations"],
    name="Operations",
    marker_color="#B279A2"
))

operations_fig.update_layout(
    title="Number of operations required",
    yaxis_title="Operations",
    height=400
)

st.plotly_chart(operations_fig, use_container_width=True)

# ------------------------------------------------------------
# Spider chart
# ------------------------------------------------------------

st.subheader("Spider diagram")

spider_df = pd.DataFrame(index=df.index)

spider_df["Total cost"] = df["Total cost (€)"]
spider_df["Improvement cost"] = df["Improvement cost (€)"]
spider_df["DQ waste"] = df["DQ waste (€)"]
spider_df["Time"] = df["Time (min)"]
spider_df["CO₂"] = df["CO₂ (kg)"]
spider_df["Latency"] = df["Latency to result (sec)"]
spider_df["Human work"] = df["Human work (min)"]
spider_df["Operations"] = df["Operations"]
spider_df["DQ improvement"] = df["DQ improvement"]


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
    height=550
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Explanation
# ------------------------------------------------------------

with st.expander("Explanation of formulas and assumptions"):
    st.markdown("""
## STRATEGY ASSUMPTIONS

This example compares two approaches for linking city names to coordinates.

The task is:

`city name → coordinates`

For example:

`Milano → latitude and longitude`

The dashboard is inspired by Table 3 in the paper and can be used to compare pairwise-based and reconciliation-based enrichment methods.

---

## Pairwise-based

Pairwise-based enrichment follows a traditional data integration pipeline.

The user first has to:

- search for external city-coordinate data online
- understand the data structure
- download or prepare the external dataset
- compare each city with several candidate matches

In this model, each city is compared with the top-k most similar candidates.

Default assumption:

`top-k = 50`

Therefore:

`Operations = number of cities × top-k candidates`

This means pairwise matching performs many comparisons.

---

## Reconciliation-based

Reconciliation-based enrichment uses a reconciliation service or API.

Instead of comparing each city with many candidates manually, the method sends the city name to a service or reconciler.

For example:

`city, state → reconciler/API → coordinates`

Therefore:

`Operations = number of cities`

This means reconciliation performs one lookup per city.

However, in order to reproduce the cost values from Table 3, the dashboard uses the same cost basis as the paper when calculating improvement cost.

This means that:

`Operations` shows the logical number of lookups performed by the reconciliation method.

`Cost basis` is used to reproduce the cost calculation from Table 3.

For reconciliation:

`Operations = number of cities`

but the improvement cost is calculated using:

`Improvement cost = number of cities × top-k candidates × cost per lookup`

This is why the reconciliation method can show fewer operations, while still matching the improvement cost values reported in the paper.

---

## CORE FORMULAS

### Records enriched

`Records enriched = number of distinct cities × perc`

In this example:

`perc = 1`

because all city values must be enriched with coordinates.

With the paper's values:

`Records enriched = 6,419`

---

### Pairwise operations

`Operations = number of cities × top-k candidates`

With the default values:

`Operations = 6,419 × 50 = 320,950`

This gives many comparisons.

---

### Reconciliation operations

`Operations = number of cities`

With the default values:

`Operations = 6,419`

This is much fewer than pairwise matching.

---

### Effectiveness

Effectiveness represents the quality of the selected method.

In the paper, the effectiveness values are measured differently:

- Pairwise-based methods use **F1-score**
- Reconciliation-based methods use **Accuracy**

In the dashboard, these values are represented as effectiveness percentages.

For example:

`p = 0.8774` is shown approximately as `87.74%`

If the slider only allows whole percentages, small differences in DQ waste may occur because of rounding.

---

### DQ improvement

`DQ improvement = number of cities × effectiveness`

This represents how many city values are successfully enriched.

For example, if there are 6,419 cities and the method has 90% effectiveness:

`DQ improvement = 6,419 × 0.90`

---

### Processing cost

Processing cost represents the cost per comparison or lookup.

To make the value easier to read, the dashboard displays it as:

`Processing cost ×1000`

This follows the same idea as Table 3, where the cost column is shown as:

`c_j,k × 1000`

For example, if the actual cost per operation is:

`0.000300`

the dashboard displays:

`0.300`

because:

`0.000300 × 1000 = 0.300`

Important:

The `×1000` value is only for display.

The actual improvement cost is still calculated using the unscaled cost.

---

### Pairwise improvement cost

For pairwise matching:

`Improvement cost = number of cities × top-k candidates × cost per comparison`

With the default structure:

`Improvement cost = 6,419 × 50 × cost per comparison`

Pairwise matching is more expensive because each city is compared with many candidates.

---

### Reconciliation improvement cost

Conceptually, reconciliation performs one lookup per city:

`Operations = number of cities`

However, to reproduce the improvement cost values from Table 3, the dashboard calculates reconciliation improvement cost using the same cost basis as the table:

`Improvement cost = number of cities × top-k candidates × cost per lookup`

For example, for HERE:

`6,419 × 50 × 0.000300 = 96.285`

This matches the improvement cost of approximately `96` shown in Table 3.

This is a modelling choice made to stay aligned with the paper's reported values.

---

### Assessment cost

For pairwise matching, the user must search for and assess external data first.

This includes manual work such as:

- searching for city-coordinate data
- selecting relevant sources
- customizing queries
- assessing whether the data is suitable for matching

The dashboard calculates assessment cost as:

`Assessment cost = number of countries × manual minutes per country / 60 × labour cost per hour`

To reproduce Table 3, the default values can be set to:

`3 countries × 60 minutes / 60 × €40 = €120`

For reconciliation-based methods:

`Assessment cost = 0`

because the enrichment is mediated by the reconciler or API.

---

### Total cost

`Total cost = improvement cost + assessment cost`

Pairwise methods usually have both improvement cost and assessment cost.

Reconciliation-based methods usually have improvement cost, but no assessment cost.

---

### DQ waste

`DQ waste = improvement cost × (1 - effectiveness)`

This represents money spent on enrichment attempts that do not successfully improve the data.

A lower effectiveness gives higher waste.

A higher improvement cost also increases waste.

---

### Time

For pairwise matching:

`Time = operations × time per comparison`

For reconciliation:

`Time = operations × time per lookup`

The result is converted from seconds to minutes.

In this dashboard, time is based on logical operations, not the Table 3 cost basis.

This means reconciliation may have fewer operations and lower latency, even when its improvement cost is calculated using the paper's cost basis.

---

### CO₂

`CO₂ = processing time × CO₂ per compute minute`

CO₂ emissions are assumed to be proportional to processing time.

---

## USER AND SYSTEM TRADE-OFFS

### Pairwise-based

Advantages:

- flexible
- gives the user more control
- can be used when no reconciliation API exists

Disadvantages:

- many comparisons
- higher processing cost
- more manual assessment work
- higher latency
- more CO₂ from compute time

---

### Reconciliation-based

Advantages:

- simpler for the user
- fewer logical operations
- lower latency
- less manual work
- can be cheaper when a good API or reconciler is available

Disadvantages:

- depends on an external API or reconciler
- may not exist for every enrichment task
- can give less control over the matching process

---

## MODEL SIMPLIFICATIONS

The dashboard is a simplified reproduction of the paper's comparison.

The most important simplifications are:

- Effectiveness is shown as a percentage, while the paper uses F1-score for pairwise methods and Accuracy for reconciliation methods.
- Processing cost is displayed as `×1000`, but calculations use the actual unscaled cost.
- Reconciliation has fewer logical operations, but its improvement cost is calculated with the Table 3 cost basis in order to reproduce the reported paper values.
- Time, latency, CO₂, and human work are simplified estimates and are not directly reported in Table 3.

---

## SPIDER DIAGRAM INTERPRETATION

The spider diagram is not inverted.

Values farther from the center are higher.

This means:

- higher DQ improvement is good
- higher cost is bad
- higher CO₂ is bad
- higher latency is bad
- higher human work is bad
- higher operations is bad

Therefore, the diagram shows relative differences, not a direct "better or worse" score.
""")