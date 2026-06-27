import os
import pickle
import numpy as np
import pandas as pd
from functools import lru_cache


@lru_cache(maxsize=1)
def load_model():
    MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model")
    with open(f"{MODEL_DIR}/model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(f"{MODEL_DIR}/encoders.pkl", "rb") as f:
        enc = pickle.load(f)
    return model, enc


def _get_practice_features(practice_df: pd.DataFrame, race_id: str) -> pd.DataFrame:
    """
    Best lap per driver across all available FP sessions for a race_id.
    Returns DataFrame with driver, team, best_lap_secs, estimated_grid.
    """
    if practice_df is None or practice_df.empty:
        return pd.DataFrame()

    fp = practice_df[practice_df["race_id"] == race_id].copy()
    if fp.empty:
        return pd.DataFrame()

    fp_best = (
        fp.sort_values("best_lap_secs")
        .groupby("driver")
        .first()
        .reset_index()
    )
    fp_best = fp_best.sort_values("best_lap_secs").reset_index(drop=True)
    fp_best["estimated_grid"] = fp_best.index + 1

    # which sessions are available
    sessions = sorted(fp["session"].unique().tolist())
    fp_best["latest_session"] = sessions[-1] if sessions else "FP1"

    return fp_best


def build_predictions(
    results_df, laps_df, qualifying_df, weather_df,
    race_id, circuit_name,
    le_driver, le_team, le_circuit, features, model,
    practice_df: pd.DataFrame = None,
):
    # ── historical features ───────────────────────────────────────────
    if not laps_df.empty:
        avg_lap_by_race = (
            laps_df[laps_df["lap_time_secs"].notna()]
            .groupby(["race_id", "driver"])["lap_time_secs"]
            .mean()
            .reset_index()
        )
        race_means = avg_lap_by_race.groupby("race_id")["lap_time_secs"].transform("mean")
        avg_lap_by_race["lap_time_delta_pct"] = (avg_lap_by_race["lap_time_secs"] - race_means) / race_means
        
        avg_lap = (
            avg_lap_by_race.groupby("driver")["lap_time_delta_pct"]
            .mean()
            .reset_index()
            .rename(columns={"lap_time_delta_pct": "avg_lap_time"})
        )
    else:
        avg_lap = pd.DataFrame(columns=["driver", "avg_lap_time"])

    total_races = results_df.groupby("driver").size().reset_index(name="total_races")
    total_wins  = (
        results_df[results_df["finish_pos"] == 1]
        .groupby("driver").size().reset_index(name="total_wins")
    )
    win_rate = total_races.merge(total_wins, on="driver", how="left").fillna(0)
    win_rate["win_rate"] = win_rate["total_wins"] / win_rate["total_races"]

    latest_team = (
        results_df.sort_values("race_id")
        .groupby("driver").last()
        .reset_index()[["driver", "team"]]
    )

    # ── weather ───────────────────────────────────────────────────────
    wrow           = weather_df[weather_df["race_id"] == race_id]
    avg_track_temp = float(wrow["avg_track_temp"].values[0]) if not wrow.empty else 28.0
    avg_humidity   = float(wrow["avg_humidity"].values[0])   if not wrow.empty else 60.0
    rainfall       = int(wrow["rainfall"].values[0])          if not wrow.empty else 0
    circuit_enc    = (
        int(le_circuit.transform([circuit_name])[0])
        if circuit_name in le_circuit.classes_ else 0
    )

    # ── decide data source: quali or practice fallback ────────────────
    quali = qualifying_df[qualifying_df["race_id"] == race_id].copy()
    fp    = _get_practice_features(practice_df, race_id)

    has_quali    = not quali.empty
    has_practice = not fp.empty

    if not has_quali and not has_practice:
        return pd.DataFrame()

    # ── build rows ────────────────────────────────────────────────────
    rows        = []
    data_source = "Qualifying" if has_quali else f"Practice ({fp['latest_session'].iloc[0]})"

    if has_quali:
        quali = quali.copy()
        quali["best_q_secs"] = quali["q3_secs"].fillna(quali["q2_secs"]).fillna(quali["q1_secs"])
        pole_time = quali["best_q_secs"].min()
        drivers_iter = quali.iterrows()
    else:
        # use practice, estimate grid from pace order
        fp = fp.copy()
        pole_time = fp["best_lap_secs"].min()
        drivers_iter = fp.iterrows()

    for _, q in drivers_iter:
        driver = q["driver"]

        team_row = latest_team[latest_team["driver"] == driver]
        team     = team_row["team"].values[0] if not team_row.empty else q.get("team", "Unknown")

        lap_row  = avg_lap[avg_lap["driver"] == driver]
        avg_l    = float(lap_row["avg_lap_time"].values[0]) if not lap_row.empty else 0.0

        wr_row   = win_rate[win_rate["driver"] == driver]
        wr       = float(wr_row["win_rate"].values[0]) if not wr_row.empty else 0.0

        driver_enc = int(le_driver.transform([driver])[0]) if driver in le_driver.classes_ else -1
        team_enc   = int(le_team.transform([team])[0])     if team in le_team.classes_     else -1

        if has_quali:
            grid_pos = float(q["grid_pos"])
            best_q   = float(q["best_q_secs"]) if pd.notna(q["best_q_secs"]) else pole_time
            q3_val   = best_q - pole_time
        else:
            # estimated grid from practice pace ranking
            grid_pos = float(q["estimated_grid"])
            best_q   = float(q["best_lap_secs"]) if pd.notna(q["best_lap_secs"]) else pole_time
            q3_val   = best_q - pole_time

        rows.append({
            "driver":         driver,
            "team":           team,
            "grid_pos":       grid_pos,
            "driver_enc":     driver_enc,
            "team_enc":       team_enc,
            "circuit_enc":    circuit_enc,
            "avg_lap_time":   avg_l,
            "avg_track_temp": avg_track_temp,
            "avg_humidity":   avg_humidity,
            "rainfall":       rainfall,
            "q3_secs":        q3_val,
            "win_rate":       wr,
            "data_source":    data_source,
        })

    pred = pd.DataFrame(rows).dropna(subset=features)
    if pred.empty:
        return pred

    pred["win_probability"] = model.predict_proba(
        pred[features].astype(float)
    )[:, 1]

    # Normalize so that probabilities sum to 1.0 (100%)
    prob_sum = pred["win_probability"].sum()
    if prob_sum > 0:
        pred["win_probability"] = pred["win_probability"] / prob_sum

    return pred.sort_values(
        "win_probability", ascending=False
    ).reset_index(drop=True)