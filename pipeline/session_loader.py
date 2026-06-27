import argparse
import sys
import os

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
import fastf1

# ── path fix so pipeline can import from project root ─────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_engine
from sqlalchemy import text

fastf1.Cache.enable_cache(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cache")
)

# ──────────────────────────────────────────────────────────────────────
# 1. LOAD SESSION
# ──────────────────────────────────────────────────────────────────────
def load_session(season: int, round_num: int, session_type: str):
    print(f"📡 Loading FastF1: {season} Round {round_num} — {session_type}")
    session = fastf1.get_session(season, round_num, session_type)
    session.load(telemetry=True, laps=True, weather=False, messages=False)
    print(f"✅ Session loaded: {session.event['EventName']}")
    return session


# ──────────────────────────────────────────────────────────────────────
# 2. UPSERT SESSION METADATA → sessions_f1 table
# ──────────────────────────────────────────────────────────────────────
def upsert_session(engine, season, round_num, session_type, circuit_key, session_date):
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO sessions_f1 (season, round, circuit_key, session_type, session_date)
            VALUES (:season, :round, :circuit_key, :session_type, :session_date)
            ON CONFLICT (season, round, session_type)
            DO UPDATE SET circuit_key = EXCLUDED.circuit_key
            RETURNING id
        """), {
            "season": season,
            "round": round_num,
            "circuit_key": circuit_key,
            "session_type": session_type,
            "session_date": str(session_date),
        })
        session_id = result.fetchone()[0]
    print(f"✅ Session ID: {session_id}")
    return session_id


# ──────────────────────────────────────────────────────────────────────
# 3. ALIGN TELEMETRY (resample to 300-point distance grid)
# ──────────────────────────────────────────────────────────────────────
def align_telemetry(session, driver_a: str, driver_b: str):
    from pipeline.telemetry_aligner import load_and_align
    print(f"🔧 Aligning telemetry: {driver_a} vs {driver_b}")
    data = load_and_align(session, driver_a, driver_b)
    print(f"✅ Telemetry aligned — grid size: {len(data['grid'])}")
    return data


# ──────────────────────────────────────────────────────────────────────
# 4. UPSERT LAP + TELEMETRY → telemetry_laps + telemetry_channels
# ──────────────────────────────────────────────────────────────────────
def upsert_telemetry(engine, session_id, driver_code, lap_time_s, tel_data):
    with engine.begin() as conn:
        # upsert lap row
        result = conn.execute(text("""
            INSERT INTO telemetry_laps
                (session_id, driver_code, lap_number, lap_time_s, is_fastest)
            VALUES (:session_id, :driver_code, 1, :lap_time_s, TRUE)
            ON CONFLICT (session_id, driver_code, lap_number)
            DO UPDATE SET lap_time_s = EXCLUDED.lap_time_s
            RETURNING id
        """), {
            "session_id": session_id,
            "driver_code": driver_code,
            "lap_time_s": lap_time_s,
        })
        lap_id = result.fetchone()[0]

        # upsert telemetry arrays
        conn.execute(text("""
            INSERT INTO telemetry_channels
                (lap_id, distance_m, speed_kph, throttle_pct,
                 brake, rpm, gear, x_pos, y_pos, sample_count)
            VALUES
                (:lap_id, :distance_m, :speed_kph, :throttle_pct,
                 :brake, :rpm, :gear, :x_pos, :y_pos, :sample_count)
            ON CONFLICT (lap_id)
            DO UPDATE SET
                speed_kph    = EXCLUDED.speed_kph,
                throttle_pct = EXCLUDED.throttle_pct,
                brake        = EXCLUDED.brake
        """), {
            "lap_id":       lap_id,
            "distance_m":   tel_data["distance_m"].tolist(),
            "speed_kph":    tel_data["Speed"].tolist(),
            "throttle_pct": tel_data["Throttle"].tolist(),
            "brake": [bool(x > 0.5) for x in tel_data["Brake"]],
            "rpm": np.round(tel_data["RPM"]).astype(int).tolist(),
            "gear": np.round(tel_data["nGear"]).astype(int).tolist(),
            "x_pos":        tel_data["X"].tolist(),
            "y_pos":        tel_data["Y"].tolist(),
            "sample_count": int(len(tel_data["distance_m"])),
        })

    print(f"✅ Telemetry saved — {driver_code}, lap_id={lap_id}")
    return lap_id


# ──────────────────────────────────────────────────────────────────────
# 5. DETECT CORNERS + SAVE → corners table
# ──────────────────────────────────────────────────────────────────────
def detect_and_save_corners(engine, circuit_key, grid, speed_ref):
    from pipeline.corner_detector import detect_corners, upsert_corners
    print("🔍 Detecting corners...")
    corners = detect_corners(circuit_key, grid, speed_ref)
    upsert_corners(engine, circuit_key, corners)
    print(f"✅ {len(corners)} corners detected and saved")
    return corners


# ──────────────────────────────────────────────────────────────────────
# 6. COMPUTE CPI + SAVE → corner_metrics table
# ──────────────────────────────────────────────────────────────────────
def compute_and_save_cpi(engine, lap_id_a, lap_id_b,
                          tel_a, tel_b, corners, circuit_key, engine_db):
    from pipeline.cpi_calculator import extract_corner_metrics, compute_cpi
    import pandas as pd

    grid = tel_a["distance_m"]

    metrics_a = [extract_corner_metrics(
        grid, np.array(tel_a["Speed"]), np.array(tel_a["Throttle"]),
        np.array(tel_a["Brake"]), c) for c in corners]
    metrics_b = [extract_corner_metrics(
        grid, np.array(tel_b["Speed"]), np.array(tel_b["Throttle"]),
        np.array(tel_b["Brake"]), c) for c in corners]

    metrics_a = [m for m in metrics_a if m]
    metrics_b = [m for m in metrics_b if m]

    df = compute_cpi(metrics_a, metrics_b)

    # fetch corner IDs from DB
    with engine_db.connect() as conn:
        result = conn.execute(text(
            "SELECT id, corner_number FROM corners WHERE circuit_key = :ck"
        ), {"ck": circuit_key})
        corner_map = {row[1]: row[0] for row in result}

    rows = []
    for _, row in df.iterrows():
        lap_id = lap_id_a if row["driver"] == "A" else lap_id_b
        corner_id = corner_map.get(int(row["corner"]))
        if not corner_id:
            continue
        rows.append({
            "lap_id": lap_id,
            "corner_id": corner_id,
            "entry_speed_kph": float(row["entry"]) if pd.notna(row["entry"]) else None,
            "brake_point_m": float(row["brake_point_m"]) if pd.notna(row["brake_point_m"]) else None,
            "brake_duration_m": float(row["brake_duration_m"]) if pd.notna(row["brake_duration_m"]) else None,
            "apex_speed_kph": float(row["apex"]) if pd.notna(row["apex"]) else None,
            "exit_speed_kph": float(row["exit"]) if pd.notna(row["exit"]) else None,
            "throttle_point_m": float(row["throttle_point_m"]) if pd.notna(row["throttle_point_m"]) else None,
            "time_to_full_throttle_s": float(row["time_to_full_throttle_s"]) if pd.notna(row["time_to_full_throttle_s"]) else None,
            "entry_score": float(row["entry_score"]) if pd.notna(row["entry_score"]) else None,
            "apex_score": float(row["apex_score"]) if pd.notna(row["apex_score"]) else None,
            "exit_score": float(row["exit_score"]) if pd.notna(row["exit_score"]) else None,
            "cpi": float(row["cpi"]) if pd.notna(row["cpi"]) else None,
            "corner_time_s": float(row["corner_time_s"]) if pd.notna(row["corner_time_s"]) else None,
        })

    with engine_db.begin() as conn:
        for r in rows:
            conn.execute(text("""
                INSERT INTO corner_metrics
                    (lap_id, corner_id, entry_speed_kph, brake_point_m, brake_duration_m,
                     apex_speed_kph, exit_speed_kph, throttle_point_m, time_to_full_throttle_s,
                     entry_score, apex_score, exit_score, cpi, corner_time_s)
                VALUES
                    (:lap_id, :corner_id, :entry_speed_kph, :brake_point_m, :brake_duration_m,
                     :apex_speed_kph, :exit_speed_kph, :throttle_point_m, :time_to_full_throttle_s,
                     :entry_score, :apex_score, :exit_score, :cpi, :corner_time_s)
                ON CONFLICT (lap_id, corner_id)
                DO UPDATE SET 
                    entry_speed_kph = EXCLUDED.entry_speed_kph,
                    brake_point_m = EXCLUDED.brake_point_m,
                    brake_duration_m = EXCLUDED.brake_duration_m,
                    apex_speed_kph = EXCLUDED.apex_speed_kph,
                    exit_speed_kph = EXCLUDED.exit_speed_kph,
                    throttle_point_m = EXCLUDED.throttle_point_m,
                    time_to_full_throttle_s = EXCLUDED.time_to_full_throttle_s,
                    entry_score = EXCLUDED.entry_score,
                    apex_score = EXCLUDED.apex_score,
                    exit_score = EXCLUDED.exit_score,
                    cpi = EXCLUDED.cpi,
                    corner_time_s = EXCLUDED.corner_time_s
            """), r)
    print(f"✅ CPI saved for {len(rows)} corner × driver combinations")


# ──────────────────────────────────────────────────────────────────────
# 7. COMPUTE DELTA + SAVE → delta_traces table
# ──────────────────────────────────────────────────────────────────────
def compute_and_save_delta(engine, session_id, driver_a, driver_b, grid, tel_a, tel_b):
    from pipeline.delta_calculator import compute_cumulative_delta
    print("📈 Computing lap delta...")
    delta = compute_cumulative_delta(
        grid,
        np.array(tel_a["Speed"]),
        np.array(tel_b["Speed"]),
    )
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO delta_traces
                (session_id, driver_a, driver_b, distance_m, delta_s)
            VALUES
                (:session_id, :driver_a, :driver_b, :distance_m, :delta_s)
            ON CONFLICT (session_id, driver_a, driver_b)
            DO UPDATE SET delta_s = EXCLUDED.delta_s
        """), {
            "session_id": session_id,
            "driver_a":   driver_a,
            "driver_b":   driver_b,
            "distance_m": grid.tolist(),
            "delta_s":    delta.tolist(),
        })
    print(f"✅ Delta trace saved — {driver_a} vs {driver_b}")


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Load F1 telemetry session into Supabase")
    parser.add_argument("--season",   type=int,  required=True)
    parser.add_argument("--round",    type=int,  required=True)
    parser.add_argument("--session",  type=str,  required=True, help="Q / FP1 / FP2 / FP3 / R")
    parser.add_argument("--driver_a", type=str,  default="VER")
    parser.add_argument("--driver_b", type=str,  default="NOR")
    args = parser.parse_args()

    driver_a = args.driver_a.upper()
    driver_b = args.driver_b.upper()

    engine = get_engine()

    # 1. load FastF1 session
    session = load_session(args.season, args.round, args.session)
    circuit_key  = session.event["Location"].lower().replace(" ", "_")
    session_date = session.date.date() if hasattr(session.date, "date") else session.date

    # 2. save session metadata
    session_id = upsert_session(
        engine, args.season, args.round, args.session,
        circuit_key, session_date
    )

    # 3. align telemetry
    data     = align_telemetry(session, driver_a, driver_b)
    grid     = data["grid"]
    tel_a    = data["driver_a"]
    tel_b    = data["driver_b"]

    # 4. save telemetry for both drivers
    lap_id_a = upsert_telemetry(engine, session_id, driver_a, data["lap_time_a"], tel_a)
    lap_id_b = upsert_telemetry(engine, session_id, driver_b, data["lap_time_b"], tel_b)

    # 5. detect corners (use driver A speed as reference)
    corners = detect_and_save_corners(engine, circuit_key, grid, np.array(tel_a["Speed"]))

    # 6. compute and save CPI
    compute_and_save_cpi(engine, lap_id_a, lap_id_b,
                          tel_a, tel_b, corners, circuit_key, engine)

    # 7. compute and save delta
    compute_and_save_delta(engine, session_id, driver_a, driver_b, grid, tel_a, tel_b)

    print(f"\n🏁 Done! Session {args.season} R{args.round} {args.session} "
          f"— {driver_a} vs {driver_b} fully loaded.")


if __name__ == "__main__":
    main()