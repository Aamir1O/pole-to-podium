import numpy as np
import pandas as pd
from dataclasses import dataclass, field

# ── CPI weighting constants ────────────────────────────────────────────
CPI_WEIGHTS = {
    "entry": 0.30,
    "apex":  0.40,
    "exit":  0.30,
}


# ──────────────────────────────────────────────────────────────────────
# DATA CLASS — one instance per driver per corner
# ──────────────────────────────────────────────────────────────────────
@dataclass
class CornerMetrics:
    corner_number:          int
    entry_speed_kph:        float
    brake_point_m:          float
    brake_duration_m:       float
    apex_speed_kph:         float
    apex_dist_m:            float
    exit_speed_kph:         float
    throttle_point_m:       float
    time_to_full_throttle_s: float
    corner_time_s:          float
    driver:                 str   = ""   # "A" or "B"


# ──────────────────────────────────────────────────────────────────────
# METRIC EXTRACTION — one corner, one driver
# ──────────────────────────────────────────────────────────────────────
def extract_corner_metrics(distance: np.ndarray,
                           speed:    np.ndarray,
                           throttle: np.ndarray,
                           brake:    np.ndarray,
                           corner:   dict,
                           driver:   str = "") -> CornerMetrics | None:
    """
    Slice telemetry arrays to the corner zone and extract
    entry / apex / exit metrics.

    Parameters
    ----------
    distance  : normalised distance grid (metres)
    speed     : speed in km/h
    throttle  : throttle 0.0 – 1.0
    brake     : brake 0.0 – 1.0
    corner    : dict with dist_start_m, dist_apex_m, dist_end_m
    driver    : label string "A" or "B"
    """

    mask = (
        (distance >= corner["dist_start_m"]) &
        (distance <= corner["dist_end_m"])
    )
    d = distance[mask]
    s = speed[mask]
    t = throttle[mask]
    b = brake[mask]

    # need at least 5 points to be meaningful
    if len(d) < 5:
        return None

    # ── entry ─────────────────────────────────────────────────────────
    entry_speed = float(s[0])

    # brake point: first sample where brake > 0.05 heading into corner
    brake_idxs  = np.where(b > 0.05)[0]
    if len(brake_idxs):
        brake_point    = float(d[brake_idxs[0]])
        # brake duration: from first brake to apex
        apex_local_idx = int(np.argmin(s))
        brake_duration = float(d[apex_local_idx] - brake_point)
        brake_duration = max(brake_duration, 0.0)
    else:
        brake_point    = float(d[0])
        brake_duration = 0.0

    # ── apex ──────────────────────────────────────────────────────────
    apex_local_idx = int(np.argmin(s))
    apex_speed     = float(s[apex_local_idx])
    apex_dist      = float(d[apex_local_idx])

    # ── exit ──────────────────────────────────────────────────────────
    exit_speed = float(s[-1])

    # throttle application point: first sample after apex where throttle > 0.95
    post_apex_throttle = t[apex_local_idx:]
    post_apex_dist     = d[apex_local_idx:]
    full_thr_idxs      = np.where(post_apex_throttle > 0.95)[0]
    if len(full_thr_idxs):
        throttle_point = float(post_apex_dist[full_thr_idxs[0]])
    else:
        throttle_point = float(d[-1])

    # time to full throttle (seconds): distance from apex to throttle point
    # divided by average speed in that zone
    zone_dist = throttle_point - apex_dist
    avg_speed_ms = max(
        float(np.mean(post_apex_throttle[:full_thr_idxs[0] + 1]
                      if len(full_thr_idxs) else post_apex_throttle))
        * (1000 / 3600), 0.1
    )
    time_to_full_throttle = zone_dist / avg_speed_ms if zone_dist > 0 else 0.0

    # ── corner time: trapezoidal integration ──────────────────────────
    speed_ms    = s * (1000 / 3600)
    speed_ms    = np.where(speed_ms < 0.1, 0.1, speed_ms)
    d_dist      = np.diff(d)
    dt          = d_dist / speed_ms[:-1]
    corner_time = float(np.sum(dt))

    return CornerMetrics(
        corner_number=corner["corner_number"],
        entry_speed_kph=round(entry_speed, 2),
        brake_point_m=round(brake_point, 1),
        brake_duration_m=round(brake_duration, 1),
        apex_speed_kph=round(apex_speed, 2),
        apex_dist_m=round(apex_dist, 1),
        exit_speed_kph=round(exit_speed, 2),
        throttle_point_m=round(throttle_point, 1),
        time_to_full_throttle_s=round(time_to_full_throttle, 3),
        corner_time_s=round(corner_time, 3),
        driver=driver,
    )


