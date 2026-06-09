import fastf1
import pandas as pd
import os
import logging
import traceback

from datetime import datetime

logging.getLogger("fastf1").setLevel(logging.ERROR)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

def t_secs(t):
    try:
        return round(t.total_seconds(), 3)
    except Exception:
        return None

def fetch_sprint_points(year, rnd):
    sprint_pts = {}

    SPRINT_POINTS = {
        1: 8,
        2: 7,
        3: 6,
        4: 5,
        5: 4,
        6: 3,
        7: 2,
        8: 1
    }

    try:
        sprint = fastf1.get_session(year, rnd, "Sprint")
        sprint.load(
            laps=False,
            telemetry=False,
            weather=False,
            messages=False
        )

        if sprint.results is not None and not sprint.results.empty:

            for _, row in sprint.results.iterrows():

                drv = row.get("Abbreviation", "")
                pos = row.get("Position")

                if drv and pd.notna(pos):
                    pos = int(pos)
                    sprint_pts[drv] = SPRINT_POINTS.get(pos, 0)

            if sprint_pts:
                print(f"   🏃 Sprint points: {sprint_pts}")

    except Exception as e:
        print(f"   ⚠️ Sprint fetch failed: {e}")
    return sprint_pts

   

def fetch_race(year, rnd):
    print(f"\n📡 Fetching {year} Round {rnd}...", flush=True)
    results_rows, laps_rows, weather_rows, quali_rows = [], [], [], []

    try:
        race = fastf1.get_session(year, rnd, "R")
        race.load(telemetry=False, messages=False)

        race_name = race.event.get("EventName", "Unknown")
        circuit   = race.event.get("Location", "Unknown")
        date_str  = str(race.date.date()) if race.date else ""
        race_id   = f"{year}_R{rnd:02d}"
        print(f"   🏁 {race_name} — {circuit}")

        sprint_pts = fetch_sprint_points(year, rnd)

        for _, row in race.results.iterrows():
            drv         = row.get("Abbreviation", "")
            race_points = float(row.get("Points", 0) or 0)
            extra       = sprint_pts.get(drv, 0.0)
            results_rows.append({
                "race_id":    race_id,
                "year":       year,
                "round":      rnd,
                "race_name":  race_name,
                "circuit":    circuit,
                "date":       date_str,
                "driver":     drv,
                "team":       row.get("TeamName", ""),
                "finish_pos": row.get("Position"),
                "grid_pos":   row.get("GridPosition"),
                "points":     race_points,
                "sprint_pts": extra,
                "status":     row.get("Status", ""),
            })

        try:
            for _, lap in race.laps.iterrows():
                laps_rows.append({
                    "race_id":       race_id,
                    "driver":        lap.get("Driver", ""),
                    "lap_number":    lap.get("LapNumber"),
                    "lap_time_secs": t_secs(lap.get("LapTime")),
                    "tyre_compound": lap.get("Compound"),
                    "tyre_age":      lap.get("TyreLife"),
                    "stint":         lap.get("Stint"),
                    "is_pit_lap":    1 if pd.notna(lap.get("PitInTime")) else 0,
                })
        except Exception as e:
            print(f"   ⚠️  Laps: {e}")

        try:
            w = race.weather_data
            if w is not None and not w.empty:
                weather_rows.append({
                    "race_id":        race_id,
                    "session":        "R",
                    "avg_air_temp":   round(float(w["AirTemp"].mean()), 2),
                    "avg_track_temp": round(float(w["TrackTemp"].mean()), 2),
                    "avg_humidity":   round(float(w["Humidity"].mean()), 2),
                    "avg_wind_speed": round(float(w["WindSpeed"].mean()), 2),
                    "rainfall":       int(w["Rainfall"].any()),
                })
        except Exception as e:
            print(f"   ⚠️  Weather: {e}")

        try:
            quali = fastf1.get_session(year, rnd, "Q")
            quali.load(telemetry=False, messages=False)
            for _, row in quali.results.iterrows():
                quali_rows.append({
                    "race_id":  race_id,
                    "driver":   row.get("Abbreviation", ""),
                    "team":     row.get("TeamName", ""),
                    "grid_pos": row.get("Position"),
                    "q1_secs":  t_secs(row.get("Q1")),
                    "q2_secs":  t_secs(row.get("Q2")),
                    "q3_secs":  t_secs(row.get("Q3")),
                })
        except Exception as e:
            print(f"   ⚠️  Qualifying: {e}")

        sprint_note = f" (incl. {sum(sprint_pts.values()):.0f} sprint pts)" if sprint_pts else ""
        print(f"   ✅ {len(results_rows)} results | {len(laps_rows)} laps | quali: {len(quali_rows)} drivers{sprint_note}")
        return results_rows, laps_rows, weather_rows, quali_rows

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        traceback.print_exc()
        return [], [], [], []

