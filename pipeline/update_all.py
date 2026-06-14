import os
import sys
import argparse
import logging
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Set up paths so this script can run from anywhere
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("update_all")

# Import pipeline/fetch_data
from pipeline.fetch_data import fetch_season
# Import db/sync_to_supabase
from db.sync_to_supabase import run_sync, UNIQUENESS_KEYS

def validate_row_counts(engine):
    """
    Validates database row counts against the combined counts from local CSV files.
    """
    logger.info("Validating local CSV row counts vs database tables...")
    data_dir = os.path.join(base_dir, "data")
    import glob
    
    validation_results = {}
    
    with engine.connect() as conn:
        for table_name in UNIQUENESS_KEYS.keys():
            # Get db count
            try:
                db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            except Exception as e:
                logger.warning(f"Could not get row count for database table '{table_name}': {e}")
                db_count = -1
                
            # Get local count
            pattern = os.path.join(data_dir, f"{table_name}_*.csv")
            csv_files = glob.glob(pattern)
            valid_files = []
            for f in csv_files:
                name_without_ext = os.path.splitext(os.path.basename(f))[0]
                parts = name_without_ext.split("_")
                if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
                    valid_files.append(f)
                    
            local_count = 0
            if valid_files:
                dfs = []
                for file_path in valid_files:
                    try:
                        df = pd.read_csv(file_path)
                        dfs.append(df)
                    except Exception:
                        pass
                if dfs:
                    combined_df = pd.concat(dfs, ignore_index=True)
                    combined_df.columns = [c.lower() for c in combined_df.columns]
                    keys = [k.lower() for k in UNIQUENESS_KEYS[table_name]]
                    combined_df = combined_df.drop_duplicates(subset=keys)
                    local_count = len(combined_df)
                else:
                    local_count = 0
            else:
                local_count = -1
                
            validation_results[table_name] = {
                "database": db_count,
                "local_csv": local_count,
                "valid": db_count == local_count if (db_count != -1 and local_count != -1) else False
            }
            
    return validation_results

def trigger_cache_refresh():
    """
    Sends a POST request to the FastAPI server to refresh in-memory caches.
    """
    # Try localhost first
    api_url = "http://127.0.0.1:8000/api/v1/refresh"
    logger.info(f"Triggering FastAPI cache refresh at: {api_url}")
    try:
        response = requests.post(api_url, timeout=5)
        if response.status_code == 200:
            logger.info("FastAPI cache refreshed successfully.")
            return True, "Successfully refreshed cache via localhost API."
        else:
            logger.warning(f"FastAPI cache refresh returned status code: {response.status_code}")
            return False, f"Failed with status code {response.status_code}."
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not reach FastAPI server for cache refresh: {e}")
        return False, "API server not reachable (normal if running offline)."

def main():
    parser = argparse.ArgumentParser(description="Ingest latest F1 data, update backups, and sync Supabase")
    parser.add_argument("--full-refresh", action="store_true", help="Rebuild database tables entirely from CSV backups")
    args = parser.parse_args()

    # 1. Fetch latest FastF1 data
    logger.info("==========================================")
    logger.info("Step 1: Fetching latest FastF1 data...")
    logger.info("==========================================")
    try:
        logger.info("Fetching 2026 season schedule/data...")
        fetch_season(2026)
        logger.info("FastF1 data ingestion completed.")
    except Exception as e:
        logger.error(f"Error fetching FastF1 data: {e}")
        # Proceed with syncing what we have even if fetch fails
        
    # 2. Sync to Supabase
    logger.info("\n==========================================")
    logger.info("Step 2: Syncing CSV data to Supabase...")
    logger.info("==========================================")
    sync_summary = {}
    try:
        sync_summary = run_sync(full_refresh=args.full_refresh)
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)
        
    # 3. Validate row counts
    logger.info("\n==========================================")
    logger.info("Step 3: Validating data counts...")
    logger.info("==========================================")
    
    load_dotenv(os.path.join(base_dir, ".env"))
    db_url = os.getenv("DB_URL")
    engine = create_engine(
        db_url,
        pool_size=2,
        max_overflow=0,
        connect_args={"connect_timeout": 15}
    )
    
    val_results = {}
    try:
        val_results = validate_row_counts(engine)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        
    # 4. Refresh caches
    logger.info("\n==========================================")
    logger.info("Step 4: Refreshing API cache...")
    logger.info("==========================================")
    cache_refreshed, cache_msg = trigger_cache_refresh()
    
    # 5. Print a summary report
    print("\n" + "=" * 60)
    print("           POLE TO PODIUM PIPELINE SUMMARY REPORT")
    print("=" * 60)
    
    print(f"\nMode: {'Full Refresh (overwrite)' if args.full_refresh else 'Staging-table UPSERT'}")
    print(f"Database URL: {db_url.split('@')[-1] if db_url else 'Not Set'}")
    
    print("\n--- Synchronization Summary ---")
    if sync_summary:
        print(f"{'Table':12s} | {'Inserted':8s} | {'Updated':8s} | {'Skipped':8s}")
        print("-" * 45)
        for tbl, counts in sync_summary.items():
            print(f"{tbl:12s} | {counts['inserted']:8d} | {counts['updated']:8d} | {counts['skipped']:8d}")
    else:
        print("No tables synced.")
        
    print("\n--- Validation Report (Local CSV vs Supabase DB) ---")
    if val_results:
        print(f"{'Table':12s} | {'Local CSV':9s} | {'Database':8s} | {'Status':8s}")
        print("-" * 45)
        for tbl, data in val_results.items():
            status_str = "PASS" if data["valid"] else "MISMATCH / ERR"
            print(f"{tbl:12s} | {data['local_csv']:9d} | {data['database']:8d} | {status_str:8s}")
    else:
        print("No validation data.")
        
    print("\n--- API Cache Refresh Status ---")
    print(f"Status: {'Success' if cache_refreshed else 'Skipped/Failed'}")
    print(f"Details: {cache_msg}")
    print("=" * 60)

if __name__ == "__main__":
    main()
