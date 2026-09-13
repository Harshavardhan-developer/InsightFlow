"""
InsightFlow — Sales & Customer Data Analytics
A single-page Streamlit application (premium, Apple-inspired UI) that
presents the sales/profit/customer/RFM analysis built on top of the
synthetic dataset in data/processed/sales_cleaned.csv.
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "analysis"))
import analysis as an  # noqa: E402

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="InsightFlow — Sales & Customer Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Apple-inspired minimal styling
# ----------------------------------------------------------------------

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .main {
            background-color: #fbfbfd;
        }

        /* Hero */
        .hero-title {
            font-size: 3.1rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #1d1d1f;
            margin-bottom: 0.2rem;
            animation: fadeIn 0.6s ease-in-out;
        }
        .hero-subtitle {
            font-size: 1.15rem;
            font-weight: 400;
            color: #6e6e73;
            max-width: 700px;
            line-height: 1.5;
            animation: fadeIn 0.9s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* KPI cards */
        .kpi-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 1.4rem 1.5rem;
            border: 1px solid #eeeeef;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }
        .kpi-label {
            font-size: 0.82rem;
            font-weight: 500;
            color: #86868b;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }
        .kpi-value {
            font-size: 1.65rem;
            font-weight: 700;
            color: #1d1d1f;
            letter-spacing: -0.01em;
        }

        /* Section headers */
        .section-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1d1d1f;
            letter-spacing: -0.02em;
            margin-top: 0.5rem;
            margin-bottom: 0.2rem;
        }
        .section-sub {
            color: #6e6e73;
            font-size: 0.95rem;
            margin-bottom: 1.2rem;
        }

        /* Insight cards */
        .insight-card {
            background: #ffffff;
            border-left: 3px solid #1d1d1f;
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.7rem;
            font-size: 0.96rem;
            color: #1d1d1f;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }

        [data-testid="stSidebar"] {
            background-color: #f5f5f7;
            border-right: 1px solid #eaeaea;
        }

        div[data-baseweb="tab-list"] { gap: 4px; }

        hr { border: none; border-top: 1px solid #eaeaea; margin: 1.2rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# Data loading (cached)
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_data():
    return an.load_data()


@st.cache_data(show_spinner=False)
def get_quality_summary():
    try:
        return pd.read_csv("data/processed/data_quality_summary.csv").iloc[0].to_dict()
    except FileNotFoundError:
        return None


df_full = get_data()
quality = get_quality_summary()

# ----------------------------------------------------------------------
# Sidebar — filters
# ----------------------------------------------------------------------

st.sidebar.markdown("### 📊 InsightFlow")
st.sidebar.caption("Sales & Customer Data Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("#### Filters")

min_date, max_date = df_full["Order_Date"].min(), df_full["Order_Date"].max()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

regions = sorted(df_full["Region"].dropna().unique().tolist())
sel_regions = st.sidebar.multiselect("Region", regions, default=regions)

categories = sorted(df_full["Category"].dropna().unique().tolist())
sel_categories = st.sidebar.multiselect("Category", categories, default=categories)

segments = sorted(df_full["Customer_Segment"].dropna().unique().tolist())
sel_segments = st.sidebar.multiselect("Customer Segment", segments, default=segments)

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Sales", "Profitability", "Customers", "Products",
     "Regions", "RFM Analysis", "Business Insights"],
)

# Apply filters
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
else:
    start_d, end_d = min_date.date(), max_date.date()

mask = (
    (df_full["Order_Date"].dt.date >= start_d)
    & (df_full["Order_Date"].dt.date <= end_d)
    & (df_full["Region"].isin(sel_regions))
    & (df_full["Category"].isin(sel_categories))
    & (df_full["Customer_Segment"].isin(sel_segments))
)
df = df_full[mask].copy()

if df.empty:
    st.warning("No data matches the selected filters. Adjust filters in the sidebar.")
    st.stop()

CHART_TEMPLATE = "plotly_white"
COLOR_SEQ = ["#1d1d1f", "#0071e3", "#86868b", "#34c759", "#ff9500", "#ff3b30"]


def kpi_card(label, value):
    st.markdown(
        f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div></div>""",
        unsafe_allow_html=True,
    )


