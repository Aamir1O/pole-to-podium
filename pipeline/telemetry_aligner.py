import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

N_GRID = 300  # fixed resampling resolution — all laps normalised to this


def load_and_align(session, driver_a: str, driver_b: str) -> dict:
    """
    Given an already-loaded FastF1 session object, extract and align
    the fastest lap telemetry for two drivers onto a common distance grid.
    Returns a dict with aligned arrays + lap times.
    """

    # ── get fastest laps ──────────────────────────────────────────────
    lap_a = session.laps.pick_driver(driver_a).pick_fastest()
    lap_b = session.laps.pick_driver(driver_b).pick_fastest()

    if lap_a is None or lap_a.empty:
        raise ValueError(
            f"{driver_a} has no valid lap data in this session"
        )
    if lap_b is None or lap_b.empty:
        raise ValueError(f"No fastest lap found for {driver_b}")

    # ── get telemetry with distance channel ───────────────────────────
    tel_a = lap_a.get_telemetry().add_distance()
    tel_b = lap_b.get_telemetry().add_distance()

    # ── validate required channels exist ─────────────────────────────
    required = ["Distance", "Speed", "Throttle", "Brake", "RPM", "nGear"]
    for ch in required:
        if ch not in tel_a.columns:
            raise ValueError(f"Channel '{ch}' missing from {driver_a} telemetry")
        if ch not in tel_b.columns:
            raise ValueError(f"Channel '{ch}' missing from {driver_b} telemetry")

    # ── drop any duplicate distance values (can happen at lap seams) ──
    tel_a = tel_a.drop_duplicates(subset="Distance").sort_values("Distance")
    tel_b = tel_b.drop_duplicates(subset="Distance").sort_values("Distance")

    # ── common grid: use shorter lap distance as upper bound ──────────
    max_dist = min(tel_a["Distance"].max(), tel_b["Distance"].max())
    grid = np.linspace(0, max_dist, N_GRID)

    # ── resample both drivers onto the common grid ────────────────────
    channels = ["Speed", "Throttle", "Brake", "RPM", "nGear"]

    # DRS and X/Y are optional — include if present
    for optional in ["DRS", "X", "Y"]:
        if optional in tel_a.columns and optional in tel_b.columns:
            channels.append(optional)

    def resample(tel: pd.DataFrame) -> dict:
        out = {"distance_m": grid}
        for ch in channels:
            f = interp1d(
                tel["Distance"].values,
                tel[ch].values.astype(float),
                kind="linear",
                bounds_error=False,
                fill_value="extrapolate",
            )
            out[ch] = f(grid)
        return out

    aligned_a = resample(tel_a)
    aligned_b = resample(tel_b)

    # ── clip throttle/brake to valid range after interpolation ────────
    for tel in [aligned_a, aligned_b]:
        tel["Throttle"] = np.clip(tel["Throttle"], 0.0, 1.0)
        tel["Brake"]    = np.clip(tel["Brake"],    0.0, 1.0)
        tel["Speed"]    = np.clip(tel["Speed"],    0.0, None)

    # ── lap times in seconds ──────────────────────────────────────────
    lap_time_a = lap_a["LapTime"].total_seconds()
    lap_time_b = lap_b["LapTime"].total_seconds()

    return {
        "driver_a":   aligned_a,
        "driver_b":   aligned_b,
        "grid":       grid,
        "lap_time_a": lap_time_a,
        "lap_time_b": lap_time_b,
    }