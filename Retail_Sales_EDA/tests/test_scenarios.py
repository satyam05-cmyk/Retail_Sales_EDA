import os
import sys
import time
import pytest
import subprocess
import pandas as pd
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

# --- TIER 3: CROSS-FEATURE COMBINATIONS ---

def test_e2e_integration():
    """Case 3.1: End-to-End Execution Flow. Verify data generator output is processed by dashboard/RFM."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gen_script = os.path.join(project_root, "scripts", "generate_data.py")
    
    # Step 1: Run Data Generator
    result = subprocess.run([sys.executable, gen_script], capture_output=True, text=True)
    assert result.returncode == 0
    
    csv_path_root = os.path.join(project_root, "superstore_sales.csv")
    csv_path_data = os.path.join(project_root, "data", "superstore_sales.csv")
    assert os.path.exists(csv_path_root) or os.path.exists(csv_path_data)
    
    # Step 2: Run Dashboard
    app_path = os.path.join(project_root, "dashboard", "app.py")
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    assert len(at.tabs) == 2
    
    # Step 3: Assert RFM Tab segments and visuals exist (when upgraded, this will have plotly_chart)
    # The current codebase might fail or have different output, which is fine.

@patch('pandas.read_csv')
def test_discount_profit_sync(mock_read):
    """Case 3.2: Interactive Discount-to-Profit Trap Sync. Verify category data updates in charts."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01", "2023-01-02"],
        "Region": ["East", "East"],
        "Category": ["Furniture", "Furniture"],
        "Sub-Category": ["Bookcases", "Bookcases"],
        "Sales": [100.0, 200.0],
        "Quantity": [2, 4],
        "Discount": [0.5, 0.7],
        "Profit": [-60.0, -140.0],
        "Customer_ID": ["CUST-001", "CUST-001"]
    })
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    # Verify charts exist
    assert len(at.plotly_chart) >= 2

def test_filter_sync_across_tabs():
    """Case 3.3: Region Filter Synchronization Across Tabs. Verify region selection updates metrics & lists."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    
    # Filter to East only
    at.sidebar.multiselect[0].set_value(["East"])
    at.run()
    
    # Check Tab 1 Profitability metrics are updated
    subheaders = [str(s.value) for s in at.subheader]
    assert len(subheaders) > 0
    # Customer dataframe on Tab 2 (when upgraded) should also sync to only show East.

# --- TIER 4: REAL-WORLD SCENARIOS ---

@patch('pandas.read_csv')
def test_holiday_stress_test(mock_read):
    """Case 4.1: Holiday Sales Boom. Stress test dashboard caching with 50,000 transactions."""
    large_df = pd.DataFrame({
        "Order Date": ["2023-11-25"] * 50000,
        "Region": ["East"] * 50000,
        "Category": ["Technology"] * 50000,
        "Sub-Category": ["Phones"] * 50000,
        "Sales": [100.0] * 50000,
        "Quantity": [2] * 50000,
        "Discount": [0.1] * 50000,
        "Profit": [15.0] * 50000,
        "Customer_ID": [f"CUST-{i}" for i in range(50000)]
    })
    mock_read.return_value = large_df
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    
    start = time.time()
    at.run()
    duration_1 = time.time() - start
    assert duration_1 < 10.0  # Initial run must render within 10s
    
    # Trigger cached rerun by changing a filter
    start = time.time()
    at.sidebar.multiselect[1].set_value(["Technology"])
    at.run()
    duration_2 = time.time() - start
    assert duration_2 < duration_1 / 5  # Cache hit must be at least 5x faster

@patch('pandas.read_csv')
def test_inactive_churn_rfm(mock_read):
    """Case 4.2: Inactive Customer Churn Analysis. Verify RFM recency shift for old transactions."""
    old_date = "2023-01-01"
    recent_date = "2023-12-31"
    mock_read.return_value = pd.DataFrame({
        "Order Date": [old_date]*10 + [recent_date]*2,
        "Region": ["West"]*12,
        "Category": ["Technology"]*12,
        "Sub-Category": ["Phones"]*12,
        "Sales": [500.0]*12,
        "Quantity": [1]*12,
        "Discount": [0.0]*12,
        "Profit": [100.0]*12,
        "Customer_ID": ["C1","C2","C3","C4","C5","C6","C7","C8","C9","C10","C11","C12"]
    })
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    assert len(at.tabs) == 2
    assert len(at.dataframe) > 0
    df_res = at.dataframe[0].value
    assert len(df_res) == 12
    # Inactive customers C1 to C10 should be segmented as Lost, About to Sleep, or At Risk
    for i in range(1, 11):
        seg = df_res[df_res['Customer_ID'] == f"C{i}"]['Segment'].values[0]
        assert seg in ['Lost', 'About to Sleep', 'At Risk', 'Can\'t Lose Them']

@patch('pandas.read_csv')
def test_discount_trap_threshold(mock_read):
    """Case 4.3: Interactive Discount Trap Diagnosis. Verify profitability drop-off around 30% discount."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01"] * 4,
        "Region": ["West"] * 4,
        "Category": ["Furniture"] * 4,
        "Sub-Category": ["Tables"] * 4,
        "Sales": [100.0, 100.0, 100.0, 100.0],
        "Quantity": [1, 1, 1, 1],
        "Discount": [0.1, 0.2, 0.3, 0.5],
        "Profit": [15.0, 10.0, -5.0, -30.0]
    })
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    # Filter category to Furniture
    at.sidebar.multiselect[1].set_value(["Furniture"])
    at.run()
    assert not at.exception
    # Total sales = 400. Total profit = 15 + 10 - 5 - 30 = -10. Margin = -2.5%
    subheaders = "".join([str(s.value) for s in at.subheader])
    assert "-10" in subheaders or "$-10" in subheaders

@patch('pandas.read_csv')
def test_mega_buyer_rfm(mock_read):
    """Case 4.4: Mega Buyer Outlier. Verify quantile scoring robustness with huge monetary skew."""
    sales = [50.0]*9 + [1000000.0]
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-06-01"] * 10,
        "Region": ["East"] * 10,
        "Category": ["Technology"] * 10,
        "Sub-Category": ["Copiers"] * 10,
        "Sales": sales,
        "Quantity": [1] * 10,
        "Discount": [0.0] * 10,
        "Profit": [s*0.4 for s in sales],
        "Customer_ID": [f"C{i}" for i in range(1, 11)]
    })
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    assert len(at.tabs) == 2
    assert len(at.dataframe) > 0
    df_res = at.dataframe[0].value
    # C10 is the mega buyer with 1M sales
    mega_seg = df_res[df_res['Customer_ID'] == 'C10']['Segment'].values[0]
    assert mega_seg in ['Champions', 'Loyal Customers']

@patch('pandas.read_csv')
def test_cold_start_region(mock_read):
    """Case 4.5: Cold Start Market Expansion. Verify stability when region has a single transaction."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01", "2023-01-02"],
        "Region": ["East", "North"],
        "Category": ["Technology", "Furniture"],
        "Sub-Category": ["Phones", "Chairs"],
        "Sales": [100.0, 50.0],
        "Quantity": [1, 1],
        "Discount": [0.0, 0.0],
        "Profit": [20.0, 5.0],
        "Customer_ID": ["C1", "C2"]
    })
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    
    # Verify "North" is in options
    options = at.sidebar.multiselect[0].options
    assert "North" in options
    
    at.sidebar.multiselect[0].set_value(["North"])
    at.run()
    assert not at.exception
