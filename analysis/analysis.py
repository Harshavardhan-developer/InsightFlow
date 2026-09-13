"""
analysis.py
-----------
Reusable analysis functions used by both this standalone script (for a
console report) and the Streamlit app (app.py imports these functions).

Everything here reads from data/processed/sales_cleaned.csv and computes
metrics dynamically — nothing is hard-coded.
"""

import numpy as np
import pandas as pd

DATA_PATH = "data/processed/sales_cleaned.csv"


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------

def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Order_Date"])
    return df


# ----------------------------------------------------------------------
# SALES
# ----------------------------------------------------------------------

def total_sales(df):
    return float(df["Sales"].sum())


def total_orders(df):
    return int(df["Order_ID"].nunique())


def avg_order_value(df):
    return float(df["Sales"].sum() / max(df["Order_ID"].nunique(), 1))


def monthly_sales(df):
    g = df.groupby(df["Order_Date"].dt.to_period("M"))["Sales"].sum().reset_index()
    g["Order_Date"] = g["Order_Date"].dt.to_timestamp()
    return g.rename(columns={"Order_Date": "Month"})


def yearly_sales(df):
    return df.groupby("Year")["Sales"].sum().reset_index()


def sales_by_category(df):
    return df.groupby("Category")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)


def sales_by_region(df):
    return df.groupby("Region")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)


def top_products(df, n=10, by="Sales"):
    return (df.groupby(["Product_ID", "Product_Name"])[by].sum()
            .reset_index().sort_values(by, ascending=False).head(n))


# ----------------------------------------------------------------------
# PROFIT
# ----------------------------------------------------------------------

def total_profit(df):
    return float(df["Profit"].sum())


def overall_profit_margin(df):
    s = df["Sales"].sum()
    return float(df["Profit"].sum() / s) if s else 0.0


def profit_by_category(df):
    return df.groupby("Category")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)


def profit_by_region(df):
    return df.groupby("Region")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)


def top_profitable_products(df, n=10):
    return top_products(df, n=n, by="Profit")


def loss_making_products(df, n=10):
    g = df.groupby(["Product_ID", "Product_Name"])["Profit"].sum().reset_index()
    return g.sort_values("Profit", ascending=True).head(n)


def discount_vs_profit(df, bins=10):
    tmp = df.copy()
    tmp["Discount_Bin"] = pd.cut(tmp["Discount"], bins=bins)
    g = tmp.groupby("Discount_Bin", observed=True).agg(
        Avg_Profit_Margin=("Profit_Margin", "mean"),
        Orders=("Order_ID", "count"),
    ).reset_index()
    g["Discount_Bin"] = g["Discount_Bin"].astype(str)
    return g


# ----------------------------------------------------------------------
# CUSTOMERS
# ----------------------------------------------------------------------

def total_customers(df):
    return int(df["Customer_ID"].nunique())


def customer_order_counts(df):
    return df.groupby("Customer_ID")["Order_ID"].nunique().reset_index(name="Orders")


def repeat_customers(df):
    c = customer_order_counts(df)
    return int((c["Orders"] > 1).sum())


def one_time_customers(df):
    c = customer_order_counts(df)
    return int((c["Orders"] == 1).sum())


def top_customers(df, n=10, by="Sales"):
    return (df.groupby(["Customer_ID", "Customer_Name"])[by].sum()
            .reset_index().sort_values(by, ascending=False).head(n))


def revenue_per_customer(df):
    return df.groupby(["Customer_ID", "Customer_Name"])["Sales"].sum().reset_index()


def profit_per_customer(df):
    return df.groupby(["Customer_ID", "Customer_Name"])["Profit"].sum().reset_index()


# ----------------------------------------------------------------------
# PRODUCTS
# ----------------------------------------------------------------------

def bottom_products(df, n=10, by="Sales"):
    g = df.groupby(["Product_ID", "Product_Name"])[by].sum().reset_index()
    return g.sort_values(by, ascending=True).head(n)


def category_performance(df):
    g = df.groupby("Category").agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique")
    ).reset_index()
    g["Profit_Margin"] = g["Profit"] / g["Sales"]
    return g.sort_values("Sales", ascending=False)


def subcategory_performance(df):
    g = df.groupby(["Category", "Sub_Category"]).agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    ).reset_index()
    g["Profit_Margin"] = g["Profit"] / g["Sales"]
    return g.sort_values("Sales", ascending=False)


# ----------------------------------------------------------------------
# REGIONS
# ----------------------------------------------------------------------

def state_sales(df):
    return df.groupby("State")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)


def city_sales(df):
    return df.groupby("City")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)


# ----------------------------------------------------------------------
# TIME
# ----------------------------------------------------------------------

def quarterly_trends(df):
    g = df.groupby(["Year", "Quarter"])["Sales"].sum().reset_index()
    g["Period"] = "Q" + g["Quarter"].astype(str) + " " + g["Year"].astype(str)
    return g


def yearly_trends(df):
    return df.groupby("Year").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).reset_index()


def month_over_month_growth(df):
    m = monthly_sales(df).sort_values("Month")
    m["Growth_%"] = m["Sales"].pct_change() * 100
    return m


# ----------------------------------------------------------------------
# STATISTICS
# ----------------------------------------------------------------------

def descriptive_stats(df, col="Sales"):
    s = df[col]
    return {
        "mean": float(s.mean()),
        "median": float(s.median()),
        "std": float(s.std()),
        "min": float(s.min()),
        "max": float(s.max()),
    }


