import numpy as np
import pandas as pd
from sqlalchemy import text


# ──────────────────────────────────────────────────────────────────────
# CUMULATIVE LAP DELTA
# ──────────────────────────────────────────────────────────────────────
def compute_cumulative_delta(distance: np.ndarray,
                              speed_a:  np.ndarray,
                              speed_b:  np.ndarray) -> np.ndarray:
    """
    Compute cumulative time delta between driver A and driver B
    across the full lap distance grid.

    Positive values = Driver A is ahead (faster up to that point)
    Negative values = Driver B is ahead (faster up to that point)

    Parameters
    ----------
    distance : shared distance grid in metres (300 points)
    speed_a  : Driver A speed in km/h
    speed_b  : Driver B speed in km/h

    Returns
    -------
    delta : np.ndarray of shape (300,) in seconds
    """

    # convert km/h → m/s, guard against zero division
    speed_a_ms = np.where(speed_a < 1.0, 1.0, speed_a * (1000 / 3600))
    speed_b_ms = np.where(speed_b < 1.0, 1.0, speed_b * (1000 / 3600))

    # time to cover each segment for each driver
    d_dist = np.diff(distance)
    dt_a   = d_dist / speed_a_ms[:-1]
    dt_b   = d_dist / speed_b_ms[:-1]

    # cumulative delta: positive = A faster
    delta = np.cumsum(dt_b - dt_a)

    # prepend 0.0 so array length matches distance grid
    delta = np.concatenate([[0.0], delta])

    return delta


# ──────────────────────────────────────────────────────────────────────
# CORNER ATTRIBUTION
# ──────────────────────────────────────────────────────────────────────
def attribute_delta_to_corners(distance: np.ndarray,
                                delta:    np.ndarray,
                                corners:  list[dict]) -> list[dict]:
    """
    Slice the cumulative delta at each corner zone boundary
    to compute net time gained or lost through that corner.

    Parameters
    ----------
    distance : shared distance grid
    delta    : cumulative delta array (same length as distance)
    corners  : list of corner dicts from corner_detector

    Returns
    -------
    list of dicts:
        corner_number, delta_s, driver_gaining, pct_of_lap_delta
    """

    total_delta = float(delta[-1])
    results     = []

    for corner in corners:
        # find indices within this corner zone
        mask = (
            (distance >= corner["dist_start_m"]) &
            (distance <= corner["dist_end_m"])
        )
        idxs = np.where(mask)[0]

        if len(idxs) < 2:
            continue

        # net delta through this corner zone
        net = float(delta[idxs[-1]] - delta[idxs[0]])

        # percentage contribution to overall lap delta
        if abs(total_delta) > 0.001:
            pct = round(abs(net) / abs(total_delta) * 100, 1)
        else:
            pct = 0.0

        results.append({
            "corner_number":  corner["corner_number"],
            "delta_s":        round(net, 3),
            "driver_gaining": "A" if net > 0 else "B",
            "pct_of_lap":     pct,
        })

    return results


# ──────────────────────────────────────────────────────────────────────
# STRAIGHT ATTRIBUTION
# ──────────────────────────────────────────────────────────────────────
def attribute_delta_to_straights(distance: np.ndarray,
                                  delta:    np.ndarray,
                                  corners:  list[dict]) -> list[dict]:
    """
    Compute time gained/lost on the straights between corners.
    Straights = zones not covered by any corner.
    """

    # build a boolean mask: True = inside a corner zone
    in_corner = np.zeros(len(distance), dtype=bool)
    for corner in corners:
        in_corner |= (
            (distance >= corner["dist_start_m"]) &
            (distance <= corner["dist_end_m"])
        )

    # find contiguous straight segments
    straight_mask = ~in_corner
    changes       = np.diff(straight_mask.astype(int))
    starts        = np.where(changes == 1)[0] + 1
    ends          = np.where(changes == -1)[0] + 1

    # handle edge cases
    if straight_mask[0]:
        starts = np.concatenate([[0], starts])
    if straight_mask[-1]:
        ends = np.concatenate([ends, [len(distance) - 1]])

    results = []
    for i, (s, e) in enumerate(zip(starts, ends)):
        if e <= s:
            continue
        net = float(delta[e] - delta[s])
        results.append({
            "straight_number": i + 1,
            "dist_start_m":    round(float(distance[s]), 1),
            "dist_end_m":      round(float(distance[e]), 1),
            "delta_s":         round(net, 3),
            "driver_gaining":  "A" if net > 0 else "B",
        })

    return results


# ──────────────────────────────────────────────────────────────────────
# SUMMARY TABLE
# ──────────────────────────────────────────────────────────────────────
def build_delta_summary(corner_deltas: list[dict],
                         driver_a: str,
                         driver_b: str) -> pd.DataFrame:
    """
    Build a clean summary DataFrame for display in the Streamlit page.

    Columns:
        Corner | Delta (s) | Gaining Driver | % of Lap Delta | Verdict
    """

    rows = []
    for c in corner_deltas:
        gainer  = driver_a if c["driver_gaining"] == "A" else driver_b
        verdict = f"{gainer} +{abs(c['delta_s']):.3f}s"
        rows.append({
            "Corner":          f"T{c['corner_number']}",
            "Delta (s)":       c["delta_s"],
            "Gaining Driver":  gainer,
            "% of Lap Delta":  c["pct_of_lap"],
            "Verdict":         verdict,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Delta (s)", key=abs, ascending=False)
    return df


# ──────────────────────────────────────────────────────────────────────
# FETCH FROM DB
# ──────────────────────────────────────────────────────────────────────
def get_delta_from_db(engine, session_id: int,
                       driver_a: str, driver_b: str) -> dict | None:
    """
    Retrieve a stored delta trace from the delta_traces table.
    Returns dict with distance_m and delta_s arrays, or None if not found.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT distance_m, delta_s
            FROM   delta_traces
            WHERE  session_id = :sid
            AND    driver_a   = :da
            AND    driver_b   = :db
            LIMIT  1
        """), {"sid": session_id, "da": driver_a, "db": driver_b})
        row = result.fetchone()

    if not row:
        return None

    return {
        "distance_m": np.array(row[0]),
        "delta_s":    np.array(row[1]),
    }