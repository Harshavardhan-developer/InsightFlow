"""
generate_data.py
----------------
Generates a realistic ~100,000 row synthetic sales dataset for the
InsightFlow analytics project. No external data is downloaded — the
dataset is fully synthetic but built with realistic business logic
(seasonality, category margins, discount effects, repeat customers).

A fixed random seed is used so the data is reproducible.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

N_ROWS = 100_000
N_CUSTOMERS = 8_000
N_PRODUCTS = 300

OUT_PATH = "data/raw/sales_raw.csv"

# ----------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------

REGIONS = {
    "North": ["Delhi", "Chandigarh", "Lucknow", "Jaipur"],
    "South": ["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
    "East": ["Kolkata", "Patna", "Bhubaneswar", "Guwahati"],
    "West": ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "Central": ["Bhopal", "Nagpur", "Indore", "Raipur"],
}
REGION_STATE = {
    "Delhi": "Delhi", "Chandigarh": "Punjab", "Lucknow": "Uttar Pradesh", "Jaipur": "Rajasthan",
    "Bengaluru": "Karnataka", "Chennai": "Tamil Nadu", "Hyderabad": "Telangana", "Kochi": "Kerala",
    "Kolkata": "West Bengal", "Patna": "Bihar", "Bhubaneswar": "Odisha", "Guwahati": "Assam",
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Ahmedabad": "Gujarat", "Surat": "Gujarat",
    "Bhopal": "Madhya Pradesh", "Nagpur": "Maharashtra", "Indore": "Madhya Pradesh", "Raipur": "Chhattisgarh",
}
# Region-level performance multipliers (some regions perform better)
REGION_WEIGHT = {"North": 1.05, "South": 1.20, "East": 0.85, "West": 1.15, "Central": 0.80}

CATEGORIES = {
    "Electronics": {
        "sub": ["Mobiles", "Laptops", "Accessories", "Audio"],
        "margin": 0.18, "price_range": (500, 60000),
    },
    "Furniture": {
        "sub": ["Chairs", "Tables", "Storage", "Decor"],
        "margin": 0.28, "price_range": (300, 25000),
    },
    "Office Supplies": {
        "sub": ["Stationery", "Paper", "Binders", "Art"],
        "margin": 0.35, "price_range": (20, 3000),
    },
    "Clothing": {
        "sub": ["Men", "Women", "Kids", "Footwear"],
        "margin": 0.30, "price_range": (200, 8000),
    },
    "Home Appliances": {
        "sub": ["Kitchen", "Cooling", "Cleaning", "Small Appliances"],
        "margin": 0.15, "price_range": (400, 45000),
    },
}
CATEGORY_NAMES = list(CATEGORIES.keys())
CATEGORY_WEIGHT = [0.30, 0.15, 0.20, 0.25, 0.10]  # some categories sell more

CUSTOMER_SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_WEIGHT = [0.55, 0.30, 0.15]

PAYMENT_MODES = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery"]
SHIPPING_MODES = ["Standard", "Express", "Same Day", "Economy"]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
               "Ishaan", "Rohan", "Ananya", "Diya", "Isha", "Aadhya", "Kavya", "Meera",
               "Priya", "Sneha", "Neha", "Riya", "Karthik", "Manish", "Sanjay", "Deepak",
               "Pooja", "Anjali", "Ravi", "Vikram", "Suresh", "Lakshmi"]
LAST_NAMES = ["Sharma", "Verma", "Reddy", "Iyer", "Nair", "Gupta", "Rao", "Patel", "Singh",
              "Kumar", "Das", "Mehta", "Joshi", "Chatterjee", "Pillai", "Menon", "Agarwal"]

PRODUCT_ADJ = ["Pro", "Max", "Lite", "Plus", "Ultra", "Classic", "Prime", "Neo", "Air", "Studio"]

# ----------------------------------------------------------------------
# Build customer master (customers reused across many orders)
# ----------------------------------------------------------------------

customer_ids = [f"CUST-{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
customer_names = [f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" for _ in customer_ids]
customer_segment = np.random.choice(CUSTOMER_SEGMENTS, size=N_CUSTOMERS, p=SEGMENT_WEIGHT)
# Some customers are far more active than others (power-law-ish via exponential weights)
customer_activity_weight = np.random.exponential(scale=1.0, size=N_CUSTOMERS) + 0.05

customer_df = pd.DataFrame({
    "Customer_ID": customer_ids,
    "Customer_Name": customer_names,
    "Customer_Segment": customer_segment,
    "_weight": customer_activity_weight,
})

# ----------------------------------------------------------------------
# Build product master
# ----------------------------------------------------------------------

product_rows = []
for i in range(1, N_PRODUCTS + 1):
    cat = np.random.choice(CATEGORY_NAMES, p=CATEGORY_WEIGHT)
    sub = random.choice(CATEGORIES[cat]["sub"])
    low, high = CATEGORIES[cat]["price_range"]
    price = round(np.random.uniform(low, high), 2)
    name = f"{sub[:-1] if sub.endswith('s') else sub} {random.choice(PRODUCT_ADJ)} {i}"
    product_rows.append({
        "Product_ID": f"PROD-{i:04d}",
        "Product_Name": name,
        "Category": cat,
        "Sub_Category": sub,
        "Unit_Price": price,
        "_base_margin": CATEGORIES[cat]["margin"],
    })
product_df = pd.DataFrame(product_rows)
# A subset of products sell much more than others (best-sellers)
product_popularity = np.random.exponential(scale=1.0, size=N_PRODUCTS) + 0.05
product_df["_weight"] = product_popularity

# ----------------------------------------------------------------------
# Build order-level records
# ----------------------------------------------------------------------

start_date = datetime(2022, 1, 1)
end_date = datetime(2024, 12, 31)
date_range_days = (end_date - start_date).days

# Seasonality: boost sales around Oct-Dec (festive season) and June-July (summer sale)
def seasonal_weight(month):
    boosts = {10: 1.4, 11: 1.5, 12: 1.3, 6: 1.15, 7: 1.15}
    return boosts.get(month, 1.0)

# Pre-generate a pool of dates weighted by seasonality
all_dates = [start_date + timedelta(days=d) for d in range(date_range_days + 1)]
date_weights = np.array([seasonal_weight(d.month) for d in all_dates], dtype=float)
date_weights /= date_weights.sum()

order_dates = np.random.choice(all_dates, size=N_ROWS, p=date_weights)

cust_idx = np.random.choice(
    customer_df.index, size=N_ROWS,
    p=customer_df["_weight"] / customer_df["_weight"].sum()
)
prod_idx = np.random.choice(
    product_df.index, size=N_ROWS,
    p=product_df["_weight"] / product_df["_weight"].sum()
)

chosen_customers = customer_df.loc[cust_idx].reset_index(drop=True)
chosen_products = product_df.loc[prod_idx].reset_index(drop=True)

regions = list(REGIONS.keys())
region_probs = np.array([REGION_WEIGHT[r] for r in regions])
region_probs = region_probs / region_probs.sum()
chosen_region = np.random.choice(regions, size=N_ROWS, p=region_probs)
chosen_city = [random.choice(REGIONS[r]) for r in chosen_region]
chosen_state = [REGION_STATE[c] for c in chosen_city]

quantity = np.random.choice([1, 2, 3, 4, 5, 6], size=N_ROWS,
                             p=[0.40, 0.25, 0.15, 0.10, 0.06, 0.04])

# Discount: mostly small, occasionally large (clearance-style)
discount = np.clip(np.random.beta(2, 8, size=N_ROWS), 0, 0.7)
discount = np.round(discount, 2)

unit_price = chosen_products["Unit_Price"].values
base_margin = chosen_products["_base_margin"].values

sales = np.round(unit_price * quantity * (1 - discount), 2)

# Cost derived from base margin, with noise; higher discount erodes profit further
noise = np.random.normal(0, 0.03, size=N_ROWS)
effective_margin = np.clip(base_margin - discount * 0.6 + noise, -0.15, 0.6)
cost = np.round(sales * (1 - effective_margin), 2)
profit = np.round(sales - cost, 2)

order_id = [f"ORD-{100000 + i}" for i in range(N_ROWS)]

df = pd.DataFrame({
    "Order_ID": order_id,
    "Order_Date": order_dates,
    "Customer_ID": chosen_customers["Customer_ID"],
    "Customer_Name": chosen_customers["Customer_Name"],
    "Customer_Segment": chosen_customers["Customer_Segment"],
    "Product_ID": chosen_products["Product_ID"],
    "Product_Name": chosen_products["Product_Name"],
    "Category": chosen_products["Category"],
    "Sub_Category": chosen_products["Sub_Category"],
    "Region": chosen_region,
    "State": chosen_state,
    "City": chosen_city,
    "Quantity": quantity,
    "Unit_Price": unit_price,
    "Discount": discount,
    "Sales": sales,
    "Cost": cost,
    "Profit": profit,
    "Payment_Mode": np.random.choice(PAYMENT_MODES, size=N_ROWS,
                                      p=[0.28, 0.22, 0.30, 0.12, 0.08]),
    "Shipping_Mode": np.random.choice(SHIPPING_MODES, size=N_ROWS,
                                       p=[0.45, 0.30, 0.10, 0.15]),
})

# ----------------------------------------------------------------------
# Inject a small amount of realistic data-quality issues
# ----------------------------------------------------------------------

rng = np.random.default_rng(SEED)

# 1. Duplicate ~0.6% of rows
dup_n = int(N_ROWS * 0.006)
dup_rows = df.sample(n=dup_n, random_state=SEED)
df = pd.concat([df, dup_rows], ignore_index=True)

# 2. Missing values in a few columns (~1-2%)
for col, frac in [("Customer_Name", 0.01), ("City", 0.008), ("Discount", 0.012), ("Payment_Mode", 0.01)]:
    idx = df.sample(frac=frac, random_state=hash(col) % (2**32)).index
    df.loc[idx, col] = np.nan

# 3. Extra whitespace + inconsistent capitalization in text columns
text_cols = ["Customer_Name", "Category", "Region", "City", "Payment_Mode"]
for col in text_cols:
    idx = df.sample(frac=0.03, random_state=hash(col + "ws") % (2**32)).index
    df.loc[idx, col] = df.loc[idx, col].apply(
        lambda x: (f"  {str(x).upper()}  " if random.random() < 0.5 else f"{str(x).lower()}  ")
        if pd.notna(x) else x
    )

# 4. A few extreme outliers in Sales / Profit
out_idx = df.sample(n=int(N_ROWS * 0.002), random_state=SEED).index
df.loc[out_idx, "Sales"] = df.loc[out_idx, "Sales"] * np.random.uniform(8, 15, size=len(out_idx))
df.loc[out_idx, "Profit"] = df.loc[out_idx, "Profit"] * np.random.uniform(-6, 10, size=len(out_idx))

# Shuffle final rows so duplicates aren't all at the tail
df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

df.to_csv(OUT_PATH, index=False)

print(f"Generated {len(df):,} raw rows -> {OUT_PATH}")
print(df.head(3).to_string())
