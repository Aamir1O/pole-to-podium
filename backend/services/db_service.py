import os
import time
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise ValueError("DB_URL environment variable is missing!")

engine = create_engine(
    DB_URL,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    connect_args={"connect_timeout": 10},
)

_cached_data = None
_last_cache_time = 0
CACHE_TTL_SECS = 300

def load_data_from_db():
    with engine.connect() as conn:
        results = pd.read_sql(text("SELECT * FROM results"), conn)
        qualifying = pd.read_sql(text("SELECT * FROM qualifying"), conn)
        laps = pd.read_sql(text("SELECT * FROM laps"), conn)
        weather = pd.read_sql(text("SELECT * FROM weather"), conn)
        try:
            practice = pd.read_sql(text("SELECT * FROM practice"), conn)
        except Exception:
            practice = pd.DataFrame()
            
    for df in [results, qualifying, laps, weather, practice]:
        if not df.empty:
            df.columns = [c.lower() for c in df.columns]
            
    return results, qualifying, laps, weather, practice

def get_cached_data(force_reload=False):
    global _cached_data, _last_cache_time
    now = time.time()
    if force_reload or _cached_data is None or (now - _last_cache_time > CACHE_TTL_SECS):
        _cached_data = load_data_from_db()
        _last_cache_time = now
    return _cached_data

def filter_season(results_all, qualifying_all, laps_all, weather_all, year: int, practice_all=None):
    r = results_all[results_all["year"] == year].copy()
    
    sprint_col = "sprint_pts" if "sprint_pts" in r.columns else "sprint_points"
    r["total_points"] = r["points"].fillna(0) + (
        r[sprint_col].fillna(0) if sprint_col in r.columns else 0
    )
    
    q = qualifying_all[qualifying_all["race_id"].astype(str).str.startswith(str(year))].copy()
    l = laps_all[laps_all["race_id"].astype(str).str.startswith(str(year))].copy()
    w = weather_all[weather_all["race_id"].astype(str).str.startswith(str(year))].copy()
    
    p = pd.DataFrame()
    if practice_all is not None and not practice_all.empty:
        p = practice_all[practice_all["race_id"].astype(str).str.startswith(str(year))].copy()
        
    return r, q, l, w, p

def get_driver_standings(r_df):
    if r_df.empty:
        return []
    
    pts_df = r_df.groupby("driver")["total_points"].sum().reset_index()
    wins_df = r_df[r_df["finish_pos"] == 1].groupby("driver").size().reset_index(name="wins")
    pod_df = r_df[r_df["finish_pos"] <= 3].groupby("driver").size().reset_index(name="podiums")
    team_df = (
        r_df.sort_values("race_id").groupby("driver").last()
        .reset_index()[["driver", "team"]]
    )
    
    standings = (
        pts_df.merge(wins_df, on="driver", how="left")
              .merge(pod_df,  on="driver", how="left")
              .merge(team_df, on="driver", how="left")
              .fillna(0)
              .sort_values("total_points", ascending=False)
              .reset_index(drop=True)
    )
    
    prev_race_ids = sorted(r_df["race_id"].unique())
    latest_points = {}
    if len(prev_race_ids) >= 1:
        latest_points = (
            r_df[r_df["race_id"] == prev_race_ids[-1]]
            .set_index("driver")["total_points"].to_dict()
        )
        
    res = []
    for idx, row in standings.iterrows():
        drv = row["driver"]
        res.append({
            "position": idx + 1,
            "driver_code": drv,
            "team": row["team"],
            "points": int(row["total_points"]),
            "wins": int(row["wins"]),
            "podiums": int(row["podiums"]),
            "delta": int(latest_points.get(drv, 0))
        })
    return res

def get_team_standings(r_df):
    if r_df.empty:
        return []
    
    tp = (
        r_df.groupby("team")["total_points"].sum()
        .reset_index()
        .sort_values("total_points", ascending=False)
        .reset_index(drop=True)
    )
    
    prev_race_ids = sorted(r_df["race_id"].unique())
    latest_points = {}
    if len(prev_race_ids) >= 1:
        latest_points = (
            r_df[r_df["race_id"] == prev_race_ids[-1]]
            .groupby("team")["total_points"].sum().to_dict()
        )
        
    res = []
    for idx, row in tp.iterrows():
        team = row["team"]
        abbr = "".join(w[0] for w in team.split()[:2]).upper()
        res.append({
            "position": idx + 1,
            "team": team,
            "team_abbr": abbr,
            "points": int(row["total_points"]),
            "delta": int(latest_points.get(team, 0))
        })
    return res

