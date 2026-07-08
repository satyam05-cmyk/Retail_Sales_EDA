import os
import sys
import pytest
import pandas as pd
import numpy as np
import subprocess

def get_calculate_rfm():
    """Helper to dynamically import calculate_rfm to avoid collection-time errors."""
    try:
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from scripts.rfm_analysis import calculate_rfm
        return calculate_rfm
    except ImportError as e:
        pytest.fail(f"Could not import calculate_rfm from scripts.rfm_analysis: {e}. The codebase may not be upgraded yet.")

# --- TIER 1 TESTS ---

def test_cli_execution():
    """Case 1.1: Verify that the RFM engine script can be run directly from the CLI."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(project_root, "scripts", "rfm_analysis.py")
    
    # Ensure script exists
    if not os.path.exists(script_path):
        pytest.fail(f"rfm_analysis.py not found at {script_path}")
        
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with code {result.returncode}. stderr: {result.stderr}"
    assert "SUCCESS" in result.stdout or "SUCCESS" in result.stderr

def test_output_csv_generation():
    """Case 1.2: Verify that the RFM analysis script produces a valid output CSV with all required columns."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_csv = os.path.join(project_root, "data", "rfm_customer_segments.csv")
    
    # Run the script to generate file
    script_path = os.path.join(project_root, "scripts", "rfm_analysis.py")
    subprocess.run([sys.executable, script_path], capture_output=True)
    
    assert os.path.exists(output_csv), f"Output CSV not found at {output_csv}"
    assert os.path.getsize(output_csv) > 0, "Output CSV is empty"
    
    df = pd.read_csv(output_csv)
    expected_cols = ['Customer_ID', 'Recency', 'Frequency', 'Monetary', 'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment']
    assert list(df.columns) == expected_cols

def test_recency_calculation():
    """Case 1.3: Verify that the mathematical calculation of Recency is correct."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame({
        'Order Date': ['2023-01-15', '2023-05-20'],
        'Customer_ID': ['CUST-001', 'CUST-001'],
        'Sales': [100.0, 200.0],
        'Profit': [10.0, 20.0]
    })
    
    # Expected reference date: 2023-05-21 (max date + 1 day)
    # Expected recency: 2023-05-21 - 2023-05-20 = 1 day
    result = calculate_rfm(df)
    assert not result.empty
    customer_row = result[result['Customer_ID'] == 'CUST-001']
    assert len(customer_row) == 1
    assert int(customer_row['Recency'].iloc[0]) == 1

def test_frequency_monetary_calculation():
    """Case 1.4: Verify that Frequency (count) and Monetary (sum) are computed accurately."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame({
        'Order Date': ['2023-01-15', '2023-01-16', '2023-01-17'],
        'Customer_ID': ['CUST-002', 'CUST-002', 'CUST-002'],
        'Sales': [150.00, 250.50, 50.25],
        'Profit': [15.0, 25.0, 5.0]
    })
    
    result = calculate_rfm(df)
    assert not result.empty
    customer_row = result[result['Customer_ID'] == 'CUST-002']
    assert len(customer_row) == 1
    assert int(customer_row['Frequency'].iloc[0]) == 3
    assert float(customer_row['Monetary'].iloc[0]) == 450.75

