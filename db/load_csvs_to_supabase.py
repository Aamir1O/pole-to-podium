import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Setup path so it can import or execute cleanly
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

def main():
    # 1. Read DB_URL from .env
    dotenv_path = os.path.join(base_dir, ".env")
    load_dotenv(dotenv_path)
    
    db_url = os.getenv("DB_URL")
    if not db_url:
        print("Error: DB_URL not set in .env", file=sys.stderr)
        sys.exit(1)
        
    # 2. Connect using SQLAlchemy
    print("[DB] Connecting to database...")
    engine = create_engine(
        db_url,
        pool_size=2,
        max_overflow=0,
        connect_args={"connect_timeout": 15},
    )
    
    # 3. Define CSV paths relative to base_dir
    csv_mapping = {
        "results": [
            os.path.join(base_dir, "data", "results_2025.csv"),
            os.path.join(base_dir, "data", "results_2026.csv"),
        ],
        "qualifying": [
            os.path.join(base_dir, "data", "qualifying_2025.csv"),
            os.path.join(base_dir, "data", "qualifying_2026.csv"),
        ],
        "laps": [
            os.path.join(base_dir, "data", "laps_2025.csv"),
            os.path.join(base_dir, "data", "laps_2026.csv"),
        ],
        "weather": [
            os.path.join(base_dir, "data", "weather_2025.csv"),
            os.path.join(base_dir, "data", "weather_2026.csv"),
        ],
        "practice": [
            os.path.join(base_dir, "data", "practice_2026.csv"),
        ]
    }
    
    # 4 & 5. Concatenate and load to Supabase
    for table_name, paths in csv_mapping.items():
        dfs = []
        for path in paths:
            if os.path.exists(path):
                print(f"Reading {os.path.basename(path)}...")
                df = pd.read_csv(path)
                dfs.append(df)
            else:
                print(f"Warning: File not found {path}", file=sys.stderr)
                
        if not dfs:
            print(f"No files loaded for table: {table_name}", file=sys.stderr)
            continue
            
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # 6 & 7. Create tables automatically using pandas to_sql with if_exists="replace"
        print(f"Uploading {len(combined_df)} rows to table '{table_name}'...")
        combined_df.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False
        )
        
        # 8. Print row counts after upload
        print(f"Uploaded table '{table_name}' successfully. Total rows: {len(combined_df)}")
        print("-" * 50)

if __name__ == "__main__":
    main()
