import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory of dashboard to path to find scripts folder
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(dashboard_dir)
if project_dir not in sys.path:
    sys.path.append(project_dir)

from scripts.rfm_analysis import calculate_rfm

# 1. PAGE SETUP
st.set_page_config(page_title="Retail Pulse Dashboard", layout="wide")

st.title("📊 Retail Profitability Diagnosis")
st.markdown("### Interactive Profit & Loss Analysis")

# 2. LOAD DATA
@st.cache_data
def load_data():
    csv_path = os.path.join(project_dir, 'data', 'superstore_sales.csv')
    df = pd.read_csv(csv_path)
    return df

df = load_data()

# 3. SIDEBAR FILTERS (The "Live" Part)
st.sidebar.header("Filter Data")
region = st.sidebar.multiselect(
    "Select Region:",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

category = st.sidebar.multiselect(
    "Select Category:",
    options=df["Category"].unique(),
    default=df["Category"].unique()
)

# Filter logic
df_selection = df.query(
    "Region == @region & Category == @category"
)

# 4. TABS SETUP
tab1, tab2 = st.tabs(["Profitability Analysis", "RFM Customer Segmentation"])

# 5. TAB 1: Profitability Analysis
with tab1:
    # Profitability KPI metrics
    total_sales = int(df_selection["Sales"].sum())
    total_profit = int(df_selection["Profit"].sum())
    # Handle division by zero if selection is empty or sales is 0
    if total_sales != 0:
        profit_margin = round((total_profit / total_sales) * 100, 1)
    else:
        profit_margin = 0.0

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.subheader("Total Sales")
        st.subheader(f"${total_sales:,}")
    with middle_column:
        st.subheader("Total Profit")
        st.subheader(f"${total_profit:,}")
    with right_column:
        st.subheader("Profit Margin")
        st.subheader(f"{profit_margin}%")

    st.markdown("---")

    # Plotly bar chart: Sales by Product Line
    sales_by_product = (
        df_selection.groupby(by=["Sub-Category"]).sum()[["Sales"]].sort_values(by="Sales")
    )
    fig_product_sales = px.bar(
        sales_by_product,
        x="Sales",
        y=sales_by_product.index,
        orientation="h",
        title="<b>Sales by Product Line</b>",
        color_discrete_sequence=["#0083B8"] * len(sales_by_product),
        template="plotly_white",
    )

    # Plotly scatter plot: Impact of Discount on Profitability
    fig_profit_discount = px.scatter(
        df_selection,
        x="Discount",
        y="Profit",
        color="Category",
        title="<b>Impact of Discount on Profitability</b>",
        template="plotly_white",
        hover_data=["Sub-Category"]
    )

    chart_left, chart_right = st.columns(2)
    chart_left.plotly_chart(fig_product_sales, use_container_width=True)
    chart_right.plotly_chart(fig_profit_discount, use_container_width=True)

# 6. TAB 2: RFM Customer Segmentation
with tab2:
    st.subheader("RFM Customer Segments")
    
    # Warn if selection has missing/malformed critical columns
    has_malformed = (
        df_selection["Customer_ID"].isna().any()
        or df_selection["Order Date"].isna().any()
        or df_selection["Sales"].isna().any()
    ) if not df_selection.empty else False
    
    if has_malformed:
        st.warning("Warning: Selected data contains missing or malformed Customer IDs, Order Dates, or Sales values.")

    rfm_df = calculate_rfm(df_selection)
    
    st.dataframe(rfm_df)
        
    if not rfm_df.empty:
        # Scatter plot of Recency vs Frequency, colored by Segment
        fig_rfm_scatter = px.scatter(
            rfm_df,
            x="Recency",
            y="Frequency",
            color="Segment",
            title="<b>Recency vs Frequency by Segment</b>",
            template="plotly_white"
        )
        
        # Bar chart of customer counts per Segment
        segment_counts = rfm_df['Segment'].value_counts().reset_index()
        segment_counts.columns = ['Segment', 'Customer Count']
        fig_rfm_bar = px.bar(
            segment_counts,
            x="Segment",
            y="Customer Count",
            title="<b>Customer Counts by Segment</b>",
            color="Segment",
            template="plotly_white"
        )
        
        rfm_col1, rfm_col2 = st.columns(2)
        rfm_col1.plotly_chart(fig_rfm_scatter, use_container_width=True)
        rfm_col2.plotly_chart(fig_rfm_bar, use_container_width=True)
    else:
        st.info("No RFM data available for the current selection.")
        
    st.markdown("---")
    st.markdown("### 💡 Actionable Insights")
    st.markdown(
        """
        - **Champions**: Reward them. They are your best customers and will promote your brand.
        - **Loyal Customers**: Keep them happy. Upsell and offer loyalty programs.
        - **At Risk / Can't Lose Them**: Re-engage them with targeted discounts, renewal offers, or surveys to understand why they stopped purchasing.
        - **About to Sleep / Promising**: Send them special promotions or recommendations to wake them up.
        - **Recent / Potential Loyalists**: Provide onboarding sequences or small incentives to encourage a second purchase.
        - **Lost**: Avoid high-cost reactivation campaigns; instead, use low-cost channels or focus on acquiring new customers.
        """
    )

# 7. RAW DATA VIEW
if st.checkbox("Show Raw Data"):
    st.dataframe(df_selection)
