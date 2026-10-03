# InsightFlow — Sales & Customer Data Analytics

A end-to-end data analytics portfolio project: synthetic data generation →
cleaning → EDA/statistics → RFM segmentation → SQL analysis → an
interactive, Apple-inspired **Streamlit** dashboard.

**Live workflow:** raw CSV → cleaned CSV → SQLite → analysis functions →
Streamlit UI. Nothing in the dashboard is hard-coded — every KPI, chart,
and insight is computed dynamically from the data.

---

## 1. Project Overview

InsightFlow simulates a retail/e-commerce sales analytics workspace. It
answers the kinds of questions a real business analyst is asked daily:
*Which category drives revenue? Which customers are at risk of
churning? Does discounting hurt margins? Which region should we invest
in next?*

## 2. Business Problem

A retail business has three years of order-level sales data but no easy
way to see trends, spot its best/worst products, or understand customer
loyalty. InsightFlow turns raw transactional data into an executive-ready
analytics dashboard — sales trends, profitability, customer segmentation,
and automatically generated business recommendations.

## 3. Dataset

- **~100,000 synthetic sales records**, generated with a fixed random
  seed (fully reproducible, no external download).
- Columns: order, customer, product, region/state/city, quantity, price,
  discount, sales, cost, profit, payment mode, shipping mode.
- Built-in realistic business logic: seasonality (festive-season spikes),
  category-level margins, discount → profit erosion, power-law customer
  activity and product popularity, and regional performance differences.
- Deliberately includes a small amount of realistic mess: missing values,
  duplicate rows, inconsistent capitalization, extra whitespace, and a
  handful of outliers — so the cleaning step has real work to do.

## 4. Data Cleaning (`scripts/clean_data.py`)

- Removes duplicate rows
- Handles missing values (imputation / sensible defaults)
- Fixes data types (dates, numerics)
- Cleans and standardizes text columns
- Filters out logically invalid values (negative prices, >90% discount, etc.)
- Winsorizes extreme outliers in Sales/Profit using the IQR method
- Adds derived columns: `Year`, `Month`, `Quarter`, `Month_Name`,
  `Order_Value`, `Profit_Margin`
- Prints before/after row counts, missing values, and duplicate counts,
  and saves a `data_quality_summary.csv` used by the dashboard

## 5. Analysis (`analysis/analysis.py`)

Pandas/NumPy-based functions covering:

- **Sales:** totals, orders, AOV, monthly/yearly trends, category/region
  breakdowns, top products
- **Profit:** totals, margin, category/region breakdowns, top & loss-making
  products, discount-vs-profit relationship
- **Customers:** counts, repeat vs one-time, top customers, revenue/profit
  per customer
- **Products:** top/bottom performers, category & sub-category performance
- **Regions:** region/state/city sales & profit
- **Time:** monthly/quarterly/yearly trends, month-over-month growth
- **Statistics:** mean/median/std, correlation matrix, IQR outlier detection

These same functions power both the console report (`python analysis/analysis.py`)
and the Streamlit dashboard — single source of truth, no duplicated logic.

## 6. RFM Analysis

Customers are scored on **Recency, Frequency, Monetary** value (1–5
quantile scores) and segmented into:

`Champions` · `Loyal Customers` · `Potential Loyalists` · `New Customers` ·
`At Risk` · `Lost Customers`

Each segment is summarized by customer count, total revenue, and total
profit — visible on the **RFM Analysis** page of the dashboard.

## 7. SQL (`sql/analysis.sql`)

15 SQLite queries covering totals, category/region breakdowns, monthly
trends, top products/customers, repeat-customer analysis, and more —
using `GROUP BY`, `HAVING`, `CASE`, `CTE`s, and window functions
(`RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LAG`). All 15 queries have been
verified to execute successfully against the generated database.

## 8. Visualizations

Interactive Plotly charts throughout the dashboard: trend lines, bar
charts, pie/donut charts, a treemap (sub-category sales & margin), a
histogram (revenue distribution), and a correlation heatmap — all filter
dynamically with the sidebar controls.

## 9. Key Findings

*(Exact numbers depend on the generated seed/filters — see the
**Business Insights** page for live, dynamically computed figures.)*

- Electronics is the highest-revenue category; Home Appliances runs the
  thinnest margin.
- Discount level is negatively correlated with profit margin — heavy
  discounting materially erodes profitability in certain categories.
- The customer base skews toward a small number of high-frequency
  "Champion" customers who account for a disproportionate share of revenue.
- Sales are seasonal, with a clear festive-season (Oct–Dec) uplift.

## 10. Technology Stack

Python · Pandas · NumPy · SciPy · SQLite · Plotly · Matplotlib · Seaborn ·
Streamlit

---

## 11. How to Run Locally (Fastest Path)

```bash
# 1. Clone / unzip the project, then move into it
cd InsightFlow

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Data is already generated — data/raw & data/processed are included.
#     Only regenerate if you want a fresh dataset/reset:)
python scripts/generate_data.py
python scripts/clean_data.py

# 5. Launch the dashboard
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**.

Optional — rebuild the SQLite DB and verify all SQL queries:
```bash
python scripts/build_and_check_sql.py
```
Optional — run the standalone console analysis report:
```bash
python analysis/analysis.py
```

## 12. How to Push to GitHub

```bash
git init
git add .
git commit -m "InsightFlow: sales & customer analytics dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/InsightFlow.git
git push -u origin main
```

## 13. How to Deploy to Streamlit Community Cloud

1. Push the project to a public (or private) GitHub repository (step 12).
2. Go to **https://share.streamlit.io** and sign in with GitHub.
3. Click **"New app"** → select your `InsightFlow` repository and the
   `main` branch.
4. Set **Main file path** to `app.py`.
5. Click **Deploy**. Streamlit Cloud will install `requirements.txt`
   automatically and launch the app — no other configuration needed.
6. Any future `git push` to `main` auto-redeploys the app.