# ──────────────────────────────────────────────────────────────────────
# CPI COMPUTATION — normalise + score across both drivers
# ──────────────────────────────────────────────────────────────────────
def compute_cpi(metrics_a: list[CornerMetrics],
                metrics_b: list[CornerMetrics]) -> pd.DataFrame:
    """
    Z-normalise entry/apex/exit speeds across both drivers,
    rescale to 0–100, compute weighted CPI.

    Returns a DataFrame with columns:
        driver, corner, entry, apex, exit,
        entry_score, apex_score, exit_score, cpi,
        corner_time_s, brake_point_m, brake_duration_m,
        throttle_point_m, time_to_full_throttle_s
    """

    rows = []
    for m in metrics_a:
        if m:
            rows.append(_metrics_to_row(m, "A"))
    for m in metrics_b:
        if m:
            rows.append(_metrics_to_row(m, "B"))

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # ── z-normalise per metric, rescale to 0–100 ─────────────────────
    for col in ["entry", "apex", "exit"]:
        mu    = df[col].mean()
        sigma = df[col].std()
        if sigma < 0.01:
            df[f"{col}_score"] = 50.0
        else:
            df[f"{col}_score"] = (
                ((df[col] - mu) / sigma) * 15 + 50
            ).clip(0, 100)

    # ── weighted CPI ──────────────────────────────────────────────────
    df["cpi"] = (
        CPI_WEIGHTS["entry"] * df["entry_score"] +
        CPI_WEIGHTS["apex"]  * df["apex_score"]  +
        CPI_WEIGHTS["exit"]  * df["exit_score"]
    ).round(2)

    return df


def _metrics_to_row(m: CornerMetrics, driver_label: str) -> dict:
    return {
        "driver":                   driver_label,
        "corner":                   m.corner_number,
        "entry":                    m.entry_speed_kph,
        "apex":                     m.apex_speed_kph,
        "exit":                     m.exit_speed_kph,
        "corner_time_s":            m.corner_time_s,
        "brake_point_m":            m.brake_point_m,
        "brake_duration_m":         m.brake_duration_m,
        "throttle_point_m":         m.throttle_point_m,
        "time_to_full_throttle_s":  m.time_to_full_throttle_s,
    }


# ──────────────────────────────────────────────────────────────────────
# NATURAL LANGUAGE EXPLANATION
# ──────────────────────────────────────────────────────────────────────
def explain_corner_delta(corner_num: int, df: pd.DataFrame,
                          driver_a: str, driver_b: str) -> str:
    """
    Given the CPI dataframe and two driver codes, return a plain-English
    explanation of why one driver is faster through a specific corner.
    """
    row_a = df[(df["driver"] == "A") & (df["corner"] == corner_num)]
    row_b = df[(df["driver"] == "B") & (df["corner"] == corner_num)]

    if row_a.empty or row_b.empty:
        return ""

    apex_diff  = row_a["apex"].values[0]  - row_b["apex"].values[0]
    exit_diff  = row_a["exit"].values[0]  - row_b["exit"].values[0]
    brake_diff = row_b["brake_point_m"].values[0] - row_a["brake_point_m"].values[0]

    # decision tree: largest contributor wins
    if abs(apex_diff) >= 3:
        faster = driver_a if apex_diff > 0 else driver_b
        return (f"due to {abs(apex_diff):.1f} km/h higher minimum speed at apex")

    if abs(exit_diff) >= 5:
        faster = driver_a if exit_diff > 0 else driver_b
        return (f"due to earlier throttle application "
                f"(+{abs(exit_diff):.1f} km/h on exit)")

    if abs(brake_diff) >= 5:
        faster = driver_a if brake_diff > 0 else driver_b
        return (f"due to a {abs(brake_diff):.0f}m later brake point")

    return "due to a combination of entry and exit technique"