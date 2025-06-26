
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Rate Card Analyser", layout="wide")
st.title("📊 Rate Card Revenue & Margin Uplift Analyser")

# Load the dataset
@st.cache_data
def load_data():
    df = pd.read_excel("rate_card_data.xlsx")
    df.columns = df.columns.str.strip()
    df = df[~df["Job Title"].str.contains("total", case=False, na=False)]
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

uplift_type = st.sidebar.radio("Choose uplift type", ["% Increase", "$ Increase"])
if uplift_type == "% Increase":
    uplift_value = st.sidebar.number_input("Rate Uplift (%)", min_value=0.0, max_value=100.0, value=5.0)
else:
    uplift_value = st.sidebar.number_input("Uplift ($ per day)", min_value=0.0, value=50.0)

effective_month = st.sidebar.selectbox("Effective From Month", [col for col in df.columns if ".2" in str(col)])

# Filter dataset
mask = (
    df["Branch"].isin(selected_branch) &
    df["Capability"].isin(selected_capability) &
    df["Department / Team"].isin(selected_team) &
    df["Job Title"].isin(selected_job)
)

df_base = df.copy()
df_affected = df[mask].copy()
df_unaffected = df[~mask].copy()

# Apply uplift
start_index = df.columns.get_loc(effective_month)
revenue_cols = df.columns[start_index:]

for col in revenue_cols:
    if uplift_type == "% Increase":
        uplift_factor = 1 + uplift_value / 100
        df_affected[col] = df_affected[col] * uplift_factor
    else:
        uplift_daily = uplift_value
        # Adjust based on cost per day uplift
        daily_rate_col = "Charge Rate Daily"
        billable_days = (df_affected[col] / df_affected[daily_rate_col]).fillna(0)
        df_affected[col] = (df_affected[daily_rate_col] + uplift_daily) * billable_days

# Merge uplifted data
df_uplifted = pd.concat([df_affected, df_unaffected], ignore_index=True)

# Revenue Summary
original_total = df_base[revenue_cols].sum().sum()
uplifted_total = df_uplifted[revenue_cols].sum().sum()
incremental = uplifted_total - original_total

# Margin Calculation
cost_rate_col = "Cost rate Daily"
rate_col = "Charge Rate Daily"

df_affected_margin = df_affected.copy()
if uplift_type == "% Increase":
    new_rate = df_affected_margin[rate_col] * (1 + uplift_value / 100)
else:
    new_rate = df_affected_margin[rate_col] + uplift_value

df_affected_margin["New Margin %"] = ((new_rate - df_affected_margin[cost_rate_col]) / new_rate) * 100
avg_margin = df_affected_margin["New Margin %"].mean()

# Summary Output
st.subheader("📈 Summary")
st.metric("Original Revenue (Post Month)", f"${original_total:,.0f}")
st.metric("Uplifted Revenue", f"${uplifted_total:,.0f}", delta=f"${incremental:,.0f}")
st.metric("Avg. New Margin % (Affected Roles)", f"{avg_margin:.2f}%")

# Monthly Revenue Table
st.subheader("🗓️ Monthly Revenue Comparison")
monthly_comparison = pd.DataFrame({
    "Month": revenue_cols,
    "Original": df_base[revenue_cols].sum().values,
    "Uplifted": df_uplifted[revenue_cols].sum().values
})
monthly_comparison["Delta"] = monthly_comparison["Uplifted"] - monthly_comparison["Original"]
st.dataframe(monthly_comparison.style.format({
    "Original": "$,.0f",
    "Uplifted": "$,.0f",
    "Delta": "$,.0f"
}))

# Detailed Role Table
st.subheader("📋 Detailed Uplifted Revenue by Role")
display_cols = ["Branch", "Capability", "Department / Team", "Job Title"] + list(revenue_cols)
st.dataframe(df_uplifted[display_cols].style.format({
    col: "$,.0f" for col in revenue_cols
}))
