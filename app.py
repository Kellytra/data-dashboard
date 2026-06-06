import streamlit as st

st.set_page_config(page_title="Sustainable Data Preparation", layout="wide")

st.title("Sustainable Data Preparation Dashboard")

st.write("""
This dashboard explores sustainability trade-offs in data preparation.

Each page models one example scenario and compares alternative methods using shared indicators such as cost, CO₂, processing time, latency, DQ waste, and processed amount.
""")

st.subheader("Project information")

st.markdown("""
This dashboard was developed as a spring semester 2026 project by Jenny Nguyen and Kelly Tran, exchange students from Norway at Politecnico di Milano.

The project was supervised by Professor Barbara Pernici at Politecnico di Milano, Milan, Italy.
""")

st.subheader("Reference paper")

st.markdown(
    "The examples in this dashboard are based on the paper "
    "[Sustainable Data Preparation](https://dl.acm.org/doi/full/10.1145/3769120)."
)

st.subheader("How to use the dashboard")

st.markdown("""
- Open an example page to inspect one specific data preparation strategy.
- Use **Cross Example Comparison** to compare the methods across examples.
- Read the explanation sections on each page to see the formulas and assumptions behind the results.
""")

st.subheader("Examples included")

st.markdown("""
1. Progressive Visualization
2. Reconciliation-based Data Enrichment
3. Cleaning on Demand
4. Cleaning and Enrichment of Dynamic Data
5. Data Preparation Pipelines Improvement
6. Cross Example Comparison
""")

