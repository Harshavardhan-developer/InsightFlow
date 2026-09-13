"""
clean_data.py
-------------
Cleans the raw synthetic sales dataset and produces an analysis-ready
processed CSV. Prints before/after stats so the cleaning is auditable.
"""

import numpy as np
import pandas as pd

RAW_PATH = "data/raw/sales_raw.csv"
OUT_PATH = "data/processed/sales_cleaned.csv"

TEXT_COLS = ["Customer_Name", "Customer_Segment", "Category", "Sub_Category",
             "Region", "State", "City", "Payment_Mode", "Shipping_Mode",
             "Product_Name"]


def main():
    df = pd.read_csv(RAW_PATH)

    before_rows = len(df)
    before_missing = int(df.isna().sum().sum())
    before_dupes = int(df.duplicated().sum())

    print("=" * 55)
    print("BEFORE CLEANING")
    print("=" * 55)
    print(f"Rows:            {before_rows:,}")
    print(f"Missing values:  {before_missing:,}")
    print(f"Duplicate rows:  {before_dupes:,}")

    # ------------------------------------------------------------------
    # 1. Remove exact duplicates
    # ------------------------------------------------------------------
    df = df.drop_duplicates().copy()

    # ------------------------------------------------------------------
    # 2. Clean text columns: strip whitespace, normalize casing
    # ------------------------------------------------------------------
    for col in TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col].isin(["nan", "None", ""]), col] = np.nan
            # Title-case categorical-ish columns for consistency
            if col not in ("Customer_Name", "Product_Name"):
                df[col] = df[col].str.title()
            else:
                df[col] = df[col].str.title()

    # ------------------------------------------------------------------
    # 3. Handle missing values
    # ------------------------------------------------------------------
    df["Customer_Name"] = df["Customer_Name"].fillna("Unknown Customer")
    df["City"] = df["City"].fillna(df["Region"].map(
        df.groupby("Region")["City"].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown")
    ))
    df["City"] = df["City"].fillna("Unknown")
    df["Discount"] = df["Discount"].fillna(df["Discount"].median())
    df["Payment_Mode"] = df["Payment_Mode"].fillna(df["Payment_Mode"].mode().iloc[0])

    # Drop rows missing critical identifiers/measures (should be ~0 by design)
    critical = ["Order_ID", "Order_Date", "Customer_ID", "Product_ID", "Sales"]
    df = df.dropna(subset=critical)

    # ------------------------------------------------------------------
    # 4. Fix data types
    # ------------------------------------------------------------------
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df = df.dropna(subset=["Order_Date"])

    numeric_cols = ["Quantity", "Unit_Price", "Discount", "Sales", "Cost", "Profit"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)

    # ------------------------------------------------------------------
    # 5. Detect & handle unreasonable numeric values / outliers
    # ------------------------------------------------------------------
    # Discount must be within [0, 0.9]
    df = df[(df["Discount"] >= 0) & (df["Discount"] <= 0.9)]
    # Quantity must be positive and reasonable
    df = df[(df["Quantity"] > 0) & (df["Quantity"] <= 20)]
    # Sales/Unit_Price must be positive
    df = df[(df["Sales"] > 0) & (df["Unit_Price"] > 0)]

    # IQR-based outlier capping (winsorizing) on Sales and Profit so extreme
    # synthetic outliers don't distort KPI cards, while keeping the rows.
    for col in ["Sales", "Profit"]:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - 3 * iqr
        upper = q3 + 3 * iqr
        df[col] = df[col].clip(lower=lower, upper=upper)

    # ------------------------------------------------------------------
    # 6. Derived columns
    # ------------------------------------------------------------------
    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.month
    df["Quarter"] = df["Order_Date"].dt.quarter
    df["Month_Name"] = df["Order_Date"].dt.strftime("%b")
    df["Order_Value"] = df["Sales"]
    df["Profit_Margin"] = np.where(df["Sales"] != 0, df["Profit"] / df["Sales"], 0)

    df = df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    df.to_csv(OUT_PATH, index=False)

    after_rows = len(df)
    after_missing = int(df.isna().sum().sum())
    after_dupes = int(df.duplicated().sum())

    print("=" * 55)
    print("AFTER CLEANING")
    print("=" * 55)
    print(f"Rows:            {after_rows:,}")
    print(f"Missing values:  {after_missing:,}")
    print(f"Duplicate rows:  {after_dupes:,}")
    print(f"Rows removed:    {before_rows - after_rows:,}")
    print(f"Saved -> {OUT_PATH}")

    # Save a tiny data-quality summary for the Streamlit app
    summary = pd.DataFrame([{
        "raw_records": before_rows,
        "clean_records": after_rows,
        "duplicates_removed": before_dupes,
        "missing_values_handled": before_missing,
        "rows_removed_total": before_rows - after_rows,
    }])
    summary.to_csv("data/processed/data_quality_summary.csv", index=False)


if __name__ == "__main__":
    main()
