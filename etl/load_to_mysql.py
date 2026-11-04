"""Safely load the cleaned sales CSV into MySQL.

Rows are imported into a temporary staging table first. The live table is
replaced only after staging succeeds, preserving the existing data on failure.
Run commands from the repository root.
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db_connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_ROOT / "data" / "processed" / "cleaned_sales_data.csv"
SOURCE_COLUMNS = (
    "OrderID", "Product", "Region", "SalesRep",
    "Quantity", "Price", "OrderDate", "TotalSales",
)
COLUMNS = (
    "order_id", "product", "region", "sales_rep",
    "quantity", "price", "order_date", "total_sales",
)
COLUMN_SQL = ", ".join(COLUMNS)
INSERT_SQL = text(
    "INSERT INTO sales_data (" + COLUMN_SQL + ") "
    "SELECT " + COLUMN_SQL + " FROM sales_data_staging"
)
INSERT_VALUES_SQL = text("""
    INSERT INTO sales_data_staging
        (order_id, product, region, sales_rep, quantity, price, order_date, total_sales)
    VALUES
        (:order_id, :product, :region, :sales_rep, :quantity, :price, :order_date, :total_sales)
""")


def _prepare_staging_table(conn) -> None:
    conn.execute(text("DROP TEMPORARY TABLE IF EXISTS sales_data_staging"))
    conn.execute(text("CREATE TEMPORARY TABLE sales_data_staging LIKE sales_data"))


def _publish_staged_rows(conn) -> int:
    staged_count = conn.execute(
        text("SELECT COUNT(*) FROM sales_data_staging")
    ).scalar_one()
    if staged_count == 0:
        raise ValueError("The CSV produced zero rows; existing data was not changed.")

    conn.execute(text("DELETE FROM sales_data"))
    conn.execute(INSERT_SQL)
    return staged_count


def load_via_infile(csv_path: Path, engine) -> None:
    resolved_path = csv_path.resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {resolved_path}")

    sql_path = resolved_path.as_posix().replace("'", "''")
    load_sql = f"""
        LOAD DATA LOCAL INFILE '{sql_path}'
        INTO TABLE sales_data_staging
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        IGNORE 1 ROWS
        (order_id, product, region, sales_rep, quantity, price, order_date, total_sales)
    """
    with engine.begin() as conn:
        _prepare_staging_table(conn)
        conn.exec_driver_sql(load_sql)
        loaded = _publish_staged_rows(conn)
    print(f"Bulk load complete. Rows published: {loaded}")


def load_via_pandas(csv_path: Path, engine) -> None:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if tuple(df.columns) != SOURCE_COLUMNS:
        raise ValueError(
            "Unexpected CSV headers. Expected: " + ", ".join(SOURCE_COLUMNS)
        )
    if df.empty:
        raise ValueError("The CSV is empty; existing data was not changed.")

    # Map the cleaner's original Excel-style headers to the SQL schema.
    df.columns = COLUMNS
    df["order_date"] = pd.to_datetime(df["order_date"], errors="raise").dt.date
    records = df.astype(object).where(pd.notna(df), None).to_dict(orient="records")

    with engine.begin() as conn:
        _prepare_staging_table(conn)
        conn.execute(INSERT_VALUES_SQL, records)
        loaded = _publish_staged_rows(conn)
    print(f"pandas load complete. Rows published: {loaded}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load cleaned sales CSV into MySQL safely.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to cleaned CSV")
    parser.add_argument(
        "--method",
        choices=("load_data_infile", "pandas"),
        default="load_data_infile",
        help="Bulk loader (default) or pandas-based fallback",
    )
    args = parser.parse_args()

    engine = get_engine(local_infile=args.method == "load_data_infile")
    try:
        if args.method == "load_data_infile":
            load_via_infile(args.csv, engine)
        else:
            load_via_pandas(args.csv, engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
