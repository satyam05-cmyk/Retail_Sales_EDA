# Test Infrastructure & Specification

This document details the E2E and integration test suite designed for the Retail Sales EDA Upgrade project.

## Directory Structure

```
02_Retail_Sales_EDA/
├── run_tests.py             # Main test runner execution script
├── TEST_INFRA.md            # Test specification document (this file)
├── TEST_READY.md            # Test readiness flag file
└── tests/
    ├── conftest.py          # Pytest fixtures and session configurations
    ├── test_data_generation.py # 10 data generation tests (Tier 1 & Tier 2)
    ├── test_rfm_engine.py      # 10 RFM engine tests (Tier 1 & Tier 2)
    ├── test_dashboard.py       # 10 dashboard UI tests (Tier 1 & Tier 2)
    └── test_scenarios.py       # 8 scenarios / integration tests (Tier 3 & Tier 4)
```

---

## Detailed Test Cases (38 Total)

### 1. Data Generation (`tests/test_data_generation.py`)
This file tests the upgraded data generator module in `scripts/generate_data.py`.

#### Tier 1: Core / Standard Cases
*   **Case 1: File Generation and Existence (`test_exists`)**
    *   *Goal*: Asserts that executing `generate_sales_data()` creates a valid pandas DataFrame of the requested size.
*   **Case 2: Schema and Column Validation (`test_columns`)**
    *   *Goal*: Asserts that the output DataFrame matches the exact column list: `['Order Date', 'Region', 'Category', 'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit', 'Customer_ID']`.
*   **Case 3: Customer ID Generation (`test_customer_id_format`)**
    *   *Goal*: Asserts that the new `Customer_ID` column is fully populated (no nulls) and matches the regex pattern `^CUST-\d+$`.
*   **Case 4: Repeat Buyers Verification (`test_repeat_buyers`)**
    *   *Goal*: Asserts that the unique number of customers is strictly less than the total row count, indicating repeat purchases.
*   **Case 5: Seed & Reproducibility (`test_reproducibility`)**
    *   *Goal*: Asserts that generating data twice using the same seed produces mathematically identical results.

#### Tier 2: Edge / Boundary Cases
*   **Case 6: Empty Configuration / Zero Rows (`test_empty_config`)**
    *   *Goal*: Asserts that requesting 0 rows returns an empty DataFrame containing the correct column headers without errors.
*   **Case 7: Boundary Case - Single Row (`test_single_row`)**
    *   *Goal*: Asserts that requesting 1 row generates exactly one row containing no null values.
*   **Case 8: Extreme Profit/Loss Logic (`test_extreme_profit_loss`)**
    *   *Goal*: Asserts profit trap rules: Tables/Bookcases are always unprofitable, and Copiers always yield exactly `40%` profit.
*   **Case 9: Zero Discount Rules (`test_zero_discount`)**
    *   *Goal*: Asserts that when discount is `0.0`, Copiers have exactly `40%` profit, and other items have exactly `20%` profit.
*   **Case 10: Single Buyer Concentration (`test_single_buyer`)**
    *   *Goal*: Asserts that setting `num_customers=1` assigns the exact same customer ID to all transactions.

---

### 2. RFM Engine (`tests/test_rfm_engine.py`)
This file tests the RFM segment analysis module in `scripts/rfm_analysis.py`.

#### Tier 1: Core / Standard Cases
*   **Case 1.1: CLI Execution & Exit Code (`test_cli_execution`)**
    *   *Goal*: Runs `python scripts/rfm_analysis.py` directly and asserts that it terminates with exit code 0.
*   **Case 1.2: Output CSV Generation & Schema Verification (`test_output_csv_generation`)**
    *   *Goal*: Asserts that the CLI execution creates `data/rfm_customer_segments.csv` with columns: `['Customer_ID', 'Recency', 'Frequency', 'Monetary', 'R_Score', 'F_Score', 'M_Score', 'RFM_Score', 'Segment']`.
*   **Case 1.3: Recency Calculation Correctness (`test_recency_calculation`)**
    *   *Goal*: Using a custom transaction timeline, asserts that Recency is calculated correctly relative to $\max(\text{Order Date}) + 1\text{ day}$.
*   **Case 1.4: Frequency & Monetary Calculation Correctness (`test_frequency_monetary_calculation`)**
    *   *Goal*: Asserts that Frequency is counted and Monetary values are summed up correctly per customer.
*   **Case 1.5: Segment Assignment Consistency (`test_segment_assignment`)**
    *   *Goal*: Asserts that the segment mapping function assigns correct segments (e.g., `'Champions'` for 5-5-5, `'Lost'` for 1-1-1).

#### Tier 2: Edge / Boundary Cases
*   **Case 2.1: Empty Input CSV (`test_empty_input_csv`)**
    *   *Goal*: Asserts that when transactions dataset is empty, it returns an empty RFM DataFrame without crash.
*   **Case 2.2: Single Customer Dataset (`test_single_customer_dataset`)**
    *   *Goal*: Asserts that having only 1 customer is handled without quantile binning errors.
