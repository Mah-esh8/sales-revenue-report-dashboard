-- =============================================================
-- 03_analysis_queries.sql
-- Reference analytical queries. The Streamlit dashboard runs these
-- same patterns through SQLAlchemy; keeping them here too makes it
-- easy to demo the raw SQL side in MySQL Workbench.
-- =============================================================

USE sales_dashboard;

-- 1. Total revenue and orders by region
SELECT
    region,
    COUNT(*)                AS total_orders,
    SUM(quantity)            AS total_units,
    SUM(total_sales)         AS total_revenue,
    ROUND(AVG(total_sales), 2) AS avg_order_value
FROM sales_data
GROUP BY region
ORDER BY total_revenue DESC;

-- 2. Revenue by product
SELECT
    product,
    SUM(quantity)     AS units_sold,
    SUM(total_sales)  AS total_revenue
FROM sales_data
GROUP BY product
ORDER BY total_revenue DESC;

-- 3. Sales rep leaderboard
SELECT
    sales_rep,
    COUNT(*)          AS orders_closed,
    SUM(total_sales)  AS total_revenue
FROM sales_data
GROUP BY sales_rep
ORDER BY total_revenue DESC;

-- 4. Monthly revenue trend
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    SUM(total_sales)                  AS total_revenue
FROM sales_data
GROUP BY month
ORDER BY month;

-- 5. Top 5 highest-value single orders
SELECT order_id, product, region, sales_rep, total_sales
FROM sales_data
ORDER BY total_sales DESC
LIMIT 5;

-- 6. Region x Product revenue matrix (useful for a heatmap)
SELECT
    region,
    product,
    SUM(total_sales) AS total_revenue
FROM sales_data
GROUP BY region, product
ORDER BY region, product;
