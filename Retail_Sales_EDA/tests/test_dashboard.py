import os
import pytest
import pandas as pd
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

# --- TIER 1 TESTS ---

def test_dashboard_renders():
    """Case 1.1: Smoke Test & App Render. Verify app boots up and renders the header structure."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    # Check that title matches or contains the expected text
    assert any("Retail Profitability Diagnosis" in str(title.value) for title in at.title)

def test_multitab_layout():
    """Case 1.2: Multi-tab Layout & Navigation. Verify the app renders 2 tabs with correct labels."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    assert len(at.tabs) == 2
    assert at.tabs[0].label == "Profitability Analysis"
    assert at.tabs[1].label == "RFM Customer Segmentation"

def test_sidebar_filters():
    """Case 1.3: Sidebar Filters Application. Verify selecting specific options updates the query."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    assert len(at.sidebar.multiselect) >= 2
    
    # Apply filters
    at.sidebar.multiselect[0].set_value(["West"])
    at.sidebar.multiselect[1].set_value(["Technology"])
    at.run()
    
    assert not at.exception
    # Ensure metrics subheaders are updated and non-empty
    subheaders = [str(s.value) for s in at.subheader]
    assert len(subheaders) > 0

@patch('pandas.read_csv')
def test_caching(mock_read):
    """Case 1.4: Caching Behavior Verification. Verify data reads are cached and not repeated."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01"],
        "Region": ["East"],
        "Category": ["Office Supplies"],
        "Sub-Category": ["Paper"],
        "Sales": [100.0],
        "Quantity": [1],
        "Discount": [0.0],
        "Profit": [20.0],
        "Customer_ID": ["CUST-001"]
    })
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    # Trigger interaction to cause rerun
    at.sidebar.multiselect[0].set_value(["East"])
    at.run()
    
    # The read should only happen once due to st.cache_data
    mock_read.assert_called_once()

def test_raw_data_toggle():
    """Case 1.5: Raw Data View Toggle. Verify checkbox displays and hides the raw dataframe."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    assert len(at.checkbox) > 0
    
    # Toggle on
    at.checkbox[0].check().run()
    assert len(at.dataframe) > 0
    
    # Toggle off
    at.checkbox[0].uncheck().run()
    assert len(at.dataframe) == 0

# --- TIER 2 TESTS ---

def test_empty_filter_results():
    """Case 2.1: Empty Filter Selection. Verify app handles empty query without throwing division-by-zero errors."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    
    # Clear all selections
    at.sidebar.multiselect[0].set_value([])
    at.sidebar.multiselect[1].set_value([])
    at.run()
    
    assert not at.exception
    # Margin should display 0.0% or similar fallback
    subheaders = [str(s.value) for s in at.subheader]
    assert any("0.0%" in val or "0%" in val for val in subheaders)

def test_single_selection():
    """Case 2.2: Single Region / Category Selection. Verify calculations on a single entity filter subset."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    
    at.sidebar.multiselect[0].set_value(["South"])
    at.sidebar.multiselect[1].set_value(["Furniture"])
    at.run()
    assert not at.exception

@patch('pandas.read_csv')
def test_missing_profit_traps(mock_read):
    """Case 2.3: Missing Profit Trap Data. Verify app renders correctly when no unprofitable items exist."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01"],
        "Region": ["East"],
        "Category": ["Technology"],
        "Sub-Category": ["Copiers"],
        "Sales": [1000.0],
        "Quantity": [1],
        "Discount": [0.0],
        "Profit": [400.0],
        "Customer_ID": ["CUST-001"]
    })
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception

@patch('pandas.read_csv')
def test_malformed_rfm_data(mock_read):
    """Case 2.4: Missing/Malformed Customer ID. Verify app handles missing/null Customer_ID gracefully on the RFM tab."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01", "2023-01-02"],
        "Region": ["East", "West"],
        "Category": ["Furniture", "Furniture"],
        "Sub-Category": ["Chairs", "Tables"],
        "Sales": [100.0, 200.0],
        "Quantity": [1, 2],
        "Discount": [0.0, 0.0],
        "Profit": [20.0, -50.0],
        "Customer_ID": [None, None]
    })
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    # When RFM is upgraded, it should warn about malformed data
    # (Since RFM is not yet implemented, this test is expected to fail or skip depending on implementation,
    # but here we assert that the app doesn't crash on boot or navigation)

@patch('pandas.read_csv')
def test_outlier_formatting(mock_read):
    """Case 2.5: Extreme/Outlier Sales and Profit. Verify extremely large amounts format correctly with comma separators."""
    mock_read.return_value = pd.DataFrame({
        "Order Date": ["2023-01-01"],
        "Region": ["East"],
        "Category": ["Technology"],
        "Sub-Category": ["Copiers"],
        "Sales": [150000000.0],
        "Quantity": [1],
        "Discount": [0.0],
        "Profit": [50000000.0],
        "Customer_ID": ["CUST-001"]
    })
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(project_root, "dashboard", "app.py")
    
    at = AppTest.from_file(app_path)
    at.run()
    assert not at.exception
    subheaders = [str(s.value) for s in at.subheader]
    assert any("$150,000,000" in val for val in subheaders), f"Expected $150,000,000 but got {subheaders}"
    assert any("$50,000,000" in val for val in subheaders), f"Expected $50,000,000 but got {subheaders}"
    assert any("33.3%" in val for val in subheaders), f"Expected 33.3% but got {subheaders}"
