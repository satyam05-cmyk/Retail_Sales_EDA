import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_sales_data(rows=1000, num_customers=200, seed=42):
    """Generates synthetic superstore sales data with repeatable customer IDs."""
    np.random.seed(seed)
    random.seed(seed)

    # 1. DEFINE CATEGORIES
    regions = ["East", "West", "Central", "South"]
    categories = {
        "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
        "Technology": ["Phones", "Accessories", "Copiers", "Machines"],
        "Office Supplies": ["Binders", "Paper", "Storage", "Art"],
    }

    # Pre-allocate customer IDs per region
    customer_ids = [f"CUST-{1000 + i}" for i in range(1, num_customers + 1)]
    customer_pools = {r: [] for r in regions}
    for idx, cid in enumerate(customer_ids):
        r = regions[idx % len(regions)]
        customer_pools[r].append(cid)

    # Fallback in case a region's pool is empty (e.g. if num_customers < 4)
    for r in regions:
        if not customer_pools[r]:
            customer_pools[r] = customer_ids

    # Sample from the regional customer pool using a local RandomState instance
    local_rng = np.random.RandomState(seed)

    data = []

    # 2. GENERATE TRANSACTIONS
    for i in range(rows):
        date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        region = np.random.choice(regions)

        # Sample Customer_ID using local RandomState to preserve the global seed stream
        cust_id = local_rng.choice(customer_pools[region])

        cat = np.random.choice(list(categories.keys()))
        sub_cat = np.random.choice(categories[cat])

        # Logic: Base Sales
        sales = round(np.random.uniform(10, 5000), 2)
        quantity = np.random.randint(1, 10)

        # Logic: Discount & Profit (The "Trap")
        # Tables and Bookcases get HIGH discounts and NEGATIVE profit
        if sub_cat in ["Tables", "Bookcases"]:
            discount = np.random.choice([0.3, 0.4, 0.5, 0.7])  # Huge discounts
            profit = (sales * 0.1) - (sales * discount * 1.2)  # Guaranteed Loss
        elif sub_cat == "Copiers":
            discount = 0.0
            profit = sales * 0.4  # Huge Profit
        else:
            discount = np.random.choice([0.0, 0.1, 0.2])
            profit = (sales * 0.2) - (sales * discount)

        data.append(
            [
                date,
                region,
                cat,
                sub_cat,
                sales,
                quantity,
                discount,
                round(profit, 2),
                cust_id,
            ]
        )

    df = pd.DataFrame(
        data,
        columns=[
            "Order Date",
            "Region",
            "Category",
            "Sub-Category",
            "Sales",
            "Quantity",
            "Discount",
            "Profit",
            "Customer_ID",
        ],
    )
    return df


if __name__ == "__main__":
    # Determine the project root to always output to the correct 'data' folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")

    # Create the directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Generate data
    df = generate_sales_data(rows=1000, num_customers=200, seed=42)

    # Save to the CSV
    output_path = os.path.join(data_dir, "superstore_sales.csv")
    df.to_csv(output_path, index=False)
    print(
        f"SUCCESS: '{output_path}' generated with repeat buyers and hidden profit traps."
    )

