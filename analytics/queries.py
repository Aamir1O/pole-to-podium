from sqlalchemy import text
from db.connection import get_engine

engine = get_engine()

def get_corner_boundaries(season: int, round_num: int) -> list[dict]:
    circuit_key = _get_circuit_key(season, round_num)
    if not circuit_key:
        return []
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT corner_number, corner_name,
                   dist_start_m, dist_apex_m, dist_end_m
            FROM   corners
            WHERE  circuit_key = :ck
            ORDER  BY corner_number
        """), {"ck": circuit_key})
        return [dict(r._mapping) for r in result.fetchall()]

def get_corner_metrics_comparison(
    session_id: int,
    driver_a: str,
    driver_b: str
) -> "pd.DataFrame":

    import pandas as pd

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
                    cm.apex_speed_kph,
                    cm.exit_speed_kph,
                    cm.brake_point_m,
                    cm.entry_speed_kph,
                    cm.throttle_point_m,
                    cm.time_to_full_throttle_s
                FROM corner_metrics cm
                JOIN telemetry_laps tl
                    ON tl.id = cm.lap_id
                JOIN corners c
                    ON c.id = cm.corner_id
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
def get_session_id(season: int, round_num: int, session_type: str) -> int | None:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id FROM sessions_f1
            WHERE  season       = :season
            AND    round        = :round
            AND    session_type = :stype
            LIMIT 1
        """), {"season": season, "round": round_num, "stype": session_type})
        row = result.fetchone()
    return row[0] if row else None

def _get_circuit_key(season: int, round_num: int) -> str | None:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT circuit_key FROM sessions_f1
            WHERE  season = :season AND round = :round
            LIMIT  1
        """), {"season": season, "round": round_num})
        row = result.fetchone()
    return row[0] if row else None