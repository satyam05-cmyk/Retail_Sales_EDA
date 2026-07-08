import os
import sys
import pandas as pd
import numpy as np

def _score_metric(series: pd.Series, ascending: bool) -> pd.Series:
    """
    Helper function to calculate rank-based scores from 1 to 5 for a metric.
    
    Rules:
    - Score values must range from 1 to 5.
    - Use rank-based scoring (series.rank(method='first')) to prevent duplicate bin edges.
    - For Recency, ascending=False (lower days is better, so lower days gets higher score).
    - For Frequency & Monetary, ascending=True (higher is better, so higher gets higher score).
    - If N < 5, scale ranks linearly to [1, 5] and round them.
    - If a metric contains only 1 unique value, assign score 5 to all customers.
    """
    if series.empty:
        return pd.Series(dtype=int)
    
    if series.nunique() <= 1:
        return pd.Series(5, index=series.index, dtype=int)
    
    n = len(series)
    ranks = series.rank(method='first', ascending=ascending)
    
    if n < 5:
        # Scale ranks linearly from [1, n] to [1, 5] and round
        scaled = 1 + (ranks - 1) * 4.0 / (n - 1)
        return scaled.round().astype(int)
    else:
        # Use pd.qcut on ranks to divide into 5 equal-sized bins
        return pd.qcut(ranks, q=5, labels=[1, 2, 3, 4, 5]).astype(int)

def calculate_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Recency, Frequency, Monetary, their respective scores,
    the concatenated RFM score, and the customer segment.
    
    Input df is cleaned by dropping rows with NaN or unparseable Order Date,
    Customer_ID, and Sales.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            'Customer_ID', 'Recency', 'Frequency', 'Monetary',
            'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment'
        ])
    
    # Clean data
    df = df.copy()
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
    
    # Drop rows with NaN or unparseable Order Date, Customer_ID, and Sales
    df = df.dropna(subset=['Order Date', 'Customer_ID', 'Sales'])
    
    if df.empty:
        return pd.DataFrame(columns=[
            'Customer_ID', 'Recency', 'Frequency', 'Monetary',
            'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment'
        ])
    
    df['Customer_ID'] = df['Customer_ID'].astype(str)
    
    # Calculate Reference Date: max(Order Date) + 1 day
    max_date = df['Order Date'].max()
    reference_date = max_date + pd.Timedelta(days=1)
    
    # Aggregate by customer
    rfm = df.groupby('Customer_ID').agg(
        Last_Order_Date=('Order Date', 'max'),
        Frequency=('Order Date', 'count'),
        Monetary=('Sales', 'sum')
    ).reset_index()
    
    # Recency: Days since last order
    rfm['Recency'] = (reference_date - rfm['Last_Order_Date']).dt.days
    rfm = rfm.drop(columns=['Last_Order_Date'])
    
    # Scoring
    rfm['R_Score'] = _score_metric(rfm['Recency'], ascending=False)
    rfm['F_Score'] = _score_metric(rfm['Frequency'], ascending=True)
    rfm['M_Score'] = _score_metric(rfm['Monetary'], ascending=True)
    
    # RFM_Score (as string concatenation)
    rfm['RFM_Score'] = (
        rfm['R_Score'].astype(str) +
        rfm['F_Score'].astype(str) +
        rfm['M_Score'].astype(str)
    )
    
    # Segment
    rfm = segment_customers(rfm)
    
    # Return ordered columns
    return rfm[[
        'Customer_ID', 'Recency', 'Frequency', 'Monetary',
        'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment'
    ]]

def segment_customers(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the segment mapping rules to populate the 'Segment' column of the RFM DataFrame.
    """
    if rfm_df.empty:
        if 'Segment' not in rfm_df.columns:
            rfm_df = rfm_df.copy()
            rfm_df['Segment'] = pd.Series(dtype=str)
        return rfm_df

    df = rfm_df.copy()
    
    r = df['R_Score'].astype(int)
    f = df['F_Score'].astype(int)
    m = df['M_Score'].astype(int)
    
    # Segment conditions in order of precedence
    conditions = [
        # 1. Champions: High R, F, M (Score >= 4 for all)
        (r >= 4) & (f >= 4) & (m >= 4),
        
        # 2. Loyal Customers: High F, M (F, M >= 4, and R >= 3)
        (f >= 4) & (m >= 4) & (r >= 3),
        
        # 3. At Risk: Low R, High F, M (R <= 2, F >= 4, M >= 4)
        (r <= 2) & (f >= 4) & (m >= 4),
        
        # 4. Can't Lose Them: Low R, High M (R <= 2, M >= 4)
        (r <= 2) & (m >= 4),
        
        # 5. Lost: Low R, F, M (R <= 2, F <= 2, M <= 2)
        (r <= 2) & (f <= 2) & (m <= 2),
        
        # 6. About to Sleep: Low R, F (R <= 2, F <= 2)
        (r <= 2) & (f <= 2),
        
        # 7. Potential Loyalists: Medium R, F (R >= 3, F >= 3)
        (r >= 3) & (f >= 3),
        
        # 8. Recent Customers: High R, low F (R >= 4, F <= 2)
        (r >= 4) & (f <= 2),
        
        # 9. Promising: Medium R, low F (R == 3, F <= 2)
        (r == 3) & (f <= 2),
        
        # 10. Customers Needing Attention: Medium F, M (F >= 3, M >= 3)
        (f >= 3) & (m >= 3)
    ]
    
    choices = [
        'Champions',
        'Loyal Customers',
        'At Risk',
        "Can't Lose Them",
        'Lost',
        'About to Sleep',
        'Potential Loyalists',
        'Recent Customers',
        'Promising',
        'Customers Needing Attention'
    ]
    
    # Default to 'About to Sleep' for any unmatched edge cases
    df['Segment'] = np.select(conditions, choices, default='About to Sleep')
    
    return df

def get_segment_definitions() -> dict:
    """
    Returns a dictionary of segment names to their descriptions.
    """
    return {
        'Champions': 'Bought recently, buy often and spend the most!',
        'Loyal Customers': 'Spend good money with us often. Responsive to promotions.',
        'Potential Loyalists': 'Recent customers, but spent a good amount and bought more than once.',
        'Recent Customers': 'Bought most recently, but not often.',
        'Promising': 'Recent shoppers, but haven\'t spent much.',
        'Customers Needing Attention': 'Above average recency, frequency and monetary values. May not have bought very recently though.',
        'About to Sleep': 'Below average recency, frequency and monetary values. Will lose them if not reactivated.',
        'At Risk': 'Spent big money and purchased often but long time ago. Need to bring them back!',
        'Can\'t Lose Them': 'Made biggest purchases, and often, but haven\'t returned for a long time.',
        'Lost': 'Lowest recency, frequency and monetary scores. Almost lost.'
    }

if __name__ == "__main__":
    # Determine project root dynamically based on this file's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_path = os.path.join(project_root, 'data', 'superstore_sales.csv')
    output_path = os.path.join(project_root, 'data', 'rfm_customer_segments.csv')
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        df = pd.read_csv(input_path)
        rfm_df = calculate_rfm(df)
        
        # Ensure target directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        rfm_df.to_csv(output_path, index=False)
        print("SUCCESS")
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)