*   **Case 2.3: Same Day Purchases (Zero Recency) (`test_same_day_purchases`)**
    *   *Goal*: Asserts that when all purchases happen on the same day, Recency is calculated as `1` day and no divide-by-zero occurs.
*   **Case 2.4: Negative & Zero Monetary Values (`test_negative_zero_monetary`)**
    *   *Goal*: Asserts that refunds (negative sales) or zero-sales transactions are correctly processed.
*   **Case 2.5: Missing / Invalid Fields (`test_missing_invalid_fields`)**
    *   *Goal*: Asserts that missing dates, missing Customer IDs, or missing Sales values are skipped gracefully.

---

### 3. Dashboard UI (`tests/test_dashboard.py`)
This file uses `streamlit.testing.v1.AppTest` to verify the Streamlit application in `dashboard/app.py`.

#### Tier 1: Core / Standard Cases
*   **Case 3.1: Smoke Test & App Render (`test_dashboard_renders`)**
    *   *Goal*: Asserts that the app boots up and displays the main title: `"📊 Retail Profitability Diagnosis"`.
*   **Case 3.2: Multi-tab Layout & Navigation (`test_multitab_layout`)**
    *   *Goal*: Asserts that the application contains exactly 2 tabs with labels: `"Profitability Analysis"` and `"RFM Customer Segmentation"`.
*   **Case 3.3: Sidebar Filters Application (`test_sidebar_filters`)**
    *   *Goal*: Asserts that modifying the multiselect sidebar filters (Region/Category) runs the app without raising exceptions.
*   **Case 3.4: Caching Behavior Verification (`test_caching`)**
    *   *Goal*: Asserts that repeated interactions trigger cached data loading, calling `read_csv` only once.
*   **Case 3.5: Raw Data View Toggle (`test_raw_data_toggle`)**
    *   *Goal*: Asserts that clicking the `"Show Raw Data"` checkbox renders the raw dataframe, and unchecking removes it.

#### Tier 2: Edge / Boundary Cases
*   **Case 3.6: Empty Filter Selection (`test_empty_filter_results`)**
    *   *Goal*: Asserts that deselecting all options in filters resets metric cards to a fallback (e.g. `0.0%` margin) without crash.
*   **Case 3.7: Single Region / Category Selection (`test_single_selection`)**
    *   *Goal*: Asserts that selecting a single region/category handles subset rendering successfully.
*   **Case 3.8: Missing Profit Trap Data Handling (`test_missing_profit_traps`)**
    *   *Goal*: Asserts that a dataset containing only profitable transactions (no "profit trap" categories) does not crash the charts.
*   **Case 3.9: Missing/Malformed Customer ID Handling (`test_malformed_rfm_data`)**
    *   *Goal*: Asserts that null customer IDs do not crash the app, displaying a warning instead.
*   **Case 3.10: Extreme/Outlier Sales and Profit Formatting (`test_outlier_formatting`)**
    *   *Goal*: Asserts that extremely large values (e.g., `$150,000,000` Sales) format correctly with comma separators.

---

### 4. Integration Scenarios (`tests/test_scenarios.py`)
This file tests multi-feature flows and business scenarios.

#### Tier 3: Cross-Feature Integration
*   **Case 3.11: End-to-End Execution Flow (`test_e2e_integration`)**
    *   *Goal*: Verifies the complete data generation -> file write -> dashboard read sequence.
*   **Case 3.12: Interactive Discount-to-Profit Trap Sync (`test_discount_profit_sync`)**
    *   *Goal*: Asserts that custom discount values are mapped accurately in the Profitability scatter plot.
*   **Case 3.13: Region Filter Synchronization Across Tabs (`test_filter_sync_across_tabs`)**
    *   *Goal*: Asserts that applying a region filter updates both the first tab's metrics and the second tab's customer list.

#### Tier 4: Real-World Business Scenarios
*   **Case 4.1: Holiday Sales Boom (`test_holiday_stress_test`)**
    *   *Goal*: Stress tests the dashboard with 50,000 transactions, asserting the initial load is under 5 seconds and cached reruns under 0.5 seconds.
*   **Case 4.2: Inactive Customer Churn Analysis (`test_inactive_churn_rfm`)**
    *   *Goal*: Asserts that inserting historical-only transactions calculates old recencies (high inactive count) correctly.
*   **Case 4.3: Interactive Discount Trap Diagnosis (`test_discount_trap_threshold`)**
    *   *Goal*: Verifies scatter plot rendering when margins cross the 30% discount trap.
*   **Case 4.4: Mega Buyer Outlier (`test_mega_buyer_rfm`)**
    *   *Goal*: Verifies that a single customer spending $1M does not squash the remaining cohort's scores.
*   **Case 4.5: Cold Start Market Expansion (`test_cold_start_region`)**
    *   *Goal*: Verifies app stability when a new region with only a single transaction is introduced.

---

## Execution Command

You can execute the entire test suite using the customized test runner script:

```bash
python run_tests.py
```

Alternatively, you can run the suite directly with pytest:

```bash
pytest tests/ -v
```
