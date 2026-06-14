from fastapi import APIRouter, HTTPException, Query
from backend.services.db_service import get_cached_data, filter_season, get_driver_standings
from backend.utils.helpers import get_driver_display, fig_to_json
from backend.utils.charts import (
    driver_bar_chart,
    driver_points_progression,
    driver_finish_trend,
    head_to_head_bar
)
from backend.utils.metadata import DRIVER_NAMES

router = APIRouter(tags=["drivers"])

def calculate_driver_stats(r_df, driver: str) -> dict:
    sub = r_df[r_df["driver"] == driver]
    if sub.empty:
        return {
            "points": 0,
            "wins": 0,
            "podiums": 0,
            "avg_finish": 0.0,
            "avg_grid": 0.0
        }
    return {
        "points": int(sub["total_points"].sum()),
        "wins": int((sub["finish_pos"] == 1).sum()),
        "podiums": int((sub["finish_pos"] <= 3).sum()),
        "avg_finish": round(float(sub["finish_pos"].dropna().mean()), 1) if not sub["finish_pos"].dropna().empty else 0.0,
        "avg_grid": round(float(sub["grid_pos"].dropna().mean()), 1) if not sub["grid_pos"].dropna().empty else 0.0,
    }

@router.get("/drivers")
def get_drivers_dashboard():
    try:
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        # 1. Fetch standings
        standings = get_driver_standings(r26)
        for s in standings:
            disp = get_driver_display(s["driver_code"])
            s["driver_name"] = disp["name"]
            s["country"] = disp["country"]
            s["color"] = disp["color"]
            
        # 2. Standings bar chart
        points_chart_fig = driver_bar_chart(r26, DRIVER_NAMES, title="Driver Points 2026")
        points_chart = fig_to_json(points_chart_fig)
        
        # 3. Points progression chart (Top 5)
        top5 = r26.groupby("driver")["total_points"].sum().nlargest(5).index.tolist()
        progression_chart_fig = driver_points_progression(r26, DRIVER_NAMES, top5)
        progression_chart = fig_to_json(progression_chart_fig)
        
        return {
            "standings": standings,
            "points_chart": points_chart,
            "progression_chart": progression_chart
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch drivers data: {str(e)}")

@router.get("/drivers/compare")
def compare_drivers(
    driver_a: str = Query(..., description="Driver code A"),
    driver_b: str = Query(..., description="Driver code B")
):
    try:
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        driver_a = driver_a.upper()
        driver_b = driver_b.upper()
        
        valid_drivers = r26["driver"].unique().tolist()
        if driver_a not in valid_drivers or driver_b not in valid_drivers:
            raise HTTPException(status_code=404, detail="One or both drivers not found in current season results.")
            
        # 1. Calculate summary metrics
        stats_a = calculate_driver_stats(r26, driver_a)
        stats_b = calculate_driver_stats(r26, driver_b)
        
        # 2. Charts
        progression_fig = driver_points_progression(r26, DRIVER_NAMES, [driver_a, driver_b])
        finish_trend_fig = driver_finish_trend(r26, DRIVER_NAMES, [driver_a, driver_b])
        head_to_head_fig = head_to_head_bar(stats_a, stats_b, driver_a, driver_b, DRIVER_NAMES)
        
        return {
            "driver_a": {
                "code": driver_a,
                "display": get_driver_display(driver_a),
                "stats": stats_a
            },
            "driver_b": {
                "code": driver_b,
                "display": get_driver_display(driver_b),
                "stats": stats_b
            },
            "progression_chart": fig_to_json(progression_fig),
            "finish_trend_chart": fig_to_json(finish_trend_fig),
            "head_to_head_chart": fig_to_json(head_to_head_fig)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare drivers: {str(e)}")
