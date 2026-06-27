import os
import sys
import pickle
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
import xgboost as xgb
from dotenv import load_dotenv

# Set paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv(os.path.join(base_dir, ".env"))
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL is missing from .env file.")

def main():
    print("📡 Connecting to Supabase...")
    engine = create_engine(DB_URL)
    
    # 1. Load data
    results = pd.read_sql(text("SELECT * FROM results WHERE year = 2026"), engine)
    qualifying = pd.read_sql(text("SELECT * FROM qualifying WHERE race_id LIKE '2026%'"), engine)
    weather = pd.read_sql(text("SELECT * FROM weather WHERE race_id LIKE '2026%'"), engine)
    laps = pd.read_sql(text("SELECT * FROM laps WHERE race_id LIKE '2026%'"), engine)
    
    if results.empty or qualifying.empty:
        print("❌ Error: Results or Qualifying table is empty. Load data first!")
        return

    print(f"Loaded {len(results)} results, {len(qualifying)} qualifying, {len(weather)} weather, {len(laps)} laps.")

    # 2. Build dataset chronologically to avoid future leakage in historical features
    race_ids = sorted(results["race_id"].unique())
    df_rows = []
    
    for i, race_id in enumerate(race_ids):
        # past results for historical features
        past_results = results[results["race_id"].isin(race_ids[:i])]
        past_laps = laps[laps["race_id"].isin(race_ids[:i])]
        
        # Calculate historical win rate prior to this race
        if not past_results.empty:
            total_races = past_results.groupby("driver").size().reset_index(name="total_races")
            total_wins = past_results[past_results["finish_pos"] == 1].groupby("driver").size().reset_index(name="total_wins")
            win_rate_df = total_races.merge(total_wins, on="driver", how="left").fillna(0)
            win_rate_df["win_rate"] = win_rate_df["total_wins"] / win_rate_df["total_races"]
        else:
            win_rate_df = pd.DataFrame(columns=["driver", "win_rate"])
            
        # Calculate historical average lap time relative delta prior to this race
        if not past_laps.empty:
            past_avg_lap = (
                past_laps[past_laps["lap_time_secs"].notna()]
                .groupby(["race_id", "driver"])["lap_time_secs"]
                .mean()
                .reset_index()
            )
            # normalize to race average to make it track-agnostic
            race_means = past_avg_lap.groupby("race_id")["lap_time_secs"].transform("mean")
            past_avg_lap["lap_time_delta_pct"] = (past_avg_lap["lap_time_secs"] - race_means) / race_means
            
            # average of the delta_pct across all past races
            driver_pace = past_avg_lap.groupby("driver")["lap_time_delta_pct"].mean().reset_index().rename(columns={"lap_time_delta_pct": "avg_lap_time"})
        else:
            driver_pace = pd.DataFrame(columns=["driver", "avg_lap_time"])
            
        # Current race features
        curr_results = results[results["race_id"] == race_id]
        curr_quali = qualifying[qualifying["race_id"] == race_id]
        curr_weather = weather[weather["race_id"] == race_id]
        
        avg_track_temp = float(curr_weather["avg_track_temp"].values[0]) if not curr_weather.empty else 28.0
        avg_humidity = float(curr_weather["avg_humidity"].values[0]) if not curr_weather.empty else 60.0
        rainfall = int(curr_weather["rainfall"].values[0]) if not curr_weather.empty else 0
        
        # pole Q3 time for relative Q3 delta
        curr_quali = curr_quali.copy()
        curr_quali["best_q_secs"] = curr_quali["q3_secs"].fillna(curr_quali["q2_secs"]).fillna(curr_quali["q1_secs"])
        pole_time = curr_quali["best_q_secs"].min()
        
        for _, r in curr_results.iterrows():
            driver = r["driver"]
            q_row = curr_quali[curr_quali["driver"] == driver]
            if q_row.empty:
                continue
                
            grid_pos = float(q_row["grid_pos"].values[0])
            best_q = float(q_row["best_q_secs"].values[0]) if pd.notna(q_row["best_q_secs"].values[0]) else pole_time
            q3_delta = best_q - pole_time
            
            wr = float(win_rate_df[win_rate_df["driver"] == driver]["win_rate"].values[0]) if driver in win_rate_df["driver"].values else 0.0
            avg_l = float(driver_pace[driver_pace["driver"] == driver]["avg_lap_time"].values[0]) if driver in driver_pace["driver"].values else 0.0
            
            df_rows.append({
                "race_id": race_id,
                "driver": driver,
                "team": r["team"],
                "grid_pos": grid_pos,
                "avg_lap_time": avg_l,
                "avg_track_temp": avg_track_temp,
                "avg_humidity": avg_humidity,
                "rainfall": rainfall,
                "q3_secs": q3_delta,
                "win_rate": wr,
                "won": 1 if r["finish_pos"] == 1 else 0
            })
            
    df = pd.DataFrame(df_rows)
    print(f"Prepared dataset with {len(df)} rows.")

    # 3. Train the model
    FEATURES = ["grid_pos", "avg_lap_time", "avg_track_temp", "avg_humidity", "rainfall", "q3_secs", "win_rate"]
    X = df[FEATURES]
    y = df["won"]
    
    # Train simple model (to prevent overfitting on 154 samples)
    model = xgb.XGBClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        subsample=0.8,
        eval_metric="logloss",
        random_state=42
    )
    model.fit(X, y)
    print("Trained new XGBoost model.")

    # 4. Save model and encoders
    # Prepare dummy LabelEncoders to satisfy structure (since we are not using enc features anymore)
    from sklearn.preprocessing import LabelEncoder
    le_driver = LabelEncoder().fit(df["driver"].astype(str))
    le_team = LabelEncoder().fit(df["team"].astype(str))
    le_circuit = LabelEncoder().fit(results["circuit"].astype(str))
    
    MODEL_DIR = os.path.join(base_dir, "model")
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Save model.pkl
    with open(f"{MODEL_DIR}/model.pkl", "wb") as f:
        pickle.dump(model, f)
        
    # Save encoders.pkl
    with open(f"{MODEL_DIR}/encoders.pkl", "wb") as f:
        pickle.dump({
            "driver": le_driver,
            "team": le_team,
            "circuit": le_circuit,
            "features": FEATURES
        }, f)
        
    print("💾 model.pkl and encoders.pkl saved successfully to model/ directory!")

if __name__ == "__main__":
    main()
