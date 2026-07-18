"""
etl/db_connection.py
---------------------
Single shared place to build a SQLAlchemy engine for MySQL, so both the
loader script and the Streamlit dashboard connect the same way.

Reads credentials from environment variables (loaded from a .env file
via python-dotenv), so no password ever needs to be hard-coded or
committed to GitHub.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()  # reads .env in the project root if present


def get_engine() -> Engine:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "sales_dashboard")

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    # pool_pre_ping avoids "MySQL server has gone away" on idle connections,
    # which matters for a dashboard that stays open in a browser tab.
    # local_infile=1 is required client-side (in addition to the server-side
    # `SET GLOBAL local_infile = 1`) for LOAD DATA LOCAL INFILE to work.
    return create_engine(url, pool_pre_ping=True, connect_args={"local_infile": 1})
