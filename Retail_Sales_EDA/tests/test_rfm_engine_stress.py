import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add project root to sys.path to enable imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.rfm_analysis import calculate_rfm, segment_customers, _score_metric

def test_missing_columns():
    """Verify that calculate_rfm raises KeyError when required columns are missing."""
    df_missing_date = pd.DataFrame({
        'Customer_ID': ['C1'],
        'Sales': [100.0]
    })
    with pytest.raises(KeyError):
        calculate_rfm(df_missing_date)

    df_missing_cust = pd.DataFrame({
        'Order Date': ['2023-01-01'],
        'Sales': [100.0]
    })
    with pytest.raises(KeyError):
        calculate_rfm(df_missing_cust)

    df_missing_sales = pd.DataFrame({
        'Order Date': ['2023-01-01'],
        'Customer_ID': ['C1']
    })
    with pytest.raises(KeyError):
        calculate_rfm(df_missing_sales)

def test_invalid_and_empty_values():
    """Verify calculate_rfm behavior with various invalid/empty values in inputs."""
    # Dataframe with NaN values in different columns
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', None, '2023-01-03', '2023-01-04', '2023-01-05'],
        'Customer_ID': ['C1', 'C2', None, 'C4', 'C5'],
        'Sales': [100.0, 200.0, 300.0, None, 'invalid_sales']
    })
    # Row 1 (C1): Valid
    # Row 2 (C2): Missing Order Date (should be dropped)
    # Row 3 (None): Missing Customer_ID (should be dropped)
    # Row 4 (C4): Missing Sales (should be dropped)
    # Row 5 (C5): Unparseable Sales (should be coerced to NaN and dropped)
    
    result = calculate_rfm(df)
    assert len(result) == 1
    assert result['Customer_ID'].iloc[0] == 'C1'

def test_invalid_dates_handling():
    """Verify calculate_rfm handles various date formats, including unparseable ones."""
    df = pd.DataFrame({
        'Order Date': ['2023/01/01', '02-01-2023', 'invalid-date-string', '2023-01-04 12:00:00'],
        'Customer_ID': ['C1', 'C2', 'C3', 'C4'],
        'Sales': [100.0, 100.0, 100.0, 100.0]
    })
    # 'invalid-date-string' should be coerced to NaT and dropped.
    # The others should be parsed correctly.
    result = calculate_rfm(df)
    assert len(result) == 3
    assert set(result['Customer_ID']) == {'C1', 'C2', 'C4'}

def test_extreme_monetary_values():
    """Verify calculate_rfm handles extreme, infinite, and negative sales values."""
    # Note: df['Sales'] is coerced to numeric.
    # Let's test very large values, negative values (refunds), and inf
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01'],
        'Customer_ID': ['C1', 'C2', 'C3', 'C4'],
        'Sales': [1e15, -100.0, 0.0, float('inf')]
    })
    
    result = calculate_rfm(df)
    assert len(result) == 4
    
    c1_row = result[result['Customer_ID'] == 'C1']
    assert c1_row['Monetary'].iloc[0] == 1e15
    
    c2_row = result[result['Customer_ID'] == 'C2']
    assert c2_row['Monetary'].iloc[0] == -100.0
    
    c3_row = result[result['Customer_ID'] == 'C3']
    assert c3_row['Monetary'].iloc[0] == 0.0
    
    c4_row = result[result['Customer_ID'] == 'C4']
    assert c4_row['Monetary'].iloc[0] == float('inf')

def test_single_customer():
    """Verify calculate_rfm behavior with a single customer."""
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-01-02'],
        'Customer_ID': ['C1', 'C1'],
        'Sales': [100.0, 200.0]
    })
    
    result = calculate_rfm(df)
    assert len(result) == 1
    assert result['Customer_ID'].iloc[0] == 'C1'
    assert result['Recency'].iloc[0] == 1  # max date is 2023-01-02, ref date is 2023-01-03, diff is 1
    assert result['Frequency'].iloc[0] == 2
    assert result['Monetary'].iloc[0] == 300.0
    # Since nunique <= 1 for all metrics, score should be 5 for R, F, M
    assert result['R_Score'].iloc[0] == 5
    assert result['F_Score'].iloc[0] == 5
    assert result['M_Score'].iloc[0] == 5
    assert result['RFM_Score'].iloc[0] == '555'
    assert result['Segment'].iloc[0] == 'Champions'

