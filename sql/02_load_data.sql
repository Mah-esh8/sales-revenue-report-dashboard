-- =============================================================
-- 02_load_data.sql
-- Loads the cleaned CSV into MySQL using LOAD DATA INFILE.
--
-- IMPORTANT: replace the file path below with the ABSOLUTE path to
-- data/processed/cleaned_sales_data.csv on your machine. MySQL requires
-- an absolute path (or LOCAL INFILE, see note below).
--
-- If you get "The MySQL server is running with the --secure-file-priv
-- option" -> either copy the CSV into the directory that
-- `SHOW VARIABLES LIKE 'secure_file_priv';` points to, or use the
-- LOAD DATA LOCAL INFILE variant further down.
-- =============================================================

USE sales_dashboard;

-- Standard server-side load (file must be readable by the MySQL server process)
LOAD DATA INFILE '/absolute/path/to/sales-revenue-dashboard/data/processed/cleaned_sales_data.csv'
INTO TABLE sales_data
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, product, region, sales_rep, quantity, price, order_date, total_sales);

-- ---------------------------------------------------------------
-- Alternative: LOAD DATA LOCAL INFILE
-- Use this if the CSV lives on the machine running the mysql client
-- rather than on the DB server itself (common when learning locally).
-- Requires: local_infile=1 on both the client and the server.
--   SET GLOBAL local_infile = 1;
-- and connecting with `mysql --local-infile=1 ...`
-- ---------------------------------------------------------------
-- LOAD DATA LOCAL INFILE '/absolute/path/to/sales-revenue-dashboard/data/processed/cleaned_sales_data.csv'
-- INTO TABLE sales_data
-- FIELDS TERMINATED BY ','
-- OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (order_id, product, region, sales_rep, quantity, price, order_date, total_sales);

-- Quick sanity check after loading
SELECT COUNT(*) AS rows_loaded FROM sales_data;
SELECT * FROM sales_data LIMIT 5;
