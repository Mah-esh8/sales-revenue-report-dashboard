"""Shared SQLAlchemy engine factory for ETL and dashboard access."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_engine(*, local_infile: bool = False) -> Engine:
    """Create a MySQL engine; opt in to LOCAL INFILE only for bulk loading."""
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "sales_dashboard"),
    )
    connect_args = {"local_infile": 1} if local_infile else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)
