-- ============================================================
-- InsightFlow — SQL Analysis
-- Target: SQLite
-- Table:  sales  (loaded from data/processed/sales_cleaned.csv)
-- ============================================================

-- 1. Total sales and total profit overall
SELECT
    ROUND(SUM(Sales), 2)  AS total_sales,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND(SUM(Profit) * 100.0 / SUM(Sales), 2) AS profit_margin_pct
FROM sales;

-- 2. Total orders and average order value
SELECT
    COUNT(DISTINCT Order_ID) AS total_orders,
    ROUND(SUM(Sales) * 1.0 / COUNT(DISTINCT Order_ID), 2) AS avg_order_value
FROM sales;

-- 3. Sales and profit by category
SELECT
    Category,
    ROUND(SUM(Sales), 2)  AS total_sales,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND(SUM(Profit) * 100.0 / SUM(Sales), 2) AS profit_margin_pct
FROM sales
GROUP BY Category
ORDER BY total_sales DESC;

-- 4. Sales by region
SELECT
    Region,
    ROUND(SUM(Sales), 2) AS total_sales,
    COUNT(DISTINCT Order_ID) AS orders
FROM sales
GROUP BY Region
ORDER BY total_sales DESC;

-- 5. Monthly sales trend
SELECT
    strftime('%Y-%m', Order_Date) AS year_month,
    ROUND(SUM(Sales), 2) AS total_sales,
    ROUND(SUM(Profit), 2) AS total_profit
FROM sales
GROUP BY year_month
ORDER BY year_month;

-- 6. Top 10 products by sales
SELECT
    Product_ID,
    Product_Name,
    ROUND(SUM(Sales), 2) AS total_sales
FROM sales
GROUP BY Product_ID, Product_Name
ORDER BY total_sales DESC
LIMIT 10;

-- 7. Top 10 customers by revenue
SELECT
    Customer_ID,
    Customer_Name,
    ROUND(SUM(Sales), 2) AS total_sales,
    COUNT(DISTINCT Order_ID) AS orders
FROM sales
GROUP BY Customer_ID, Customer_Name
ORDER BY total_sales DESC
LIMIT 10;

-- 8. Repeat vs one-time customers (using HAVING)
SELECT
    CASE WHEN order_count > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
    COUNT(*) AS num_customers
FROM (
    SELECT Customer_ID, COUNT(DISTINCT Order_ID) AS order_count
    FROM sales
    GROUP BY Customer_ID
    HAVING order_count >= 1
)
GROUP BY customer_type;

-- 9. Products ranked within each category by sales (window function)
SELECT *
FROM (
    SELECT
        Category,
        Product_Name,
        ROUND(SUM(Sales), 2) AS product_sales,
        RANK() OVER (PARTITION BY Category ORDER BY SUM(Sales) DESC) AS category_rank
    FROM sales
    GROUP BY Category, Product_Name
)
WHERE category_rank <= 3
ORDER BY Category, category_rank;

-- 10. Customers ranked by lifetime revenue (window function, dense rank)
SELECT
    Customer_ID,
    Customer_Name,
    ROUND(SUM(Sales), 2) AS lifetime_sales,
    DENSE_RANK() OVER (ORDER BY SUM(Sales) DESC) AS revenue_rank
FROM sales
GROUP BY Customer_ID, Customer_Name
ORDER BY revenue_rank
LIMIT 20;

-- 11. Category profit contribution using a CTE
WITH category_totals AS (
    SELECT Category, SUM(Profit) AS category_profit
    FROM sales
    GROUP BY Category
),
grand_total AS (
    SELECT SUM(category_profit) AS total_profit FROM category_totals
)
SELECT
    c.Category,
    ROUND(c.category_profit, 2) AS category_profit,
    ROUND(c.category_profit * 100.0 / g.total_profit, 2) AS pct_of_total_profit
FROM category_totals c, grand_total g
ORDER BY category_profit DESC;

-- 12. Discount bucket vs average profit margin (CASE)
SELECT
    CASE
        WHEN Discount = 0 THEN '0% (No discount)'
        WHEN Discount <= 0.1 THEN '0-10%'
        WHEN Discount <= 0.25 THEN '10-25%'
        WHEN Discount <= 0.4 THEN '25-40%'
        ELSE '40%+'
    END AS discount_bucket,
    ROUND(AVG(Profit_Margin) * 100, 2) AS avg_profit_margin_pct,
    COUNT(*) AS num_orders
FROM sales
GROUP BY discount_bucket
ORDER BY MIN(Discount);

-- 13. Month-over-month sales growth using a CTE + window LAG function
WITH monthly AS (
    SELECT
        strftime('%Y-%m', Order_Date) AS year_month,
        SUM(Sales) AS total_sales
    FROM sales
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(total_sales, 2) AS total_sales,
    ROUND(
        (total_sales - LAG(total_sales) OVER (ORDER BY year_month))
        * 100.0 / LAG(total_sales) OVER (ORDER BY year_month), 2
    ) AS mom_growth_pct
FROM monthly
ORDER BY year_month;

-- 14. Top region per category (window function + HAVING-style filter via QUALIFY-alternative)
SELECT Category, Region, total_sales
FROM (
    SELECT
        Category,
        Region,
        SUM(Sales) AS total_sales,
        ROW_NUMBER() OVER (PARTITION BY Category ORDER BY SUM(Sales) DESC) AS rn
    FROM sales
    GROUP BY Category, Region
)
WHERE rn = 1
ORDER BY total_sales DESC;

-- 15. Loss-making products (negative total profit), ordered worst first
SELECT
    Product_ID,
    Product_Name,
    Category,
    ROUND(SUM(Profit), 2) AS total_profit
FROM sales
GROUP BY Product_ID, Product_Name, Category
HAVING total_profit < 0
ORDER BY total_profit ASC;
