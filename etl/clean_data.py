"""
etl/clean_data.py
------------------
Step 1 of the pipeline: reads the raw, messy sales export and produces
a clean CSV that is safe to load into MySQL with LOAD DATA INFILE.

Why CSV and not straight into MySQL from here?
  Keeping "clean" and "load" as two separate scripts mirrors how a real
  ETL/DBA workflow is structured: a repeatable transform step that produces
  a flat file, and a separate load step that a DBA can run, schedule, or
  hand off. It also means the load step can be re-run without re-cleaning.

Usage:
    python etl/clean_data.py
    python etl/clean_data.py --input data/raw/messy_sales_data.xlsx --output data/processed/cleaned_sales_data.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

TEXT_COLUMNS = ["Product", "Region", "SalesRep"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "messy_sales_data.xlsx"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "cleaned_sales_data.csv"


def clean_data(input_path: str) -> pd.DataFrame:
    df = pd.read_excel(input_path, sheet_name="RawData")

    # 1. Drop rows that are entirely blank
    df = df.dropna(how="all")

    # 2. Drop exact duplicate rows (same order captured twice in the export)
    before = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before - len(df)

    # 3. Standardize text columns: trim whitespace, consistent Title Case
    #    ("west" / "WEST" / " West " all become "West")
    for col in TEXT_COLUMNS:
        df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        df[col] = df[col].str.title()
        df[col] = df[col].replace("Nan", np.nan)  # restore true NaNs lost to str cast

    # 4. Drop rows with no OrderID -> can't be uniquely identified / keyed in MySQL
    before = len(df)
    df = df.dropna(subset=["OrderID"])
    missing_order_id = before - len(df)
    df["OrderID"] = df["OrderID"].astype(int)

    # 5. Drop rows with no SalesRep -> sale can't be attributed to anyone
    before = len(df)
    df = df.dropna(subset=["SalesRep"])
    missing_sales_rep = before - len(df)

    # 6. Fix Quantity: negative/invalid values become NaN, then filled with
    #    the median quantity *for that product* (a fairer fill than a global median)
    df.loc[df["Quantity"] < 0, "Quantity"] = np.nan
    df["Quantity"] = df.groupby("Product")["Quantity"].transform(
        lambda x: x.fillna(x.median())
    )
    df["Quantity"] = df["Quantity"].fillna(df["Quantity"].median())
    df["Quantity"] = df["Quantity"].astype(int)

    # 7. Fix Price: fill missing with the average price for that product
    df["Price"] = df.groupby("Product")["Price"].transform(lambda x: x.fillna(x.mean()))
    df["Price"] = df["Price"].fillna(df["Price"].mean())
    df["Price"] = df["Price"].round(2)

    # 8. Standardize OrderDate: the export mixes DD/MM/YYYY, MM-DD-YYYY,
    #    YYYY-MM-DD and "Mon DD, YYYY" -> parse all to one real date type.
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce", format="mixed")
    before = len(df)
    df = df.dropna(subset=["OrderDate"])
    missing_dates = before - len(df)

    # 9. Computed column used throughout the dashboard
    df["TotalSales"] = (df["Quantity"] * df["Price"]).round(2)

    df = df.sort_values("OrderID").reset_index(drop=True)

    print("Cleaning summary")
    print("-----------------")
    print(f"  Duplicate rows removed      : {duplicates_removed}")
    print(f"  Rows dropped (no OrderID)   : {missing_order_id}")
    print(f"  Rows dropped (no SalesRep)  : {missing_sales_rep}")
    print(f"  Rows dropped (bad/missing date): {missing_dates}")
    print(f"  Final row count             : {len(df)}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Clean the raw sales export.")
    parser.add_argument(
        "--input", default=str(DEFAULT_INPUT), help="Path to the raw .xlsx file"
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the cleaned CSV",
    )
    args = parser.parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    cleaned = clean_data(args.input)
    cleaned.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    print(f"\nCleaned data written to: {args.output}")


if __name__ == "__main__":
    main()
