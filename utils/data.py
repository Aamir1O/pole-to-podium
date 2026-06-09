import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")


@st.cache_resource
def get_engine():
    return create_engine(
        DB_URL,
        pool_size=2,
        max_overflow=0,
        connect_args={"connect_timeout": 10},
    )


@st.cache_data(ttl=300)
def load_data():
    engine = get_engine()
    with engine.connect() as conn:
        results    = pd.read_sql(text("SELECT * FROM results"),    conn)
        qualifying = pd.read_sql(text("SELECT * FROM qualifying"), conn)
        laps       = pd.read_sql(text("SELECT * FROM laps"),       conn)
        weather    = pd.read_sql(text("SELECT * FROM weather"),    conn)
    return results, qualifying, laps, weather


def get_seasons(results_all):
    """Return sorted list of all available seasons e.g. [2024, 2025, 2026]"""
    return sorted(results_all["year"].dropna().unique().astype(int).tolist())


def get_current_season(results_all):
    """Return the most recent season with data."""
    seasons = get_seasons(results_all)
    return seasons[-1] if seasons else None


def filter_season(results_all, qualifying_all, laps_all, weather_all, year: int):
    """Return (r, q, l, w) filtered to a single season with total_points column."""
    r = results_all[results_all["year"] == year].copy()
    r["total_points"] = r["points"].fillna(0) + (
        r["sprint_pts"].fillna(0) if "sprint_pts" in r.columns else 0
    )
    q = qualifying_all[qualifying_all["race_id"].str.startswith(str(year))].copy()
    l = laps_all[laps_all["race_id"].str.startswith(str(year))].copy()
    w = weather_all[weather_all["race_id"].str.startswith(str(year))].copy()
    return r, q, l, w