def correlation_matrix(df, cols=None):
    cols = cols or ["Quantity", "Unit_Price", "Discount", "Sales", "Profit", "Profit_Margin"]
    return df[cols].corr()


def iqr_outliers(df, col="Sales"):
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (df[col] < lower) | (df[col] > upper)
    return df[mask], lower, upper


# ----------------------------------------------------------------------
# RFM ANALYSIS
# ----------------------------------------------------------------------

def rfm_analysis(df, reference_date=None):
    if reference_date is None:
        reference_date = df["Order_Date"].max() + pd.Timedelta(days=1)

    rfm = df.groupby(["Customer_ID", "Customer_Name"]).agg(
        Recency=("Order_Date", lambda x: (reference_date - x.max()).days),
        Frequency=("Order_ID", "nunique"),
        Monetary=("Sales", "sum"),
    ).reset_index()

    # Score 1-5 using quantiles (5 = best)
    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    def segment(row):
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "New Customers"
        elif r >= 3 and f <= 3 and m <= 3:
            return "Potential Loyalists"
        elif r <= 2 and f >= 3:
            return "At Risk"
        else:
            return "Lost Customers"

    rfm["Segment"] = rfm.apply(segment, axis=1)
    return rfm


def rfm_segment_summary(rfm_df, sales_df):
    profit_map = sales_df.groupby("Customer_ID")["Profit"].sum()
    rfm_df = rfm_df.copy()
    rfm_df["Profit"] = rfm_df["Customer_ID"].map(profit_map)
    summary = rfm_df.groupby("Segment").agg(
        Customers=("Customer_ID", "nunique"),
        Revenue=("Monetary", "sum"),
        Profit=("Profit", "sum"),
    ).reset_index().sort_values("Revenue", ascending=False)
    return summary


# ----------------------------------------------------------------------
# BUSINESS INSIGHTS (fully dynamic — no hard-coded names)
# ----------------------------------------------------------------------

def generate_insights(df):
    insights = []

    cat_perf = category_performance(df)
    best_cat = cat_perf.iloc[0]
    worst_margin_cat = cat_perf.sort_values("Profit_Margin").iloc[0]

    reg_perf = sales_by_region(df)
    best_region = reg_perf.iloc[0]

    prod_profit = top_profitable_products(df, n=1).iloc[0]

    top_cust = top_customers(df, n=1).iloc[0]

    m_sales = monthly_sales(df)
    best_month_row = m_sales.sort_values("Sales", ascending=False).iloc[0]

    disc_profit = discount_vs_profit(df)
    corr = df[["Discount", "Profit_Margin"]].corr().iloc[0, 1]

    insights.append(
        f"**{best_cat['Category']}** is the top-performing category by sales, "
        f"generating ₹{best_cat['Sales']:,.0f} in total revenue."
    )
    insights.append(
        f"**{best_region['Region']}** is the strongest region, contributing "
        f"₹{best_region['Sales']:,.0f} in sales."
    )
    insights.append(
        f"**{prod_profit['Product_Name']}** is the most profitable product, "
        f"with ₹{prod_profit['Profit']:,.0f} in total profit."
    )
    insights.append(
        f"**{top_cust['Customer_Name']}** is the highest-value customer, having generated "
        f"₹{top_cust['Sales']:,.0f} in lifetime sales."
    )
    insights.append(
        f"The highest-sales month was **{pd.to_datetime(best_month_row['Month']).strftime('%B %Y')}**, "
        f"with ₹{best_month_row['Sales']:,.0f} in revenue."
    )
    insights.append(
        f"**{worst_margin_cat['Category']}** has the lowest profit margin "
        f"({worst_margin_cat['Profit_Margin']*100:.1f}%) among all categories."
    )

    if corr < -0.05:
        insights.append(
            f"Discounting shows a negative relationship with profit margin (correlation "
            f"{corr:.2f}). Review discount levels in **{worst_margin_cat['Category']}** since "
            f"high discount rates there are associated with lower profit margins."
        )
    else:
        insights.append(
            f"Discount levels show a weak relationship with profit margin overall "
            f"(correlation {corr:.2f}); discounting does not appear to be a major profit driver."
        )

    return insights


# ----------------------------------------------------------------------
# Console report (run this file directly)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    df = load_data()

    print("=" * 60)
    print("INSIGHTFLOW — ANALYSIS REPORT")
    print("=" * 60)
    print(f"Total Sales:        ₹{total_sales(df):,.2f}")
    print(f"Total Profit:       ₹{total_profit(df):,.2f}")
    print(f"Profit Margin:      {overall_profit_margin(df)*100:.2f}%")
    print(f"Total Orders:       {total_orders(df):,}")
    print(f"Avg Order Value:    ₹{avg_order_value(df):,.2f}")
    print(f"Total Customers:    {total_customers(df):,}")
    print(f"Repeat Customers:   {repeat_customers(df):,}")
    print(f"One-time Customers: {one_time_customers(df):,}")

    print("\nTop 5 Categories by Sales:")
    print(sales_by_category(df).head(5).to_string(index=False))

    print("\nTop 5 Products by Profit:")
    print(top_profitable_products(df, n=5).to_string(index=False))

    rfm = rfm_analysis(df)
    print("\nRFM Segment Summary:")
    print(rfm_segment_summary(rfm, df).to_string(index=False))

    print("\nBusiness Insights:")
    for i, ins in enumerate(generate_insights(df), 1):
        print(f"{i}. {ins}")
