from fastapi import APIRouter, HTTPException
from backend.services.db_service import get_cached_data, filter_season, get_driver_standings, get_team_standings, get_race_schedule
from backend.services.prediction_service import get_predictions
from backend.utils.helpers import get_next_race, get_driver_display, fig_to_json
from backend.utils.charts import championship_battle_chart
from backend.utils.metadata import DRIVER_NAMES

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard")
def get_dashboard_data():
    try:
        # 1. Load cached datasets
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        
        # 2. Filter for 2026 season
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        if r26.empty:
            return {
                "hero_stats": {
                    "races_complete": 0,
                    "championship_leader": "No Data",
                    "leader_points": 0,
                    "leader_team": "N/A",
                    "wins_count": 0
                },
                "next_race": get_next_race(),
                "driver_standings": [],
                "team_standings": [],
                "race_schedule": [],
                "championship_battle_chart": None,
                "win_probability_preview": []
            }
            
        # 3. Calculate Hero KPIs
        races_complete = int(r26["race_id"].nunique())
        
        # Group points to find championship leader
        driver_points = r26.groupby("driver")["total_points"].sum()
        leader_drv = driver_points.idxmax()
        leader_pts = int(driver_points.max())
        leader_name = DRIVER_NAMES.get(leader_drv, (leader_drv, ""))[0]
        
        leader_team_row = r26[r26["driver"] == leader_drv].sort_values("race_id")
        leader_team = leader_team_row["team"].iloc[-1] if not leader_team_row.empty else "N/A"
        
        wins_count = int((r26["finish_pos"] == 1).sum())
        
        hero_stats = {
            "races_complete": races_complete,
            "championship_leader": leader_name,
            "leader_points": leader_pts,
            "leader_team": leader_team,
            "wins_count": wins_count
        }
        
        # 4. Generate Plotly Championship Battle Chart
        fig = championship_battle_chart(r26, DRIVER_NAMES, top_n=10)
        championship_battle_json = fig_to_json(fig)
        
        # 5. Extract Standings & Schedule previews
        driver_standings = get_driver_standings(r26)
        team_standings = get_team_standings(r26)
        race_schedule = get_race_schedule(r26)
        
        # Hydrate standings preview with full driver metadata (names, flags, colors)
        for d in driver_standings:
            disp = get_driver_display(d["driver_code"])
            d["driver_name"] = disp["name"]
            d["country"] = disp["country"]
            d["color"] = disp["color"]
            
        # 6. Generate Win Probability Preview using model fallback
        next_race = get_next_race()
        latest_race_id = q26["race_id"].max() if not q26.empty else None
        
        win_prob_preview = []
        if latest_race_id:
            ri = r26[r26["race_id"] == latest_race_id]
            circuit = ri["circuit"].iloc[0] if not ri.empty else next_race.get("circuit", "Unknown")
            try:
                pred_df = get_predictions(
                    results_all, laps_all, qualifying_all, weather_all,
                    latest_race_id, circuit, practice_all
                )
                if not pred_df.empty:
                    # Select top 5 drivers
                    for _, row in pred_df.head(5).iterrows():
                        disp = get_driver_display(row["driver"])
                        win_prob_preview.append({
                            "driver_code": row["driver"],
                            "driver_name": disp["name"],
                            "team": row["team"],
                            "win_probability": float(row["win_probability"]),
                            "grid_pos": int(row["grid_pos"])
                        })
            except Exception:
                pass
                
        return {
            "hero_stats": hero_stats,
            "next_race": next_race,
            "driver_standings": driver_standings[:10],  # Preview limit 10 (fills the card height)
            "team_standings": team_standings[:5],      # Preview limit 5
            "race_schedule": race_schedule[:10],        # Preview limit 10
            "championship_battle_chart": championship_battle_json,
            "win_probability_preview": win_prob_preview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")
