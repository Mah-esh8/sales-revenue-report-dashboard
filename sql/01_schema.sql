-- =============================================================
-- 01_schema.sql
-- Creates the database and the sales_data table.
-- Run this first in MySQL Workbench (or `mysql -u root -p < sql/01_schema.sql`).
-- =============================================================

CREATE DATABASE IF NOT EXISTS sales_dashboard
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sales_dashboard;

DROP TABLE IF EXISTS sales_data;

CREATE TABLE sales_data (
    order_id     INT PRIMARY KEY,
    product      VARCHAR(50)  NOT NULL,
    region       VARCHAR(50)  NOT NULL,
    sales_rep    VARCHAR(100) NOT NULL,
    quantity     INT          NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,
    order_date   DATE         NOT NULL,
    total_sales  DECIMAL(12, 2) NOT NULL,

    -- Indexes to speed up the exact GROUP BY / filter patterns the
    -- dashboard and the analysis queries use.
    INDEX idx_region (region),
    INDEX idx_product (product),
    INDEX idx_sales_rep (sales_rep),
    INDEX idx_order_date (order_date)
) ENGINE = InnoDB;
