import os
import re
import pytest
import pandas as pd
import numpy as np

def get_generate_sales_data():
    """Helper to dynamically import generate_sales_data to avoid collection-time errors."""
    try:
        # Add project root to sys.path just in case
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from scripts.generate_data import generate_sales_data
        return generate_sales_data
    except ImportError as e:
        pytest.fail(f"Could not import generate_sales_data from scripts.generate_data: {e}. The codebase may not be upgraded yet.")

# --- TIER 1 TESTS ---

def test_exists():
    """Tier 1: Verify file output is created (simulated by function execution)."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=10)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 10

def test_columns():
    """Tier 1: Verify correct schema and columns exist."""
    generate_sales_data = get_generate_sales_data()
    expected_cols = ['Order Date', 'Region', 'Category', 'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit', 'Customer_ID']
    df = generate_sales_data(rows=5)
    assert list(df.columns) == expected_cols

def test_customer_id_format():
    """Tier 1: Verify Customer_ID column details."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=20)
    assert df['Customer_ID'].isnull().sum() == 0
    # Customer IDs should match pattern CUST-XXXX or similar (e.g., CUST- followed by digits)
    pattern = re.compile(r'^CUST-\d+$')
    for cid in df['Customer_ID']:
        assert pattern.match(str(cid)), f"Customer_ID '{cid}' does not match expected pattern CUST-XXXX"

def test_repeat_buyers():
    """Tier 1: Verify that duplicate Customer_IDs are generated."""
    generate_sales_data = get_generate_sales_data()
    # With 1000 rows and 50 unique customers, there should be repeat buyers
    df = generate_sales_data(rows=1000, num_customers=50)
    unique_custs = df['Customer_ID'].nunique()
    assert unique_custs <= 50
    assert df['Customer_ID'].duplicated().any()
    assert df['Customer_ID'].value_counts().max() > 1

def test_reproducibility():
    """Tier 1: Verify reproducibility with matching seeds."""
    generate_sales_data = get_generate_sales_data()
    df1 = generate_sales_data(rows=100, seed=42)
    df2 = generate_sales_data(rows=100, seed=42)
    pd.testing.assert_frame_equal(df1, df2)

# --- TIER 2 TESTS ---

def test_empty_config():
    """Tier 2: Test boundary condition with rows=0."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=0)
    assert len(df) == 0
    expected_cols = ['Order Date', 'Region', 'Category', 'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit', 'Customer_ID']
    assert list(df.columns) == expected_cols

def test_single_row():
    """Tier 2: Test boundary condition with rows=1."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=1)
    assert len(df) == 1
    assert not df.isnull().values.any()

def test_extreme_profit_loss():
    """Tier 2: Test profit trap calculations (Tables/Bookcases vs Copiers)."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=500, seed=123)
    
    # Tables and Bookcases
    loss_items = df[df['Sub-Category'].isin(['Tables', 'Bookcases'])]
    for idx, row in loss_items.iterrows():
        assert row['Profit'] < 0, f"Expected loss for {row['Sub-Category']} but got {row['Profit']}"
        
    # Copiers
    copiers = df[df['Sub-Category'] == 'Copiers']
    for idx, row in copiers.iterrows():
        assert row['Profit'] > 0
        expected_profit = round(row['Sales'] * 0.4, 2)
        assert abs(row['Profit'] - expected_profit) < 0.01

def test_zero_discount():
    """Tier 2: Test zero discount profitability rules."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=500, seed=123)
    zero_disc = df[df['Discount'] == 0.0]
    
    for idx, row in zero_disc.iterrows():
        if row['Sub-Category'] == 'Copiers':
            expected_profit = round(row['Sales'] * 0.4, 2)
        else:
            expected_profit = round(row['Sales'] * 0.2, 2)
        assert abs(row['Profit'] - expected_profit) < 0.01

def test_single_buyer():
    """Tier 2: Test generator when only 1 customer is configured."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=100, num_customers=1)
    assert df['Customer_ID'].nunique() == 1
    assert len(df) == 100
