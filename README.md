# Sales & Revenue Analysis Dashboard

A full ETL + analytics pipeline that takes a messy sales export, cleans it,
loads it into MySQL, and serves an interactive Streamlit + Plotly dashboard
on top of it.

Built as Task 1 of the Data Analytics internship, with the pipeline
deliberately designed around database-administration fundamentals
(schema design, indexing, bulk loading with `LOAD DATA INFILE`, and
querying through SQLAlchemy) as groundwork for a Database Administrator
track.

## Architecture

```
Raw Excel (.xlsx)
      │
      ▼
etl/clean_data.py  ──────► data/processed/cleaned_sales_data.csv
      │                       (deduped, standardized, validated)
      ▼
etl/load_to_mysql.py ────► MySQL: sales_dashboard.sales_data
   (LOAD DATA LOCAL INFILE      (schema defined in sql/01_schema.sql)
    via SQLAlchemy)
      │
      ▼
dashboard/app.py  ───────► Streamlit + Plotly (reads live via SQLAlchemy)
```

## Project structure

```
sales-revenue-dashboard/
├── README.md
├── requirements.txt
├── .env.example              # copy to .env and fill in DB credentials
├── data/
│   ├── raw/
│   │   └── messy_sales_data.xlsx     # original, untouched source export
│   └── processed/
│       └── cleaned_sales_data.csv    # output of etl/clean_data.py
├── sql/
│   ├── 01_schema.sql          # CREATE DATABASE / CREATE TABLE + indexes
│   ├── 02_load_data.sql       # LOAD DATA INFILE reference script
│   └── 03_analysis_queries.sql # revenue-by-region/product/rep, trends
├── etl/
│   ├── clean_data.py          # Step 1: raw xlsx -> clean CSV
│   ├── db_connection.py       # shared SQLAlchemy engine factory
│   └── load_to_mysql.py       # Step 2: clean CSV -> MySQL table
└── dashboard/
    └── app.py                 # Streamlit + Plotly dashboard
```

## Data cleaning

The raw export (`data/raw/messy_sales_data.xlsx`, 240 rows) has the kind of
mess a real export usually has:

| Issue                                   | Fix applied                                              |
|------------------------------------------|-----------------------------------------------------------|
| Inconsistent casing (`west`, `WEST`, ` West `) | Trimmed, whitespace-collapsed, Title Case               |
| Exact duplicate rows                     | Dropped                                                    |
| Missing `OrderID`                        | Row dropped (can't be a valid primary key)                 |
| Missing `SalesRep`                       | Row dropped (sale can't be attributed)                     |
| Negative/invalid `Quantity`               | Treated as missing, filled with per-product median         |
| Missing `Price`                          | Filled with per-product average price                      |
| Four different date formats in one column | Parsed to a single `DATE` type                             |
| No revenue column                        | Computed `TotalSales = Quantity * Price`                   |

Running `etl/clean_data.py` prints a summary of exactly how many rows were
affected by each rule, so the cleaning is auditable rather than silent.

## 1. Run it on your local machine first

Do this before pushing anywhere, so you know it actually works.

**Prerequisites:** Python 3.10+, MySQL Server installed and running, MySQL Workbench (optional, for a GUI).

1. **Open a terminal in the project folder**
   ```bash
   cd sales-revenue-dashboard
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create the database and table**
   ```bash
   mysql -u root -p < sql/01_schema.sql
   ```
   This creates the `sales_dashboard` database and the `sales_data` table with indexes.

4. **Set your MySQL credentials**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your actual `DB_USER` / `DB_PASSWORD`.

5. **Run the ETL pipeline** — cleans the raw Excel file, then loads it into MySQL
   ```bash
   python etl/clean_data.py
   cd etl
   python load_to_mysql.py
   cd ..
   ```
   This runs `LOAD DATA LOCAL INFILE` under the hood. If MySQL rejects it with
   *"Loading local data is disabled"*, run this once in a MySQL session:
   ```sql
   SET GLOBAL local_infile = 1;
   ```
   or use the fallback: `python load_to_mysql.py --method pandas`

6. **Launch the dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```
   Opens at `http://localhost:8501`. Confirm the KPIs and charts load with real numbers before moving on.

## 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Sales & Revenue Analysis Dashboard"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

The repository includes a `.gitignore` that excludes `.env` and other local or generated files. Use `.env.example` as the template for local MySQL credentials, and never commit real credentials to GitHub.

## Dashboard features

- KPI cards: total revenue, total orders, units sold, average order value
- Revenue by region (bar chart) and by product (donut chart)
- Monthly revenue trend (line chart)
- Sales rep leaderboard (orders closed + revenue)
- Sidebar filters: region, product, date range
- Expandable raw data table for the current filter selection

## Re-running the analysis in plain SQL

`sql/03_analysis_queries.sql` has the same queries the dashboard runs
(revenue by region/product/rep, monthly trend, top orders, region×product
matrix) written as plain SQL, so they can be run directly in MySQL
Workbench without Python at all.

## Possible next steps

- Add a `tests/` suite around `clean_data.py`'s cleaning rules
- Parameterize the date range for a rolling "last 30 days" view
- Add a materialized summary table + a scheduled job (cron / MySQL EVENT)
  to refresh it, as a next step toward more DBA-flavored work
