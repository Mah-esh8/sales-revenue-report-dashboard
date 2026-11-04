# Sales & Revenue Analysis Dashboard

A database-centred ETL and analytics project that transforms a messy Excel sales export into a structured MySQL database and presents the results through a Streamlit + Plotly dashboard.

The project demonstrates practical database fundamentals relevant to a future Database Administrator (DBA): relational schema design, primary keys, indexing, bulk data loading, safe data replacement, SQL querying, connection management, and data validation.

## Project architecture

\`\`\`text
Raw Excel export
      |
      v
etl/clean_data.py
  - removes duplicates
  - standardizes text and dates
  - handles missing / invalid values
      |
      v
Cleaned CSV
      |
      v
etl/load_to_mysql.py
  - imports into a temporary staging table
  - checks that rows were loaded
  - replaces live rows only after staging succeeds
      |
      v
MySQL: sales_dashboard.sales_data
  - primary key
  - query-supporting indexes
      |
      v
dashboard/app.py
  - SQLAlchemy connection
  - Streamlit filters, KPIs and Plotly charts
\`\`\`

## Technology stack

- **Database:** MySQL, InnoDB
- **Database access:** SQLAlchemy, PyMySQL
- **ETL and data processing:** Python, pandas, NumPy, openpyxl
- **Dashboard:** Streamlit, Plotly
- **Configuration:** python-dotenv and environment variables

## Repository structure

\`\`\`text
sales-revenue-report-dashboard/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── raw/
│   │   └── messy_sales_data.xlsx
│   └── processed/
│       └── cleaned_sales_data.csv       # generated locally
├── sql/
│   ├── 01_schema.sql
│   ├── 02_load_data.sql
│   └── 03_analysis_queries.sql
├── etl/
│   ├── clean_data.py
│   ├── db_connection.py
│   └── load_to_mysql.py
└── dashboard/
    └── app.py
\`\`\`

## Database design

The project uses a single sales fact table for this dataset.

| Column | MySQL type | Purpose |
|---|---|---|
| order_id | INT, primary key | Uniquely identifies each order |
| product | VARCHAR(50) | Product category/name |
| region | VARCHAR(50) | Sales region |
| sales_rep | VARCHAR(100) | Responsible sales representative |
| quantity | INT | Units sold |
| price | DECIMAL(10,2) | Unit price |
| order_date | DATE | Date of order |
| total_sales | DECIMAL(12,2) | Quantity multiplied by price |

Indexes are created for \`region\`, \`product\`, \`sales_rep\`, and \`order_date\` to support the dashboard's common filters and aggregations. Indexes improve suitable reads but add storage and write overhead; index choices should be validated against real query plans and workload.

The schema script uses \`CREATE TABLE IF NOT EXISTS\`. It does **not** drop or truncate an existing table, so rerunning setup will not erase stored rows.

## ETL process

### 1. Extract and clean

The raw workbook is read from \`data/raw/messy_sales_data.xlsx\`. The cleaning step:

- removes fully blank and duplicate rows;
- standardizes text values and whitespace;
- removes rows without an order ID or sales representative;
- handles invalid quantities and missing prices;
- parses mixed date formats and removes invalid dates;
- calculates \`TotalSales = Quantity × Price\`;
- prints a cleaning summary and writes the processed CSV.

Run:

\`\`\`bash
python etl/clean_data.py
\`\`\`

### 2. Load into MySQL

The default loader uses MySQL \`LOAD DATA LOCAL INFILE\`. A pandas-based fallback is also available:

\`\`\`bash
python etl/load_to_mysql.py
python etl/load_to_mysql.py --method pandas
\`\`\`

Both methods use a temporary staging table created from the live table's schema. Data is loaded and counted in staging before the existing rows are replaced. The replacement is performed in a transaction. If the import fails or produces zero rows, the previous live data is left unchanged. The pandas method inserts into the existing schema; it does not use \`to_sql(if_exists="replace")\`, which could discard indexes and constraints.

**LOCAL INFILE note:** The bulk method requires LOCAL INFILE support in the MySQL server and client configuration. The Python client opts in only for the loader connection. The script does not attempt to change the server-wide \`local_infile\` setting. If your server administrator has disabled LOCAL INFILE, use the pandas method or ask the administrator to review the setting for your environment.

## Setup and run

### Prerequisites

- Python 3.10 or later
- MySQL Server 8.x (or a compatible MySQL release)
- Git (optional)
- MySQL Workbench (optional)

### 1. Clone and enter the project

\`\`\`bash
git clone https://github.com/Mah-esh8/sales-revenue-report-dashboard.git
cd sales-revenue-report-dashboard
\`\`\`

### 2. Create a virtual environment

Windows PowerShell:

\`\`\`powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
\`\`\`

macOS / Linux:

\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
\`\`\`

Install dependencies:

\`\`\`bash
python -m pip install -r requirements.txt
\`\`\`

### 3. Configure database credentials

Copy \`.env.example\` to \`.env\` and update the values:

\`\`\`env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_local_password
DB_NAME=sales_dashboard
\`\`\`

Use a dedicated least-privilege MySQL account for regular use rather than a root account where practical. Never commit \`.env\` or real credentials.

### 4. Create the database schema

From the repository root:

\`\`\`bash
mysql -u root -p < sql/01_schema.sql
\`\`\`

Or open \`sql/01_schema.sql\` in MySQL Workbench and execute it. The setup script is safe to rerun and does not delete existing data.

### 5. Run the ETL pipeline

\`\`\`bash
python etl/clean_data.py
python etl/load_to_mysql.py
\`\`\`

If LOCAL INFILE is unavailable:

\`\`\`bash
python etl/load_to_mysql.py --method pandas
\`\`\`

The loader prints the number of rows published. You can independently verify the result in MySQL:

\`\`\`sql
USE sales_dashboard;
SELECT COUNT(*) AS total_rows FROM sales_data;
SELECT * FROM sales_data ORDER BY order_id LIMIT 10;
\`\`\`

### 6. Launch the dashboard

\`\`\`bash
streamlit run dashboard/app.py
\`\`\`

Open the local URL printed by Streamlit (normally \`http://localhost:8501\`).

## Dashboard features

- KPI cards for total revenue, order count, units sold, and average order value;
- revenue by region and product;
- monthly revenue trend;
- sales representative leaderboard;
- region, product, and inclusive date-range filters;
- filtered raw-data view.

The date filter uses an exclusive next-day boundary internally so the entire selected end date is included.

## SQL analysis

\`sql/03_analysis_queries.sql\` contains standalone queries for revenue by region, product and sales representative, monthly trends, top orders, and region/product comparisons. Run them in MySQL Workbench to explore the database without launching the dashboard.

## Database administration concepts demonstrated

1. **Schema creation:** database and table definition with appropriate data types.
2. **Integrity:** primary key and NOT NULL constraints.
3. **Indexing:** indexes for common filter and grouping columns.
4. **Bulk loading:** MySQL \`LOAD DATA LOCAL INFILE\`.
5. **Staging and transactional publishing:** load and validate before replacing live rows.
6. **Connection management:** SQLAlchemy engine and \`pool_pre_ping\`.
7. **Credential handling:** environment-based configuration and URL-safe SQLAlchemy connection construction.
8. **Operational verification:** row-count checks and direct SQL validation.

## Current scope and limitations

- This is a learning and portfolio project, not a production-hardened database service.
- The dataset is a small sales-export sample; performance claims should not be made without benchmarks on larger representative data.
- The current schema is intentionally a single-table analytical model, not a fully normalized transactional sales system.
- Automated test coverage, query-plan benchmarks, backup/restore demonstrations, and database monitoring are potential next steps.
- Screenshots of a successfully running dashboard and verified SQL output should be added after a local end-to-end run.

## Future improvements

- Add automated tests for data cleaning and import validation.
- Compare query plans with \`EXPLAIN ANALYZE\` before and after index changes.
- Add a documented backup and restore exercise.
- Add database users and role-based privileges for application access.
- Add import audit metadata (run time, source file, rows accepted/rejected).
- Evaluate pagination or server-side filtering if the dataset grows.
