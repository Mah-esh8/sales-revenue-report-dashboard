"""
etl/load_to_mysql.py
---------------------
Step 2 of the pipeline: loads the cleaned CSV into MySQL.

Two modes are supported:
  --method load_data_infile   (default) Runs LOAD DATA LOCAL INFILE through
                               the SQLAlchemy connection. This is the
                               fastest way MySQL can bulk-load a file and
                               is the technique most worth practicing for
                               a DBA track.
  --method pandas             Uses df.to_sql() instead. Slower, but useful
                               as a fallback when local_infile is disabled
                               on the server and you don't have permission
                               to change it.

Usage:
    python etl/load_to_mysql.py
    python etl/load_to_mysql.py --method pandas
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db_connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_ROOT / "data" / "processed" / "cleaned_sales_data.csv"


def load_via_infile(csv_path: str, engine) -> None:
    csv_path = str(Path(csv_path).resolve())

    with engine.connect() as conn:
        # Needed on the client side for LOCAL INFILE to be permitted.
        conn.execute(text("SET GLOBAL local_infile = 1"))
        conn.execute(text("TRUNCATE TABLE sales_data"))

        load_sql = f"""
            LOAD DATA LOCAL INFILE '{csv_path}'
            INTO TABLE sales_data
            FIELDS TERMINATED BY ','
            OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
            IGNORE 1 ROWS
            (order_id, product, region, sales_rep, quantity, price, order_date, total_sales)
        """
        conn.execute(text(load_sql))
        conn.commit()

        count = conn.execute(text("SELECT COUNT(*) FROM sales_data")).scalar()
        print(f"LOAD DATA INFILE complete. Rows in sales_data: {count}")


def load_via_pandas(csv_path: str, engine) -> None:
    df = pd.read_csv(csv_path)
    df.columns = [
        "order_id", "product", "region", "sales_rep",
        "quantity", "price", "order_date", "total_sales",
    ]
    df.to_sql("sales_data", engine, if_exists="replace", index=False)
    print(f"pandas to_sql complete. Rows loaded: {len(df)}")


def main():
    parser = argparse.ArgumentParser(description="Load cleaned sales CSV into MySQL.")
    parser.add_argument(
        "--csv", default=str(DEFAULT_CSV), help="Path to cleaned CSV"
    )
    parser.add_argument(
        "--method",
        choices=["load_data_infile", "pandas"],
        default="load_data_infile",
        help="How to load the data into MySQL",
    )
    args = parser.parse_args()

    engine = get_engine()

    if args.method == "load_data_infile":
        load_via_infile(args.csv, engine)
    else:
        load_via_pandas(args.csv, engine)


if __name__ == "__main__":
    main()
