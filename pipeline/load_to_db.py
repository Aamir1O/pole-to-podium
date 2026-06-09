import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise ValueError("❌ DB_URL not found in .env file!")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

print("🔌 Connecting to Supabase...")
engine = create_engine(DB_URL, pool_size=2, max_overflow=0, connect_args={"connect_timeout": 10})
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("✅ Connected!\n")

# ── tables and their CSV files (add more years here as needed) ─────────────
tables = {
    "results"   : ["results_2025.csv",    "results_2026.csv"],
    "laps"      : ["laps_2025.csv",       "laps_2026.csv"],
    "weather"   : ["weather_2025.csv",    "weather_2026.csv"],
    "qualifying": ["qualifying_2025.csv", "qualifying_2026.csv"],
}

for table, csv_files in tables.items():
    combined = []
    for csv_file in csv_files:
        filepath = os.path.join(DATA_DIR, csv_file)
        if not os.path.exists(filepath):
            print(f"  ⚠️  {csv_file} not found — skipping")
            continue
        df = pd.read_csv(filepath)
        combined.append(df)
        print(f"  📂 Loaded {csv_file} — {len(df)} rows")

    if not combined:
        continue

    final_df = pd.concat(combined, ignore_index=True)
    if table == "qualifying":
        final_df = final_df.drop_duplicates(
            subset=["race_id", "driver"]
        )
    final_df.to_sql(table, con=engine, if_exists="replace", index=False, chunksize=500)
    print(f"  ✅ {len(final_df)} total rows → '{table}'\n")

print("🎉 All data loaded into Supabase!")