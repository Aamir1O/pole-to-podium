from fastapi import APIRouter, HTTPException, Query
from typing import List
from backend.services.db_service import get_cached_data, filter_season
from backend.utils.helpers import fig_to_json, get_driver_display
from backend.utils.charts import (
    lap_time_evolution,
    tyre_degradation_chart,
    tyre_usage_chart,
    position_changes_chart,
    qualifying_vs_race_scatter,
    race_pace_analysis
)
from backend.utils.metadata import DRIVER_NAMES

router = APIRouter(tags=["analytics"])

@router.get("/analytics")
def get_analytics_dashboard(
    race_id: str = Query(None, description="Race ID (e.g. 2026_R01). Defaults to latest completed race."),
    drivers: List[str] = Query(None, description="List of driver codes to filter by (e.g. VER, HAM).")
):
    try:
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        if r26.empty or l26.empty:
            return {
                "races": [],
                "selected_race_id": None,
                "drivers_in_race": [],
                "charts": {
                    "lap_time_evolution": None,
                    "tyre_degradation": None,
                    "tyre_usage": None,
                    "position_changes": None,
                    "qualifying_vs_race": None,
                    "race_pace_distribution": None
                }
            }
            
        # 1. Get list of all completed races
        races_df = (
            r26[["race_id", "race_name"]]
            .drop_duplicates()
            .sort_values("race_id", ascending=False)
        )
        races = [{"race_id": row["race_id"], "race_name": row["race_name"]} for _, row in races_df.iterrows()]
        
        # 2. Default to latest completed race
        if not race_id:
            race_id = races[0]["race_id"] if races else None
            
        if not race_id:
            raise HTTPException(status_code=404, detail="No race rounds completed yet in this season.")
            
        # 3. Find drivers participating in this specific race
        drivers_in_race_list = sorted(
            l26[l26["race_id"] == race_id]["driver"].dropna().unique().tolist()
        )
        drivers_in_race = [
            {**get_driver_display(d), "code": d}
            for d in drivers_in_race_list
        ]
        
        # 4. Apply driver filters (default to first 8 drivers if empty)
        if not drivers:
            drivers = drivers_in_race_list[:8]
        else:
            # Clean uppercase
            drivers = [d.upper() for d in drivers]
            
        # 5. Build Plotly Figures
        fig_lap_evo = lap_time_evolution(l26, race_id, drivers, DRIVER_NAMES)
        fig_tyre_deg = tyre_degradation_chart(l26, race_id, drivers)
        fig_tyre_use = tyre_usage_chart(l26, race_id, drivers)
        fig_pos_change = position_changes_chart(r26, race_id)
        fig_quali_race = qualifying_vs_race_scatter(r26, race_id)
        fig_pace_dist = race_pace_analysis(l26, race_id, drivers, DRIVER_NAMES)
        
        return {
            "races": races,
            "selected_race_id": race_id,
            "drivers_in_race": drivers_in_race,
            "selected_drivers": drivers,
            "charts": {
                "lap_time_evolution": fig_to_json(fig_lap_evo),
                "tyre_degradation": fig_to_json(fig_tyre_deg),
                "tyre_usage": fig_to_json(fig_tyre_use),
                "position_changes": fig_to_json(fig_pos_change),
                "qualifying_vs_race": fig_to_json(fig_quali_race),
                "race_pace_distribution": fig_to_json(fig_pace_dist)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")
