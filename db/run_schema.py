
from sqlalchemy import text
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import get_engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE_DIR, "db", "schema.sql")

engine = get_engine()

print("🔌 Applying schema to Supabase...")
with open(SCHEMA_PATH, "r") as f:
    sql = f.read()

with engine.begin() as conn:
    # Split on ; and execute each statement individually
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            conn.execute(text(stmt))

print("✅ Schema applied — all corner analysis tables created.")