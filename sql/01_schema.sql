-- Creates the database and table without deleting existing data.
-- Run: mysql -u root -p < sql/01_schema.sql

CREATE DATABASE IF NOT EXISTS sales_dashboard
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sales_dashboard;

-- Safe to rerun: existing rows and table structure are preserved.
CREATE TABLE IF NOT EXISTS sales_data (
    order_id     INT PRIMARY KEY,
    product      VARCHAR(50) NOT NULL,
    region       VARCHAR(50) NOT NULL,
    sales_rep    VARCHAR(100) NOT NULL,
    quantity     INT NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,
    order_date   DATE NOT NULL,
    total_sales  DECIMAL(12, 2) NOT NULL,
    INDEX idx_region (region),
    INDEX idx_product (product),
    INDEX idx_sales_rep (sales_rep),
    INDEX idx_order_date (order_date)
) ENGINE = InnoDB;

-- This setup script intentionally does not DROP or TRUNCATE data.
-- For a deliberate reset, back up the database and run a separately
-- reviewed reset command.
