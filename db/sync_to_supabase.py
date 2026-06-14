import os
import sys
import glob
import logging
import argparse
import pandas as pd
from sqlalchemy import create_engine, text, inspect
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
logger = logging.getLogger("sync_to_supabase")

# Configuration
UNIQUENESS_KEYS = {
    "results": ["race_id", "driver"],
    "qualifying": ["race_id", "driver"],
    "laps": ["race_id", "driver", "lap_number"],
    "weather": ["race_id"],
    "practice": ["race_id", "session", "driver"]
}

def sync_table(engine, table_name, df, unique_keys, full_refresh=False):
    """
    Syncs a pandas DataFrame to a Supabase table.
    Uses replacement for --full-refresh, otherwise performs a staging-table-based UPSERT.
    """
    if df.empty:
        logger.info(f"[{table_name}] No rows to sync.")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    # Ensure all column names are lowercase to match the database schema
    df.columns = [c.lower() for c in df.columns]

    # Validate that all unique keys exist in the DataFrame columns
    for key in unique_keys:
        if key not in df.columns:
            raise ValueError(f"[{table_name}] Unique key '{key}' is missing from the DataFrame columns: {list(df.columns)}")

    # Check if table exists
    with engine.connect() as conn:
        try:
            insp = inspect(conn)
            table_exists = insp.has_table(table_name)
        except Exception as e:
            logger.warning(f"[{table_name}] Inspector failed to check table existence: {e}. Assuming table does not exist.")
            table_exists = False

    # Standard replacement flow if table does not exist or full_refresh is requested
    if not table_exists or full_refresh:
        logger.info(f"[{table_name}] Creating/Replacing table '{table_name}' in the database...")
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)
        inserted = len(df)
        logger.info(f"[{table_name}] Successfully created/replaced. Rows inserted: {inserted}, updated: 0, skipped: 0")
        return {"inserted": inserted, "updated": 0, "skipped": 0}

    # Otherwise, perform transactional staging-table-based UPSERT
    staging_table = f"{table_name}_staging"
    logger.info(f"[{table_name}] Uploading {len(df)} rows to staging table '{staging_table}'...")
    df.to_sql(staging_table, con=engine, if_exists="replace", index=False)

    with engine.connect() as conn:
        insp = inspect(conn)
        target_cols = [c["name"].lower() for c in insp.get_columns(table_name)]
        staging_cols = [c["name"].lower() for c in insp.get_columns(staging_table)]

    # Get intersection of columns to prevent query errors if schemas slightly mismatch
    common_cols = [c for c in staging_cols if c in target_cols]
    non_key_cols = [c for c in common_cols if c not in unique_keys]

    join_cond = " AND ".join([f"s.{k} = t.{k}" for k in unique_keys])
    null_cond = " AND ".join([f"t.{k} IS NULL" for k in unique_keys])

    if non_key_cols:
        diff_cond = " OR ".join([f"s.{c} IS DISTINCT FROM t.{c}" for c in non_key_cols])
        set_clause = ", ".join([f"{c} = s.{c}" for c in non_key_cols])
    else:
        diff_cond = "FALSE"
        set_clause = ""

    # Construct status check queries
    ins_query = text(f"""
        SELECT COUNT(*) FROM {staging_table} s
        LEFT JOIN {table_name} t ON {join_cond}
        WHERE {null_cond}
    """)

    upd_query = text(f"""
        SELECT COUNT(*) FROM {staging_table} s
        JOIN {table_name} t ON {join_cond}
        WHERE {diff_cond}
    """)

    skp_query = text(f"""
        SELECT COUNT(*) FROM {staging_table} s
        JOIN {table_name} t ON {join_cond}
        WHERE NOT ({diff_cond})
    """)

    # Execute inside transaction block
    with engine.begin() as conn:
        inserted = conn.execute(ins_query).scalar()
        updated = conn.execute(upd_query).scalar()
        skipped = conn.execute(skp_query).scalar()

        # Update existing changed rows
        if updated > 0 and set_clause:
            conn.execute(text(f"""
                UPDATE {table_name} t
                SET {set_clause}
                FROM {staging_table} s
                WHERE {join_cond} AND ({diff_cond})
            """))

        # Insert new rows
        if inserted > 0:
            cols_str = ", ".join(common_cols)
            conn.execute(text(f"""
                INSERT INTO {table_name} ({cols_str})
                SELECT {cols_str} FROM {staging_table} s
                WHERE NOT EXISTS (
                    SELECT 1 FROM {table_name} t WHERE {join_cond}
                )
            """))

        # Cleanup staging table
        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))

    logger.info(f"[{table_name}] Sync complete. Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}")
    return {"inserted": inserted, "updated": updated, "skipped": skipped}

def run_sync(full_refresh=False):
    """
    Main entry point for loading, merging, and syncing CSV files.
    """
    # 1. Read DB_URL from .env
    load_dotenv(os.path.join(base_dir, ".env"))
    db_url = os.getenv("DB_URL")
    if not db_url:
        logger.error("DB_URL is missing from environment or .env file.")
        raise ValueError("DB_URL environment variable is missing!")

    logger.info("Connecting to Supabase...")
    engine = create_engine(
        db_url,
        pool_size=2,
        max_overflow=0,
        connect_args={"connect_timeout": 15}
    )

    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory '{data_dir}' does not exist. No files to sync.")
        return {}

    summary = {}

    # 2. Discover and merge files for each table type
    for table_name, unique_keys in UNIQUENESS_KEYS.items():
        pattern = os.path.join(data_dir, f"{table_name}_*.csv")
        csv_files = glob.glob(pattern)

        # Filter files that end with _YYYY.csv (a 4-digit year)
        valid_files = []
        for f in csv_files:
            name_without_ext = os.path.splitext(os.path.basename(f))[0]
            parts = name_without_ext.split("_")
            if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
                valid_files.append(f)

        if not valid_files:
            logger.warning(f"No CSV files found matching pattern '{pattern}'. Skipping '{table_name}'.")
            continue

        logger.info(f"[{table_name}] Found files: {[os.path.basename(f) for f in valid_files]}")

        dfs = []
        for file_path in valid_files:
            try:
                df = pd.read_csv(file_path)
                dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to read CSV '{file_path}': {e}")
                raise

        # Build unified DataFrame
        unified_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"[{table_name}] Unified DataFrame loaded {len(unified_df)} total rows.")

        # Drop duplicates on unique keys to keep it clean and prevent staging conflicts
        before_len = len(unified_df)
        unified_df.columns = [c.lower() for c in unified_df.columns]
        unified_df = unified_df.drop_duplicates(subset=[k.lower() for k in unique_keys], keep="last")
        after_len = len(unified_df)
        if before_len != after_len:
            logger.info(f"[{table_name}] Removed {before_len - after_len} duplicate rows based on unique keys: {unique_keys}")

        # Sync table to DB
        try:
            counts = sync_table(
                engine=engine,
                table_name=table_name,
                df=unified_df,
                unique_keys=unique_keys,
                full_refresh=full_refresh
            )
            summary[table_name] = counts
        except Exception as e:
            logger.error(f"Failed syncing table '{table_name}': {e}")
            raise

    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync local F1 CSV backups to Supabase")
    parser.add_argument("--full-refresh", action="store_true", help="Overwrites target tables entirely")
    args = parser.parse_args()

    try:
        run_sync(full_refresh=args.full_refresh)
        logger.info("Database sync complete.")
    except Exception as ex:
        logger.error(f"Sync process failed: {ex}")
        sys.exit(1)
