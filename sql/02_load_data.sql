-- Manual reference for a safe LOCAL INFILE import.
-- Replace the path with the absolute path on the MySQL client machine.
-- Recommended: run python etl/load_to_mysql.py instead; it stages and
-- validates the CSV before replacing the live rows.
--
-- LOCAL INFILE must be allowed by both server and client configuration.
-- Do not change a shared/production server-wide setting casually.

USE sales_dashboard;

DROP TEMPORARY TABLE IF EXISTS sales_data_staging;
CREATE TEMPORARY TABLE sales_data_staging LIKE sales_data;

LOAD DATA LOCAL INFILE '/absolute/path/to/cleaned_sales_data.csv'
INTO TABLE sales_data_staging
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, product, region, sales_rep, quantity, price, order_date, total_sales);

-- Inspect before publishing.
SELECT COUNT(*) AS staged_rows FROM sales_data_staging;
SELECT * FROM sales_data_staging LIMIT 5;

-- Execute only after confirming the staged data. sales_data is InnoDB.
START TRANSACTION;
DELETE FROM sales_data;
INSERT INTO sales_data
    (order_id, product, region, sales_rep, quantity, price, order_date, total_sales)
SELECT
    order_id, product, region, sales_rep, quantity, price, order_date, total_sales
FROM sales_data_staging;
COMMIT;

SELECT COUNT(*) AS rows_published FROM sales_data;
