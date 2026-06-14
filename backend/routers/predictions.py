from fastapi import APIRouter, HTTPException, Query
from backend.services.db_service import get_cached_data, filter_season
from backend.services.prediction_service import get_predictions
from backend.utils.helpers import get_driver_display, fig_to_json, get_next_race
from backend.utils.charts import win_prob_chart
from backend.utils.metadata import DRIVER_NAMES

router = APIRouter(tags=["predictions"])

@router.get("/predictions")
def get_race_predictions(race_id: str = Query(None, description="Race ID (e.g., 2026_R06). Defaults to latest qualifying round.")):
    try:
        results_all, qualifying_all, laps_all, weather_all, practice_all = get_cached_data()
        r26, q26, l26, w26, p26 = filter_season(results_all, qualifying_all, laps_all, weather_all, 2026, practice_all)
        
        # 1. Determine which race to predict
        if not race_id:
            # Try to get latest from qualifying
            latest_quali_race = q26["race_id"].max() if not q26.empty else None
            # Fallback to latest practice if no qualifying is loaded
            latest_practice_race = p26["race_id"].max() if not p26.empty else None
            race_id = latest_quali_race or latest_practice_race
            
        if not race_id:
            return {
                "race_id": None,
                "circuit": None,
                "data_source": None,
                "predictions": [],
                "win_prob_chart": None,
                "insights": {}
            }
            
        # 2. Get circuit name
        next_race = get_next_race()
        ri = r26[r26["race_id"] == race_id]
        circuit = ri["circuit"].iloc[0] if not ri.empty else next_race.get("circuit", "Unknown")
        
        # 3. Get predictions DataFrame
        pred_df = get_predictions(
            results_all, laps_all, qualifying_all, weather_all,
            race_id, circuit, practice_all
        )
        
        if pred_df.empty:
            return {
                "race_id": race_id,
                "circuit": circuit,
                "data_source": None,
                "predictions": [],
                "win_prob_chart": None,
                "insights": {}
            }
            
        # 4. Generate win probability Plotly figure
        fig = win_prob_chart(pred_df, DRIVER_NAMES, title=f"Win Probability — {race_id}")
        chart_json = fig_to_json(fig)
        
        # 5. Hydrate records
        predictions = []
        data_source = pred_df["data_source"].iloc[0] if "data_source" in pred_df.columns else "Unknown"
        
        for idx, row in pred_df.iterrows():
            disp = get_driver_display(row["driver"])
            predictions.append({
                "position": idx + 1,
                "driver_code": row["driver"],
                "driver_name": disp["name"],
                "country": disp["country"],
                "color": disp["color"],
                "team": row["team"],
                "grid_pos": int(row["grid_pos"]),
                "win_probability": float(row["win_probability"])
            })
            
        insights = {
            "model_type": "XGBoost Classifier",
            "features_used": "Grid position, Q3/Practice time, Historical win rate, Track temperature, Humidity, Rain factor",
            "training_source": "Formula 1 Historical Race Results"
        }
        
        return {
            "race_id": race_id,
            "circuit": circuit,
            "data_source": data_source,
            "predictions": predictions,
            "win_prob_chart": chart_json,
            "insights": insights
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate predictions: {str(e)}")