def test_segment_assignment():
    """Case 1.5: Verify that customers are correctly classified into segments based on RFM scores."""
    calculate_rfm = get_calculate_rfm()
    
    # We create a dataset with enough distinct values to establish scores 1 to 5
    # Let's generate 10 customers with varying recency, frequency, and monetary values.
    # To make scores predictable, we construct transactions:
    data = []
    # R_Score range: we want customers with last order dates ranging from 2023-01-01 (oldest) to 2023-12-31 (newest)
    # Customer 1: Champion: R_Score=5, F_Score=5, M_Score=5
    # Customer 2: Lost: R_Score=1, F_Score=1, M_Score=1
    # Customer 3: Can't Lose Them or At Risk: R_Score=1, F_Score=5, M_Score=5
    
    # Let's write the test to verify that the segment classification logic maps scores correctly.
    # If the module has a segment_customers function, we can also test it directly.
    try:
        from scripts.rfm_analysis import segment_customers
        rfm_mock = pd.DataFrame({
            'Customer_ID': ['C1', 'C2', 'C3'],
            'R_Score': [5, 1, 1],
            'F_Score': [5, 1, 5],
            'M_Score': [5, 1, 5],
            'RFM_Score': ['555', '111', '155']
        })
        result = segment_customers(rfm_mock)
        assert result.loc[result['Customer_ID'] == 'C1', 'Segment'].iloc[0] == 'Champions'
        assert result.loc[result['Customer_ID'] == 'C2', 'Segment'].iloc[0] == 'Lost'
        assert result.loc[result['Customer_ID'] == 'C3', 'Segment'].iloc[0] in ["Can't Lose Them", "At Risk"]
    except ImportError:
        # Fallback to calculate_rfm E2E check with a constructed dataset
        # We'll let it fail or attempt to assert on calculate_rfm if we have it
        pytest.fail("Could not import segment_customers from scripts.rfm_analysis.")

# --- TIER 2 TESTS ---

def test_empty_input_csv():
    """Case 2.1: Verify the engine's behavior when the input file is empty (contains only header)."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame(columns=['Customer_ID', 'Order Date', 'Region', 'Category', 'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit'])
    
    result = calculate_rfm(df)
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    expected_cols = ['Customer_ID', 'Recency', 'Frequency', 'Monetary', 'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment']
    for col in expected_cols:
        assert col in result.columns

def test_single_customer_dataset():
    """Case 2.2: Verify that the engine handles a dataset containing only one unique customer without throwing errors."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-02-01', '2023-03-01'],
        'Customer_ID': ['CUST-001', 'CUST-001', 'CUST-001'],
        'Sales': [100.0, 100.0, 100.0],
        'Profit': [10.0, 10.0, 10.0]
    })
    
    result = calculate_rfm(df)
    assert len(result) == 1
    assert result['Customer_ID'].iloc[0] == 'CUST-001'

def test_same_day_purchases():
    """Case 2.3: Verify calculations when all transactions occur on the same day as the reference date."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame({
        'Order Date': ['2023-12-31', '2023-12-31', '2023-12-31'],
        'Customer_ID': ['C1', 'C2', 'C3'],
        'Sales': [100.0, 200.0, 300.0],
        'Profit': [10.0, 20.0, 30.0]
    })
    
    # Reference date is 2024-01-01. Recency for all is 1 day.
    result = calculate_rfm(df)
    assert not result.empty
    assert (result['Recency'] == 1).all()

def test_negative_zero_monetary():
    """Case 2.4: Verify how the engine handles refunds or zero-value transactions that lead to net negative/zero monetary totals."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'Customer_ID': ['C1', 'C2', 'C2'],
        'Sales': [0.0, 100.0, -200.0],
        'Profit': [0.0, 10.0, -20.0]
    })
    
    result = calculate_rfm(df)
    assert result.loc[result['Customer_ID'] == 'C1', 'Monetary'].iloc[0] == 0.0
    assert result.loc[result['Customer_ID'] == 'C2', 'Monetary'].iloc[0] == -100.0

def test_missing_invalid_fields():
    """Case 2.5: Verify that the engine is robust to corrupted records (null fields or invalid formats)."""
    calculate_rfm = get_calculate_rfm()
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', 'invalid-date', '2023-01-03', '2023-01-04'],
        'Customer_ID': ['C1', 'C2', None, 'C4'],
        'Sales': [100.0, 200.0, 300.0, None],
        'Profit': [10.0, 20.0, 30.0, 40.0]
    })
    
    # Row 1 is valid (C1).
    # Row 2 has invalid date (C2).
    # Row 3 has missing Customer_ID (None).
    # Row 4 has missing Sales (C4).
    # Only C1 should be processed successfully if the invalid rows are skipped/dropped.
    result = calculate_rfm(df)
    assert len(result) == 1
    assert result['Customer_ID'].iloc[0] == 'C1'
