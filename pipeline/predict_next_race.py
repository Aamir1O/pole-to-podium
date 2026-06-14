import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pickle
import os

load_dotenv()
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, pool_size=2, max_overflow=0, connect_args={"connect_timeout": 10})

# load model & encoders
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model")
with open(f"{MODEL_DIR}/model.pkl", "rb") as f:
    model = pickle.load(f)
with open(f"{MODEL_DIR}/encoders.pkl", "rb") as f:
    enc = pickle.load(f)

le_driver  = enc["driver"]
le_team    = enc["team"]
le_circuit = enc["circuit"]
FEATURES   = enc["features"]

# load data
with engine.connect() as conn:
    results    = pd.read_sql(text("SELECT * FROM results"), conn)
    qualifying = pd.read_sql(text("SELECT * FROM qualifying"), conn)
    laps       = pd.read_sql(text("SELECT * FROM laps"), conn)
    weather    = pd.read_sql(text("SELECT * FROM weather"), conn)

# get latest qualifying
latest_race_id = qualifying["race_id"].max()
print(f"\n📡 Latest qualifying: {latest_race_id}")

# get race info
race_info = results[results["race_id"] == latest_race_id]
race_name = race_info["race_name"].iloc[0] if not race_info.empty else latest_race_id
circuit   = race_info["circuit"].iloc[0] if not race_info.empty else "Unknown"
print(f"   Race    : {race_name}")
print(f"   Circuit : {circuit}")

# historical features
avg_lap = (
    laps[laps["lap_time_secs"].notna()]
    .groupby("driver")["lap_time_secs"]
    .mean()
    .reset_index()
    .rename(columns={"lap_time_secs": "avg_lap_time"})
)

total_races = results.groupby("driver").size().reset_index(name="total_races")
total_wins  = results[results["finish_pos"]==1].groupby("driver").size().reset_index(name="total_wins")
win_rate    = total_races.merge(total_wins, on="driver", how="left").fillna(0)
win_rate["win_rate"] = win_rate["total_wins"] / win_rate["total_races"]

latest_team = (
    results.sort_values("race_id")
    .groupby("driver").last()
    .reset_index()[["driver","team"]]
)

# weather
latest_weather = weather[weather["race_id"] == latest_race_id]
avg_track_temp = float(latest_weather["avg_track_temp"].values[0]) if not latest_weather.empty else 28.0
avg_humidity   = float(latest_weather["avg_humidity"].values[0])   if not latest_weather.empty else 60.0
rainfall       = int(latest_weather["rainfall"].values[0])          if not latest_weather.empty else 0

# circuit encoding
circuit_enc = int(le_circuit.transform([circuit])[0]) if circuit in le_circuit.classes_ else 0

# build rows
quali = qualifying[qualifying["race_id"] == latest_race_id].copy()
quali = quali.drop_duplicates(subset=["driver"])
rows = []
for _, q in quali.iterrows():
    driver = q["driver"]

    team_row = latest_team[latest_team["driver"] == driver]
    team     = team_row["team"].values[0] if not team_row.empty else "Unknown"

    lap_row  = avg_lap[avg_lap["driver"] == driver]
    avg_l    = float(lap_row["avg_lap_time"].values[0]) if not lap_row.empty else np.nan

    wr_row   = win_rate[win_rate["driver"] == driver]
    wr       = float(wr_row["win_rate"].values[0]) if not wr_row.empty else 0.0

    driver_enc = int(le_driver.transform([driver])[0]) if driver in le_driver.classes_ else -1
    team_enc   = int(le_team.transform([team])[0])     if team in le_team.classes_     else -1

    q3 = q["q3_secs"] if pd.notna(q["q3_secs"]) else q["q1_secs"]

    rows.append({
        "driver"        : driver,
        "team"          : team,
        "grid_pos"      : float(q["grid_pos"]),
        "driver_enc"    : driver_enc,
        "team_enc"      : team_enc,
        "circuit_enc"   : circuit_enc,
        "avg_lap_time"  : avg_l,
        "avg_track_temp": avg_track_temp,
        "avg_humidity"  : avg_humidity,
        "rainfall"      : rainfall,
        "q3_secs"       : float(q3) if pd.notna(q3) else np.nan,
        "win_rate"      : wr,
    })

pred = pd.DataFrame(rows).dropna(subset=FEATURES)
X    = pred[FEATURES].astype(float)

pred["win_probability"] = model.predict_proba(X)[:,1]
prob_sum = pred["win_probability"].sum()
if prob_sum > 0:
    pred["win_probability"] = pred["win_probability"] / prob_sum
pred = pred.sort_values("win_probability", ascending=False)

print(f"\n{'='*58}")
print(f"  🏁 {race_name} — Win Predictions")
print(f"{'='*58}")
for _, row in pred.head(10).iterrows():
    team = str(row["team"])[:15]
    bar  = "█" * int(row["win_probability"] * 50)
    print(f"  {row['driver']:4s} ({team:15s}) P{int(row['grid_pos'])}  {row['win_probability']*100:5.1f}%  {bar}")
print(f"{'='*58}")