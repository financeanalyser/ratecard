
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Rate Card Analyser", layout="wide")
st.title("📊 Rate Card Revenue & Margin Uplift Analyser")

# Load the dataset
@st.cache_data
def load_data():
    df = pd.read_excel("rate_card_data.xlsx")
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("🔧 Uplift Parameters")
branches = df["Branch"].unique()
capabilities = df["Capability"].unique()
teams = df["Department / Team"].unique()
jobs = df["Job Title"].unique()

selected_branch = st.sidebar.multiselect("Branch", branches, default=branches)
selected_capability = st.sidebar.multiselect("Capability", capabilities, default=capabilities)
selected_team = st.sidebar.multiselect("Department / Team", teams, default=teams)
selected_job = st.sidebar.multiselect("Job Title", jobs, default=jobs)

uplift_pct = st.sidebar.number_input("Rate Uplift (%)", min_value=0.0, max_value=100.0, value=5.0)
effective_month = st.sidebar.selectbox("Effective From Month", [col for col in df.columns if ".2" in str(col)])

# Filter dataset
mask = (
    df["Branch"].isin(selected_branch) &
    df["Capability"].isin(selected_capability) &
    df["Department / Team"].isin(selected_team) &
    df["Job Title"].isin(selected_job)
)

# Split data
df_base = df.copy()
df_affected = df[mask].copy()
df_unaffected = df[~mask].copy()

# Apply uplift to affected rows from effective month onward
start_index = df.columns.get_loc(effective_month)
revenue_cols = df.columns[start_index:]

for col in revenue_cols:
    uplift_factor = 1 + uplift_pct / 100
    df_affected[col] = df_affected[col] * uplift_factor

# Merge back for full comparison
df_uplifted = pd.concat([df_affected, df_unaffected], ignore_index=True)

# Revenue Summary
original_total = df_base[revenue_cols].sum().sum()
uplifted_total = df_uplifted[revenue_cols].sum().sum()
incremental = uplifted_total - original_total

# Margin Calculations
cost_rate_col = "Cost rate Daily"
rate_col = "Charge Rate Daily"

# Use average monthly uplifted margin
df_affected_margin = df_affected.copy()
df_affected_margin["New Rate"] = df_affected_margin[rate_col] * uplift_factor
df_affected_margin["New Margin %"] = (
    (df_affected_margin["New Rate"] - df_affected_margin[cost_rate_col]) / df_affected_margin["New Rate"]
) * 100

avg_margin = df_affected_margin["New Margin %"].mean()

# Output Section
st.subheader("📈 Summary")
st.metric("Original Revenue (Post Month)", f"${original_total:,.0f}")
st.metric("Uplifted Revenue", f"${uplifted_total:,.0f}", delta=f"${incremental:,.0f}")
st.metric("Avg. New Margin % (Affected Roles)", f"{avg_margin:.2f}%")

# Monthly Revenue Breakdown
st.subheader("🗓️ Monthly Revenue Comparison")
monthly_comparison = pd.DataFrame({
    "Month": revenue_cols,
    "Original": df_base[revenue_cols].sum().values,
    "Uplifted": df_uplifted[revenue_cols].sum().values
})
monthly_comparison["Delta"] = monthly_comparison["Uplifted"] - monthly_comparison["Original"]
st.dataframe(monthly_comparison.style.format({"Original": "$,.0f", "Uplifted": "$,.0f", "Delta": "$,.0f"}))

# Detailed Breakdown Table
st.subheader("📋 Detailed Uplifted Revenue by Role")
display_cols = ["Branch", "Capability", "Department / Team", "Job Title"] + list(revenue_cols)
st.dataframe(df_uplifted[display_cols])
