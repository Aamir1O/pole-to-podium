from fastapi import APIRouter, HTTPException, Query
from backend.services.db_service import get_cached_data, filter_season, get_team_standings
from backend.utils.helpers import fig_to_json
from backend.utils.charts import (
    team_bar_chart,
    team_points_progression,
    qualifying_performance_chart,
    driver_contribution_chart,
    race_pace_chart
)
from backend.utils.metadata import DRIVER_NAMES

router = APIRouter(tags=["teams"])

@router.get("/teams")
def get_teams_dashboard():
    try:
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        # 1. Constructor standings
        standings = get_team_standings(r26)
        
        # 2. Points bar chart
        points_chart_fig = team_bar_chart(r26, title="Constructor Points 2026", horizontal=True)
        points_chart = fig_to_json(points_chart_fig)
        
        return {
            "standings": standings,
            "points_chart": points_chart
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor standings: {str(e)}")

@router.get("/teams/compare")
def compare_teams(
    team_a: str = Query(..., description="Team name A"),
    team_b: str = Query(..., description="Team name B")
):
    try:
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        valid_teams = r26["team"].unique().tolist()
        if team_a not in valid_teams or team_b not in valid_teams:
            raise HTTPException(status_code=404, detail="One or both teams not found in current season constructors.")
            
        # 1. Progression lines
        progression_fig = team_points_progression(r26, [team_a, team_b])
        
        # 2. Avg Qualifying bar
        qualifying_fig = qualifying_performance_chart(r26, [team_a, team_b])
        
        # 3. Driver contribution pie charts
        driver_contrib_a_fig = driver_contribution_chart(r26, team_a, DRIVER_NAMES)
        driver_contrib_b_fig = driver_contribution_chart(r26, team_b, DRIVER_NAMES)
        
        # 4. Race pace bar
        race_pace_fig = race_pace_chart(r26, [team_a, team_b])
        
        return {
            "team_a": team_a,
            "team_b": team_b,
            "progression_chart": fig_to_json(progression_fig),
            "qualifying_chart": fig_to_json(qualifying_fig),
            "driver_contribution_a": fig_to_json(driver_contrib_a_fig),
            "driver_contribution_b": fig_to_json(driver_contrib_b_fig),
            "race_pace_chart": fig_to_json(race_pace_fig)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare constructors: {str(e)}")
