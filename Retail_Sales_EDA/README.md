# 📊 Retail Sales Exploratory Data Analysis + RFM Customer Segmentation

## Overview
An interactive, multi-tab analytics dashboard built with **Streamlit** and **Plotly**. It combines profitability diagnosis with advanced **RFM (Recency, Frequency, Monetary) Customer Segmentation** to answer both *"where are we losing money?"* and *"who are our best and worst customers?"*

## Key Features

### Tab 1: Profitability Diagnosis
- **KPI Cards** — Total Sales, Total Profit, Profit Margin
- **Sales by Product Line** — Horizontal bar chart revealing top/bottom performers
- **Discount vs. Profit Scatter** — Demonstrates how heavy discounting destroys margins
- **Sidebar Filters** — Region & Category multi-select filters that update all charts in real-time

### Tab 2: RFM Customer Segmentation
- **RFM Table** — Every customer scored on Recency, Frequency, and Monetary value (1-5 scale)
- **Recency vs. Frequency Scatter Plot** — Color-coded by segment to visualize customer health
- **Segment Distribution Bar Chart** — Counts of Champions, At Risk, Lost, etc.
- **Actionable Insights** — Business recommendations per segment

### Customer Segments
| Segment | Description |
|---------|-------------|
| **Champions** | Bought recently, buy often, spend the most |
| **Loyal Customers** | Frequent buyers, responsive to promotions |
| **At Risk** | Were big spenders, but haven't returned in a while |
| **Can't Lose Them** | Biggest purchases, but gone for a long time |
| **Lost** | Lowest recency, frequency, and monetary scores |
| **Potential Loyalists** | Recent + decent spend, need nurturing |
| **Recent Customers** | Just arrived, haven't bought often yet |
| **Promising** | Recent but low spenders |
| **Customers Needing Attention** | Above average but slipping |
| **About to Sleep** | Below average — will lose them if not reactivated |

## Project Structure

```
02_Retail_Sales_EDA/
├── data/
│   ├── superstore_sales.csv         # Generated sales data with Customer_IDs
│   └── rfm_customer_segments.csv    # RFM output (auto-generated)
├── scripts/
│   ├── generate_data.py             # Synthetic data generator (200 customers, repeat buyers)
│   ├── rfm_analysis.py              # RFM engine (calculate, score, segment)
│   └── analysis_eda.py              # Static 4-panel matplotlib analysis
├── dashboard/
│   └── app.py                       # Streamlit multi-tab dashboard
├── reports/
│   └── executive_dashboard.png      # Saved static dashboard image
└── README.md
```

## Run

```bash
# 1. Generate fresh data (optional — data is already included)
python scripts/generate_data.py

# 2. Generate RFM segments (optional — the dashboard computes them on-the-fly too)
python scripts/rfm_analysis.py

# 3. Launch the interactive dashboard
cd dashboard
streamlit run app.py
```

## Tech Stack
Python, Pandas, NumPy, Plotly, Streamlit, Matplotlib, Seaborn