def fetch_season(year):
    print(f"\n🏁 Fetching {year} season...")
    all_results, all_laps, all_weather, all_quali = [], [], [], []

    # load already-fetched race IDs to skip them
    existing_results_csv = f"{DATA_DIR}/results_{year}.csv"
    existing_ids = set()
    if ( 
        os.path.exists(existing_results_csv) 
        and os.path.getsize(existing_results_csv) > 0
    ):
        existing_ids = set(pd.read_csv(existing_results_csv)["race_id"].unique())
        print(f"   Already have: {sorted(existing_ids)}")

        # preload existing data so we can append new races
        all_results = pd.read_csv(f"{DATA_DIR}/results_{year}.csv").to_dict("records")
        if os.path.exists(f"{DATA_DIR}/laps_{year}.csv"):
            all_laps = pd.read_csv(f"{DATA_DIR}/laps_{year}.csv").to_dict("records")
        if os.path.exists(f"{DATA_DIR}/weather_{year}.csv"):
            all_weather = pd.read_csv(f"{DATA_DIR}/weather_{year}.csv").to_dict("records")
        if os.path.exists(f"{DATA_DIR}/qualifying_{year}.csv"):
            all_quali = pd.read_csv(f"{DATA_DIR}/qualifying_{year}.csv").to_dict("records")

    schedule = fastf1.get_event_schedule(year, include_testing=False)
    now = datetime.now()
    new_races = 0

    for _, event in schedule.iterrows():
        event_date = pd.to_datetime(event.get("EventDate"))
        if event_date.to_pydatetime().replace(tzinfo=None) > now:
            print(f"  ⏭  Round {int(event['RoundNumber'])} ({event['EventName']}) — future race")
            continue

        race_id = f"{year}_R{int(event['RoundNumber']):02d}"
        if race_id in existing_ids:
            print(f"  🔄 Updating {race_id}")

            all_results = [
                row for row in all_results
                if row["race_id"] != race_id
            ]

            all_laps = [
                row for row in all_laps
                if row["race_id"] != race_id
            ]

            all_weather = [
                row for row in all_weather
                if row["race_id"] != race_id
            ]

            all_quali = [
                row for row in all_quali
                if row["race_id"] != race_id
            ]
        r, l, w, q = fetch_race(year, int(event["RoundNumber"]))
        all_results.extend(r)
        all_laps.extend(l)
        all_weather.extend(w)
        all_quali.extend(q)
        all_quali = (
            pd.DataFrame(all_quali)
            .drop_duplicates(
                subset=["race_id", "driver"],
                keep="last"
            )
             .to_dict("records")
        )
        new_races += 1

    if new_races == 0:
        print(f"\n✅ Nothing new to fetch for {year} — all races already saved!")
        return

    # save updated CSVs
    pd.DataFrame(all_results).to_csv(f"{DATA_DIR}/results_{year}.csv", index=False)
    print(f"\n💾 results_{year}.csv — {len(all_results)} rows")

    if all_laps:
        pd.DataFrame(all_laps).to_csv(f"{DATA_DIR}/laps_{year}.csv", index=False)
        print(f"💾 laps_{year}.csv — {len(all_laps)} rows")

    if all_weather:
        pd.DataFrame(all_weather).to_csv(f"{DATA_DIR}/weather_{year}.csv", index=False)
        print(f"💾 weather_{year}.csv — {len(all_weather)} rows")

    if all_quali:
        pd.DataFrame(all_quali).to_csv(f"{DATA_DIR}/qualifying_{year}.csv", index=False)
        print(f"💾 qualifying_{year}.csv — {len(all_quali)} rows")

if __name__ == "__main__":
    fetch_season(2026)
    print(f"\n🎉 All done!")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")