def get_race_schedule(r_df):
    if r_df.empty:
        return []
    
    races = (
        r_df[["race_id", "race_name", "circuit", "date"]]
        .drop_duplicates()
        .sort_values("race_id", ascending=False)
    )
    
    res = []
    for _, race in races.iterrows():
        race_id = race["race_id"]
        wr = r_df[(r_df["race_id"] == race_id) & (r_df["finish_pos"] == 1)]
        winner_code = wr.iloc[0]["driver"] if not wr.empty else None
        
        res.append({
            "race_id": race_id,
            "race_name": race["race_name"],
            "circuit": race["circuit"],
            "date": str(race["date"])[:10] if race["date"] else "",
            "status": "Finished" if winner_code else "Upcoming",
            "winner_code": winner_code
        })
    return res

# ── Telemetry & Corner DB Queries ─────────────────────────────────────────────

def get_session_info(season: int, round_num: int, session_type: str):
    """Fetches session ID and circuit key for a given round."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, circuit_key FROM sessions_f1
            WHERE season = :season AND round = :round AND session_type = :stype
            LIMIT 1
        """), {"season": season, "round": round_num, "stype": session_type})
        row = result.fetchone()
    return {"id": row[0], "circuit_key": row[1]} if row else None

def get_corners_by_circuit(circuit_key: str) -> list[dict]:
    """Retrieves all corner boundaries for a circuit key."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT corner_number, dist_start_m, dist_apex_m, dist_end_m
            FROM corners
            WHERE circuit_key = :ck
            ORDER BY corner_number
        """), {"ck": circuit_key})
        rows = result.fetchall()
    return [
        {
            "corner_number": r[0],
            "dist_start_m": r[1],
            "dist_apex_m": r[2],
            "dist_end_m": r[3]
        }
        for r in rows
    ]

def get_driver_telemetry(session_id: int, driver_code: str) -> dict | None:
    """Retrieves aligned telemetry trace from DB."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tl.lap_time_s,
                   tc.distance_m, tc.speed_kph, tc.throttle_pct, tc.brake, tc.gear, tc.rpm
            FROM telemetry_laps tl
            JOIN telemetry_channels tc ON tc.lap_id = tl.id
            WHERE tl.session_id = :sid AND tl.driver_code = :drv
            LIMIT 1
        """), {"sid": session_id, "drv": driver_code})
        row = result.fetchone()
        
    if not row:
        return None
        
    return {
        "lap_time_s": float(row[0]) if row[0] else None,
        "distance_m": list(row[1]),
        "speed_kph": list(row[2]),
        "throttle_pct": list(row[3]),
        "brake": [bool(x) for x in row[4]],
        "gear": [int(x) for x in row[5]],
        "rpm": [int(x) for x in row[6]]
    }

def get_delta_trace(session_id: int, driver_a: str, driver_b: str) -> dict | None:
    """Retrieves the pre-computed delta trace. Accounts for swapped drivers."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT driver_a, distance_m, delta_s
            FROM delta_traces
            WHERE session_id = :sid
              AND (
                (driver_a = :da AND driver_b = :db)
                OR (driver_a = :db AND driver_b = :da)
              )
            LIMIT 1
        """), {"sid": session_id, "da": driver_a, "db": driver_b})
        row = result.fetchone()
        
    if not row:
        return None
        
    db_da = row[0]
    distance = list(row[1])
    delta = list(row[2])
    
    # If driver inputs were swapped, negate delta values
    if db_da != driver_a:
        delta = [-x for x in delta]
        
    return {
        "distance_m": distance,
        "delta_s": delta
    }

def get_corner_metrics(session_id: int, driver_a: str, driver_b: str) -> pd.DataFrame:
    """Returns corner CPI comparison dataframe between two drivers."""
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT
                    tl.driver_code,
                    c.corner_number,
                    c.corner_name,
                    cm.entry_score,
                    cm.apex_score,
                    cm.exit_score,
                    cm.cpi,
                    cm.corner_time_s,
                    cm.entry_speed_kph,
                    cm.apex_speed_kph,
                    cm.exit_speed_kph,
                    cm.brake_point_m,
                    cm.throttle_point_m,
                    cm.time_to_full_throttle_s
                FROM corner_metrics cm
                JOIN telemetry_laps tl ON tl.id = cm.lap_id
                JOIN corners c ON c.id = cm.corner_id
                WHERE tl.session_id = :sid
                  AND tl.driver_code IN (:da, :db)
                ORDER BY c.corner_number, tl.driver_code
            """),
            conn,
            params={
                "sid": session_id,
                "da": driver_a,
                "db": driver_b
            }
        )
    return df