def section(title, subtitle=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


# ========================================================================
# PAGE: OVERVIEW
# ========================================================================

if page == "Overview":
    st.markdown('<div class="hero-title">Understand your business<br>through data.</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Explore sales, customers, products and profitability '
        'in one intelligent analytics workspace.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Total Sales", f"₹{an.total_sales(df):,.0f}")
    with c2:
        kpi_card("Total Profit", f"₹{an.total_profit(df):,.0f}")
    with c3:
        kpi_card("Profit Margin", f"{an.overall_profit_margin(df)*100:.1f}%")

    c4, c5, c6 = st.columns(3)
    with c4:
        kpi_card("Orders", f"{an.total_orders(df):,}")
    with c5:
        kpi_card("Customers", f"{an.total_customers(df):,}")
    with c6:
        kpi_card("Avg Order Value", f"₹{an.avg_order_value(df):,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)
    section("Sales & Profit Trend", "Monthly revenue and profit across the selected period")

    m = an.monthly_sales(df)
    p = df.groupby(df["Order_Date"].dt.to_period("M"))["Profit"].sum().reset_index()
    p["Order_Date"] = p["Order_Date"].dt.to_timestamp()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["Month"], y=m["Sales"], name="Sales", mode="lines",
                              line=dict(color="#0071e3", width=3), fill="tozeroy",
                              fillcolor="rgba(0,113,227,0.08)"))
    fig.add_trace(go.Scatter(x=p["Order_Date"], y=p["Profit"], name="Profit", mode="lines",
                              line=dict(color="#34c759", width=2, dash="dot")))
    fig.update_layout(template=CHART_TEMPLATE, height=380, margin=dict(l=10, r=10, t=10, b=10),
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Category Performance")
        cat = an.sales_by_category(df)
        fig = px.bar(cat, x="Sales", y="Category", orientation="h", color_discrete_sequence=["#1d1d1f"])
        fig.update_layout(template=CHART_TEMPLATE, height=320, margin=dict(l=10, r=10, t=10, b=10),
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        section("Regional Performance")
        reg = an.sales_by_region(df)
        fig = px.pie(reg, names="Region", values="Sales", hole=0.55,
                     color_discrete_sequence=COLOR_SEQ)
        fig.update_layout(template=CHART_TEMPLATE, height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)


# ========================================================================
# PAGE: SALES
# ========================================================================

elif page == "Sales":
    section("Sales Analysis", "Revenue trends across time, category and geography")

    c1, c2, c3 = st.columns(3)
    kpi_card_ph = c1.empty()
    with c1:
        kpi_card("Total Sales", f"₹{an.total_sales(df):,.0f}")
    with c2:
        kpi_card("Total Orders", f"{an.total_orders(df):,}")
    with c3:
        kpi_card("Avg Order Value", f"₹{an.avg_order_value(df):,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Monthly Trend", "By Category / Region", "Top Products"])

    with tab1:
        m = an.monthly_sales(df)
        fig = px.line(m, x="Month", y="Sales", markers=True, color_discrete_sequence=["#0071e3"])
        fig.update_layout(template=CHART_TEMPLATE, height=400)
        st.plotly_chart(fig, use_container_width=True)

        y = an.yearly_sales(df)
        fig2 = px.bar(y, x="Year", y="Sales", color_discrete_sequence=["#1d1d1f"])
        fig2.update_layout(template=CHART_TEMPLATE, height=320, title="Yearly Sales")
        st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            cat = an.sales_by_category(df)
            fig = px.bar(cat, x="Category", y="Sales", color="Category", color_discrete_sequence=COLOR_SEQ)
            fig.update_layout(template=CHART_TEMPLATE, height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            reg = an.sales_by_region(df)
            fig = px.bar(reg, x="Region", y="Sales", color="Region", color_discrete_sequence=COLOR_SEQ)
            fig.update_layout(template=CHART_TEMPLATE, height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        top = an.top_products(df, n=10)
        fig = px.bar(top, x="Sales", y="Product_Name", orientation="h",
                      color_discrete_sequence=["#0071e3"])
        fig.update_layout(template=CHART_TEMPLATE, height=420,
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top.rename(columns={"Sales": "Total Sales"}), use_container_width=True, hide_index=True)


# ========================================================================
# PAGE: PROFITABILITY
# ========================================================================

elif page == "Profitability":
    section("Profitability Analysis", "Where the business makes — and loses — money")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Total Profit", f"₹{an.total_profit(df):,.0f}")
    with c2:
        kpi_card("Profit Margin", f"{an.overall_profit_margin(df)*100:.1f}%")
    with c3:
        loss_count = int((df.groupby("Product_ID")["Profit"].sum() < 0).sum())
        kpi_card("Loss-Making Products", f"{loss_count}")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["By Category / Region", "Top & Bottom Products", "Discount vs Profit"])

    with tab1:
        colA, colB = st.columns(2)
        with colA:
            pc = an.profit_by_category(df)
            fig = px.bar(pc, x="Category", y="Profit", color_discrete_sequence=["#34c759"])
            fig.update_layout(template=CHART_TEMPLATE, height=380, title="Profit by Category")
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            pr = an.profit_by_region(df)
            fig = px.bar(pr, x="Region", y="Profit", color_discrete_sequence=["#0071e3"])
            fig.update_layout(template=CHART_TEMPLATE, height=380, title="Profit by Region")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Top Profitable Products**")
            top_p = an.top_profitable_products(df, n=10)
            st.dataframe(top_p.rename(columns={"Profit": "Total Profit"}), use_container_width=True, hide_index=True)
        with colB:
            st.markdown("**Loss-Making Products**")
            loss_p = an.loss_making_products(df, n=10)
            st.dataframe(loss_p.rename(columns={"Profit": "Total Profit"}), use_container_width=True, hide_index=True)

    with tab3:
        dvp = an.discount_vs_profit(df)
        fig = px.bar(dvp, x="Discount_Bin", y="Avg_Profit_Margin",
                      color_discrete_sequence=["#ff9500"])
        fig.update_layout(template=CHART_TEMPLATE, height=400,
                           yaxis_tickformat=".0%", title="Average Profit Margin by Discount Level")
        st.plotly_chart(fig, use_container_width=True)

        corr = df[["Discount", "Profit_Margin"]].corr().iloc[0, 1]
        st.caption(f"Correlation between Discount and Profit Margin: **{corr:.2f}**")


# ========================================================================
# PAGE: CUSTOMERS
# ========================================================================

elif page == "Customers":
    section("Customer Analysis", "Who buys, how often, and how much")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Total Customers", f"{an.total_customers(df):,}")
    with c2:
        kpi_card("Repeat Customers", f"{an.repeat_customers(df):,}")
    with c3:
        kpi_card("One-time Customers", f"{an.one_time_customers(df):,}")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Top Customers", "Revenue / Profit per Customer"])

    with tab1:
        top_c = an.top_customers(df, n=10)
        fig = px.bar(top_c, x="Sales", y="Customer_Name", orientation="h",
                      color_discrete_sequence=["#1d1d1f"])
        fig.update_layout(template=CHART_TEMPLATE, height=420,
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_c.rename(columns={"Sales": "Total Sales"}), use_container_width=True, hide_index=True)

    with tab2:
        rev = an.revenue_per_customer(df)
        fig = px.histogram(rev, x="Sales", nbins=40, color_discrete_sequence=["#0071e3"])
        fig.update_layout(template=CHART_TEMPLATE, height=380, title="Distribution of Revenue per Customer")
        st.plotly_chart(fig, use_container_width=True)

        seg_counts = df.groupby("Customer_Segment")["Customer_ID"].nunique().reset_index()
        fig2 = px.pie(seg_counts, names="Customer_Segment", values="Customer_ID", hole=0.5,
                       color_discrete_sequence=COLOR_SEQ)
        fig2.update_layout(template=CHART_TEMPLATE, height=380, title="Customers by Segment")
        st.plotly_chart(fig2, use_container_width=True)


# ========================================================================
# PAGE: PRODUCTS
# ========================================================================

elif page == "Products":
    section("Product Performance", "Category, sub-category and product-level performance")

    tab1, tab2 = st.tabs(["Category / Sub-category", "Top & Bottom Products"])

    with tab1:
        cat_perf = an.category_performance(df)
        fig = px.bar(cat_perf, x="Category", y=["Sales", "Profit"], barmode="group",
                      color_discrete_sequence=["#1d1d1f", "#34c759"])
        fig.update_layout(template=CHART_TEMPLATE, height=380, title="Category: Sales vs Profit")
        st.plotly_chart(fig, use_container_width=True)

        sub_perf = an.subcategory_performance(df)
        fig2 = px.treemap(sub_perf, path=["Category", "Sub_Category"], values="Sales",
                           color="Profit_Margin", color_continuous_scale="Blues")
        fig2.update_layout(height=420, title="Sub-Category Sales (size) & Margin (color)")
        st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Top 10 Products (Sales)**")
            st.dataframe(an.top_products(df, n=10).rename(columns={"Sales": "Total Sales"}),
                         use_container_width=True, hide_index=True)
        with colB:
            st.markdown("**Bottom 10 Products (Sales)**")
            st.dataframe(an.bottom_products(df, n=10).rename(columns={"Sales": "Total Sales"}),
                         use_container_width=True, hide_index=True)


# ========================================================================
# PAGE: REGIONS
# ========================================================================

elif page == "Regions":
    section("Regional Analysis", "Sales and profit across regions, states and cities")

    tab1, tab2 = st.tabs(["Region Overview", "State / City Breakdown"])

    with tab1:
        colA, colB = st.columns(2)
        with colA:
            reg = an.sales_by_region(df)
            fig = px.bar(reg, x="Region", y="Sales", color="Region", color_discrete_sequence=COLOR_SEQ)
            fig.update_layout(template=CHART_TEMPLATE, height=380, showlegend=False, title="Sales by Region")
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            pr = an.profit_by_region(df)
            fig = px.bar(pr, x="Region", y="Profit", color="Region", color_discrete_sequence=COLOR_SEQ)
            fig.update_layout(template=CHART_TEMPLATE, height=380, showlegend=False, title="Profit by Region")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        state = an.state_sales(df).head(15)
        fig = px.bar(state, x="Sales", y="State", orientation="h", color_discrete_sequence=["#0071e3"])
        fig.update_layout(template=CHART_TEMPLATE, height=420, title="Top 15 States by Sales",
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

        city = an.city_sales(df).head(15)
        fig2 = px.bar(city, x="Sales", y="City", orientation="h", color_discrete_sequence=["#1d1d1f"])
        fig2.update_layout(template=CHART_TEMPLATE, height=420, title="Top 15 Cities by Sales",
                            yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig2, use_container_width=True)


# ========================================================================
# PAGE: RFM ANALYSIS
# ========================================================================

elif page == "RFM Analysis":
    section("RFM Analysis", "Recency, Frequency, Monetary segmentation of the customer base")

    rfm = an.rfm_analysis(df)
    summary = an.rfm_segment_summary(rfm, df)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Segments", f"{summary.shape[0]}")
    with c2:
        kpi_card("Champions", f"{int(summary.loc[summary['Segment']=='Champions','Customers'].sum()):,}")
    with c3:
        kpi_card("At Risk / Lost", f"{int(summary.loc[summary['Segment'].isin(['At Risk','Lost Customers']),'Customers'].sum()):,}")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Segment Overview", "Customer Detail"])

    with tab1:
        colA, colB = st.columns(2)
        with colA:
            fig = px.bar(summary, x="Segment", y="Customers", color="Segment", color_discrete_sequence=COLOR_SEQ)
            fig.update_layout(template=CHART_TEMPLATE, height=380, showlegend=False, title="Customers per Segment")
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            fig2 = px.pie(summary, names="Segment", values="Revenue", hole=0.5, color_discrete_sequence=COLOR_SEQ)
            fig2.update_layout(template=CHART_TEMPLATE, height=380, title="Revenue Share by Segment")
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(
            summary.rename(columns={"Revenue": "Total Revenue", "Profit": "Total Profit"}),
            use_container_width=True, hide_index=True,
        )

    with tab2:
        seg_filter = st.multiselect("Filter by segment", sorted(rfm["Segment"].unique()),
                                     default=sorted(rfm["Segment"].unique()))
        st.dataframe(
            rfm[rfm["Segment"].isin(seg_filter)].sort_values("Monetary", ascending=False),
            use_container_width=True, hide_index=True, height=420,
        )


# ========================================================================
# PAGE: BUSINESS INSIGHTS
# ========================================================================

elif page == "Business Insights":
    section("Business Insights", "Automatically generated from the current filtered dataset")

    insights = an.generate_insights(df)
    for ins in insights:
        st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section("Data Quality", "Snapshot of the raw-to-clean transformation")

    if quality:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Raw Records", f"{int(quality['raw_records']):,}")
        with c2:
            kpi_card("Clean Records", f"{int(quality['clean_records']):,}")
        with c3:
            kpi_card("Duplicates Removed", f"{int(quality['duplicates_removed']):,}")
        with c4:
            kpi_card("Missing Values Handled", f"{int(quality['missing_values_handled']):,}")
        with c5:
            kpi_card("Rows Removed", f"{int(quality['rows_removed_total']):,}")
    else:
        st.info("Run scripts/clean_data.py to generate the data quality summary.")

    st.markdown("<br>", unsafe_allow_html=True)
    section("Descriptive Statistics")
    stats_col = st.selectbox("Column", ["Sales", "Profit", "Quantity", "Discount", "Profit_Margin"])
    stats = an.descriptive_stats(df, stats_col)
    c1, c2, c3, c4, c5 = st.columns(5)
    for c, (k, v) in zip([c1, c2, c3, c4, c5], stats.items()):
        with c:
            kpi_card(k.title(), f"{v:,.2f}")

    corr = an.correlation_matrix(df)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="Blues", aspect="auto")
    fig.update_layout(height=420, title="Correlation Matrix")
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------

st.markdown("---")
st.caption("InsightFlow · Built with Python, Pandas, SQLite & Streamlit · Synthetic demo dataset")
