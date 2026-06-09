import os
import pickle
import numpy as np
import pandas as pd
import streamlit as st


@st.cache_resource
def load_model():
    MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model")
    with open(f"{MODEL_DIR}/model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(f"{MODEL_DIR}/encoders.pkl", "rb") as f:
        enc = pickle.load(f)
    return model, enc


def build_predictions(
    results_df, laps_df, qualifying_df, weather_df,
    race_id, circuit_name,
    le_driver, le_team, le_circuit, features, model,
):
    avg_lap = (
        laps_df[laps_df["lap_time_secs"].notna()]
        .groupby("driver")["lap_time_secs"]
        .mean()
        .reset_index()
        .rename(columns={"lap_time_secs": "avg_lap_time"})
    )

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

    wrow           = weather_df[weather_df["race_id"] == race_id]
    avg_track_temp = float(wrow["avg_track_temp"].values[0]) if not wrow.empty else 28.0
    avg_humidity   = float(wrow["avg_humidity"].values[0])   if not wrow.empty else 60.0
    rainfall       = int(wrow["rainfall"].values[0])          if not wrow.empty else 0
    circuit_enc    = (
        int(le_circuit.transform([circuit_name])[0])
        if circuit_name in le_circuit.classes_ else 0
    )

    quali = qualifying_df[qualifying_df["race_id"] == race_id].copy()
    rows  = []
    for _, q in quali.iterrows():
        driver     = q["driver"]
        team_row   = latest_team[latest_team["driver"] == driver]
        team       = team_row["team"].values[0] if not team_row.empty else "Unknown"
        lap_row    = avg_lap[avg_lap["driver"] == driver]
        avg_l      = float(lap_row["avg_lap_time"].values[0]) if not lap_row.empty else np.nan
        wr_row     = win_rate[win_rate["driver"] == driver]
        wr         = float(wr_row["win_rate"].values[0]) if not wr_row.empty else 0.0
        driver_enc = int(le_driver.transform([driver])[0]) if driver in le_driver.classes_ else -1
        team_enc   = int(le_team.transform([team])[0])     if team in le_team.classes_     else -1
        q3         = q["q3_secs"] if pd.notna(q.get("q3_secs", np.nan)) else q["q1_secs"]
        rows.append({
            "driver":         driver,
            "team":           team,
            "grid_pos":       float(q["grid_pos"]),
            "driver_enc":     driver_enc,
            "team_enc":       team_enc,
            "circuit_enc":    circuit_enc,
            "avg_lap_time":   avg_l,
            "avg_track_temp": avg_track_temp,
            "avg_humidity":   avg_humidity,
            "rainfall":       rainfall,
            "q3_secs":        float(q3) if pd.notna(q3) else np.nan,
            "win_rate":       wr,
        })

    pred = pd.DataFrame(rows).dropna(subset=features)
    if pred.empty:
        return pred
    pred["win_probability"] = model.predict_proba(pred[features].astype(float))[:, 1]
    return pred.sort_values("win_probability", ascending=False).reset_index(drop=True)