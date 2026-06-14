import numpy as np
from scipy.signal import argrelextrema
from sqlalchemy import text


# ──────────────────────────────────────────────────────────────────────
# CORNER DETECTION
# ──────────────────────────────────────────────────────────────────────
def detect_corners(circuit_key: str, distance: np.ndarray,
                   speed: np.ndarray, order: int = 12) -> list[dict]:
    """
    Detect corners from a speed trace using local minima.

    Parameters
    ----------
    circuit_key : str
        e.g. 'monza', 'spa-francorchamps'
    distance : np.ndarray
        300-point normalised distance grid (metres)
    speed : np.ndarray
        Corresponding speed values (km/h)
    order : int
        scipy argrelextrema neighbourhood — higher = fewer corners detected

    Returns
    -------
    list of dicts with keys:
        corner_number, dist_start_m, dist_apex_m, dist_end_m
    """

    # ── find local speed minima ───────────────────────────────────────
    minima_idx = argrelextrema(speed, np.less, order=order)[0]

    # ── filter out noise: minimum must be at least 5% below local mean ─
    filtered = []
    for idx in minima_idx:
        window_start = max(0, idx - order * 2)
        window_end   = min(len(speed), idx + order * 2)
        local_mean   = np.mean(speed[window_start:window_end])
        if speed[idx] < local_mean * 0.95:
            filtered.append(idx)

    # ── also filter: minimum speed must be below 280 km/h ─────────────
    # (removes false positives on long straights with slight speed variation)
    filtered = [idx for idx in filtered if speed[idx] < 280]

    corners = []
    for i, idx in enumerate(filtered):

        apex_dist  = float(distance[idx])
        apex_speed = float(speed[idx])

        # ── entry: walk back to the preceding speed peak ──────────────
        search_back  = max(0, idx - order * 4)
        entry_idx    = search_back + int(np.argmax(speed[search_back:idx]))
        # clamp: entry must be at least 10m before apex
        while entry_idx < idx and (apex_dist - distance[entry_idx]) < 10:
            entry_idx = max(0, entry_idx - 1)
        dist_start = float(distance[entry_idx])

        # ── exit: walk forward to where speed recovers past apex + 5% ─
        search_fwd    = min(len(speed), idx + order * 4)
        recovery_tgt  = apex_speed * 1.05
        exit_candidates = np.where(speed[idx:search_fwd] > recovery_tgt)[0]
        if len(exit_candidates):
            exit_idx  = idx + int(exit_candidates[0])
        else:
            exit_idx  = min(len(distance) - 1, search_fwd)
        dist_end = float(distance[exit_idx])

        # ── guard: skip if zone is unrealistically narrow ─────────────
        if (dist_end - dist_start) < 20:
            continue

        corners.append({
            "corner_number": i + 1,
            "dist_start_m":  round(dist_start, 1),
            "dist_apex_m":   round(apex_dist,  1),
            "dist_end_m":    round(dist_end,   1),
        })

    print(f"  → {len(corners)} corners detected for {circuit_key}")
    return corners


# ──────────────────────────────────────────────────────────────────────
# DB UPSERT
# ──────────────────────────────────────────────────────────────────────
def upsert_corners(engine, circuit_key: str, corners: list[dict]):
    """
    Write detected corners to the corners table.
    Safe to re-run — uses ON CONFLICT DO UPDATE.
    """
    with engine.begin() as conn:
        for c in corners:
            conn.execute(text("""
                INSERT INTO corners
                    (circuit_key, corner_number, dist_start_m,
                     dist_apex_m, dist_end_m)
                VALUES
                    (:circuit_key, :corner_number, :dist_start_m,
                     :dist_apex_m, :dist_end_m)
                ON CONFLICT (circuit_key, corner_number)
                DO UPDATE SET
                    dist_start_m = EXCLUDED.dist_start_m,
                    dist_apex_m  = EXCLUDED.dist_apex_m,
                    dist_end_m   = EXCLUDED.dist_end_m
            """), {
                "circuit_key":   circuit_key,
                "corner_number": c["corner_number"],
                "dist_start_m":  c["dist_start_m"],
                "dist_apex_m":   c["dist_apex_m"],
                "dist_end_m":    c["dist_end_m"],
            })

    print(f"  → corners upserted to DB for {circuit_key}")


# ──────────────────────────────────────────────────────────────────────
# FETCH FROM DB (used by pages to get corner boundaries)
# ──────────────────────────────────────────────────────────────────────
def get_corners_from_db(engine, circuit_key: str) -> list[dict]:
    """
    Retrieve stored corner boundaries for a circuit.
    Returns list of dicts sorted by corner_number.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT corner_number, corner_name,
                   dist_start_m, dist_apex_m, dist_end_m
            FROM   corners
            WHERE  circuit_key = :ck
            ORDER  BY corner_number
        """), {"ck": circuit_key})
        rows = result.fetchall()

    return [
        {
            "corner_number": r[0],
            "corner_name":   r[1],
            "dist_start_m":  r[2],
            "dist_apex_m":   r[3],
            "dist_end_m":    r[4],
        }
        for r in rows
    ]