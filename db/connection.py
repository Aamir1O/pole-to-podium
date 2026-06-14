import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL not set in .env")

# Same settings as your existing load_to_db.py
_engine = create_engine(
    DB_URL,
    pool_size=2,
    max_overflow=0,
    connect_args={"connect_timeout": 10},
)

def get_engine():
    return _engine

def get_conn():
    """Context manager — use with `with get_conn() as conn:`"""
    return _engine.connect()

def test_connection():
    with _engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[DB] Connection OK")