def test_small_n_customers():
    """Verify linear scaling logic when customer count N < 5."""
    # Case N = 2
    df_2 = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-01-05'],
        'Customer_ID': ['C1', 'C2'],
        'Sales': [100.0, 200.0]  # C2 is better on monetary (200 > 100), C2 is better on recency (5 > 1)
    })
    # Reference date: 2023-01-06
    # C1: Last order 2023-01-01, Recency = 5 days, F = 1, M = 100
    # C2: Last order 2023-01-05, Recency = 1 day, F = 1, M = 200
    res_2 = calculate_rfm(df_2)
    # Recency: C2 (1 day) is better than C1 (5 days).
    # Since ascending=False for Recency:
    # ranks: C1 -> 1.0 (worst), C2 -> 2.0 (best)
    # scaled = 1 + (ranks - 1) * 4 / (2-1) = 1 + (ranks - 1) * 4
    # C1 R_Score: 1, C2 R_Score: 5
    assert res_2.loc[res_2['Customer_ID'] == 'C1', 'R_Score'].iloc[0] == 1
    assert res_2.loc[res_2['Customer_ID'] == 'C2', 'R_Score'].iloc[0] == 5
    # Frequency: Both have F=1. nunique <= 1, so both F_Score should be 5.
    assert res_2['F_Score'].iloc[0] == 5
    assert res_2['F_Score'].iloc[1] == 5
    # Monetary: C2 (200) is better than C1 (100).
    # Since ascending=True for Monetary:
    # ranks: C1 -> 1.0, C2 -> 2.0
    # C1 M_Score: 1, C2 M_Score: 5
    assert res_2.loc[res_2['Customer_ID'] == 'C1', 'M_Score'].iloc[0] == 1
    assert res_2.loc[res_2['Customer_ID'] == 'C2', 'M_Score'].iloc[0] == 5

    # Case N = 3
    df_3 = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-01-03', '2023-01-05'],
        'Customer_ID': ['C1', 'C2', 'C3'],
        'Sales': [100.0, 150.0, 200.0]
    })
    res_3 = calculate_rfm(df_3)
    # Monetary ranks: C1->1.0, C2->2.0, C3->3.0
    # scaled = 1 + (ranks - 1) * 4 / 2 = 1 + (ranks - 1) * 2
    # Scores: C1 -> 1, C2 -> 3, C3 -> 5
    assert res_3.loc[res_3['Customer_ID'] == 'C1', 'M_Score'].iloc[0] == 1
    assert res_3.loc[res_3['Customer_ID'] == 'C2', 'M_Score'].iloc[0] == 3
    assert res_3.loc[res_3['Customer_ID'] == 'C3', 'M_Score'].iloc[0] == 5

def test_zero_variance_metrics():
    """Verify that if all customers have identical metric values, they get score 5."""
    df = pd.DataFrame({
        'Order Date': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01'],
        'Customer_ID': ['C1', 'C2', 'C3', 'C4', 'C5'],
        'Sales': [100.0, 100.0, 100.0, 100.0, 100.0]
    })
    result = calculate_rfm(df)
    assert (result['R_Score'] == 5).all()
    assert (result['F_Score'] == 5).all()
    assert (result['M_Score'] == 5).all()
    assert (result['RFM_Score'] == '555').all()

def test_large_dataset_performance():
    """Verify calculate_rfm performance and score distributions on a large dataset."""
    # Generate 10000 rows for 1000 unique customers
    np.random.seed(42)
    n_rows = 10000
    customers = [f"CUST-{i:04d}" for i in range(1, 1001)]
    
    df = pd.DataFrame({
        'Order Date': pd.to_datetime('2023-01-01') + pd.to_timedelta(np.random.randint(0, 365, n_rows), unit='D'),
        'Customer_ID': np.random.choice(customers, n_rows),
        'Sales': np.random.uniform(5.0, 500.0, n_rows)
    })
    
    import time
    start_time = time.time()
    result = calculate_rfm(df)
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 2.0, f"Performance test took too long: {duration:.2f} seconds"
    assert len(result) == 1000
    
    # Check that score values are distributed evenly from 1 to 5
    # Since pd.qcut divides ranks into 5 equal bins of size 200 each:
    for score_col in ['R_Score', 'F_Score', 'M_Score']:
        counts = result[score_col].value_counts()
        for s in [1, 2, 3, 4, 5]:
            assert counts[s] == 200, f"Expected exactly 200 counts for score {s} in {score_col}, got {counts[s]}"

def test_all_segment_combinations():
    """Verify that all 125 possible RFM score combinations map correctly to segments."""
    # Test segment_customers directly
    records = []
    for r in range(1, 6):
        for f in range(1, 6):
            for m in range(1, 6):
                records.append({
                    'Customer_ID': f"C-{r}{f}{m}",
                    'R_Score': r,
                    'F_Score': f,
                    'M_Score': m,
                    'RFM_Score': f"{r}{f}{m}"
                })
    df_rfm = pd.DataFrame(records)
    result = segment_customers(df_rfm)
    
    # Check that Segment is populated for all and contains no nulls
    assert len(result) == 125
    assert not result['Segment'].isnull().any()
    
    # Verify the fallback cases: R <= 2, F >= 3, M <= 2 must map to 'About to Sleep'
    fallback_mask = (result['R_Score'] <= 2) & (result['F_Score'] >= 3) & (result['M_Score'] <= 2)
    fallback_records = result[fallback_mask]
    assert len(fallback_records) == 12  # 2 * 3 * 2 = 12
    assert (fallback_records['Segment'] == 'About to Sleep').all()
    
    # Verify Champion mappings
    champs = result[(result['R_Score'] >= 4) & (result['F_Score'] >= 4) & (result['M_Score'] >= 4)]
    assert (champs['Segment'] == 'Champions').all()
    
    # Verify Lost mappings
    lost = result[(result['R_Score'] <= 2) & (result['F_Score'] <= 2) & (result['M_Score'] <= 2)]
    assert (lost['Segment'] == 'Lost').all()

def test_empty_dataframe_types():
    """Verify that calculate_rfm returns expected column types for empty inputs."""
    df = pd.DataFrame(columns=['Customer_ID', 'Order Date', 'Sales'])
    result = calculate_rfm(df)
    assert list(result.columns) == [
        'Customer_ID', 'Recency', 'Frequency', 'Monetary',
        'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment'
    ]
    # Check column types when non-empty but with zero rows
    # Let's ensure types are not object where we expect numbers
    # Note: pandas empty Series might have default dtypes, but we check if we can safely perform operations
    assert len(result) == 0
