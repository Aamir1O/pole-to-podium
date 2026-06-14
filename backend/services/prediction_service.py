import os
import pickle
import pandas as pd
from utils.predictions import build_predictions

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "model")

_model = None
_encoders = None

def get_model_and_encoders():
    """Loads XGBoost model and encoders into memory (singleton pattern)."""
    global _model, _encoders
    if _model is None or _encoders is None:
        with open(f"{MODEL_DIR}/model.pkl", "rb") as f:
            _model = pickle.load(f)
        with open(f"{MODEL_DIR}/encoders.pkl", "rb") as f:
            _encoders = pickle.load(f)
    return _model, _encoders

def get_predictions(results_all, laps_all, qualifying_all, weather_all, race_id, circuit_name, practice_all=None):
    """Executes the win predictions model pipeline for a specific race_id."""
    model, enc = get_model_and_encoders()
    le_driver = enc["driver"]
    le_team = enc["team"]
    le_circuit = enc["circuit"]
    features = enc["features"]
    
    pred_df = build_predictions(
        results_all, laps_all, qualifying_all, weather_all,
        race_id, circuit_name,
        le_driver=le_driver, le_team=le_team, le_circuit=le_circuit,
        features=features, model=model, practice_df=practice_all
    )
    return pred_df
