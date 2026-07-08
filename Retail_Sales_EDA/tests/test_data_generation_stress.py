import pytest
import pandas as pd
import numpy as np
import os
import re

def get_generate_sales_data():
    """Helper to dynamically import generate_sales_data to avoid import issues."""
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from scripts.generate_data import generate_sales_data
    return generate_sales_data

def test_zero_rows_boundary():
    """Verify that requesting 0 rows returns an empty DataFrame with the correct schema."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=0)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    expected_cols = ['Order Date', 'Region', 'Category', 'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit', 'Customer_ID']
    assert list(df.columns) == expected_cols

def test_large_rows_boundary():
    """Verify that requesting a large number of rows (e.g., 20,000) generates the correct number of rows without crash."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=20000, num_customers=100)
    assert len(df) == 20000
    assert df['Customer_ID'].nunique() <= 100

def test_num_customers_zero_crash():
    """Verify that num_customers = 0 raises ValueError when rows > 0 due to sampling from an empty pool."""
    generate_sales_data = get_generate_sales_data()
    with pytest.raises(ValueError, match="a must be non-empty|cannot select an item from an empty sequence"):
        generate_sales_data(rows=10, num_customers=0)

def test_customer_distribution_uniformity():
    """Verify that customer ID selection yields a highly uniform distribution (low variance) when pools are equal size."""
    generate_sales_data = get_generate_sales_data()
    # 20,000 rows, 20 customers (5 per region)
    df = generate_sales_data(rows=20000, num_customers=20, seed=42)
    counts = df['Customer_ID'].value_counts()
    
    # Expected count is 1000 per customer
    mean_count = counts.mean()
    std_count = counts.std()
    
    assert mean_count == 1000
    # Standard deviation should be small (e.g., < 10% of mean, i.e., < 100)
    assert std_count < 100, f"Customer purchase counts standard deviation is too high: {std_count}"

def test_customer_distribution_skew():
    """Verify that if num_customers is not a multiple of 4, the selection probability is skewed (non-uniform)."""
    generate_sales_data = get_generate_sales_data()
    # 5 customers: East (2), West (1), Central (1), South (1)
    df = generate_sales_data(rows=20000, num_customers=5, seed=42)
    counts = df['Customer_ID'].value_counts()
    
    # Customers in smaller pools (West, Central, South) are chosen twice as often as East
    # CUST-1001 (East), CUST-1005 (East)
    # CUST-1002 (West), CUST-1003 (Central), CUST-1004 (South)
    cust_east = ['CUST-1001', 'CUST-1005']
    cust_others = ['CUST-1002', 'CUST-1003', 'CUST-1004']
    
    east_avg = np.mean([counts[c] for c in cust_east])
    others_avg = np.mean([counts[c] for c in cust_others])
    
    # others_avg should be approximately twice east_avg
    ratio = others_avg / east_avg
    assert 1.8 < ratio < 2.2, f"Skew ratio is not ~2.0: {ratio}"

def test_customer_region_isolation():
    """Verify that customer IDs are strictly isolated to their assigned region when num_customers >= 4."""
    generate_sales_data = get_generate_sales_data()
    df = generate_sales_data(rows=1000, num_customers=8, seed=42)
    
    # Group by Customer_ID and get set of unique regions they bought in
    customer_regions = df.groupby('Customer_ID')['Region'].nunique()
    
    # Each customer should only purchase in exactly 1 region
    for cid, num_regions in customer_regions.items():
        assert num_regions == 1, f"Customer {cid} purchased in {num_regions} regions instead of 1."

def test_customer_fallback_cross_region():
    """Verify that if num_customers < 4, fallback triggers and customer IDs purchase in multiple regions."""
    generate_sales_data = get_generate_sales_data()
    # num_customers = 3 (East: CUST-1001, West: CUST-1002, Central: CUST-1003, South: empty fallback)
    df = generate_sales_data(rows=1000, num_customers=3, seed=42)
    
    # Since South region's pool was fallback-assigned to all customer IDs,
    # every customer should have purchased in at least 2 regions (their home region + South).
    customer_regions = df.groupby('Customer_ID')['Region'].nunique()
    
    for cid, num_regions in customer_regions.items():
        assert num_regions > 1, f"Customer {cid} did not shop cross-region despite fallback."
